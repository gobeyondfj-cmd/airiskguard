"""Security checker — prompt injection, jailbreak, encoding attacks."""

from __future__ import annotations

import base64
import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# Injection patterns (~30)
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"ignore (?:all )?previous instructions",
        r"ignore (?:all )?prior instructions",
        r"disregard (?:all )?(?:previous|prior|above) (?:instructions|prompts|rules)",
        r"forget (?:all )?(?:previous|prior|your) (?:instructions|rules|guidelines)",
        r"override (?:your |all )?(?:instructions|rules|guidelines|programming)",
        r"you are now (?:a |an )?(?:different|new|unrestricted)",
        r"new (?:instruction|directive|command|role):",
        r"system prompt:",
        r"<\|(?:system|im_start)\|>",
        r"\[INST\]",
        r"\[SYSTEM\]",
        r"###\s*(?:instruction|system|human|assistant)",
        r"(?:act|behave|respond) as (?:if |though )?(?:you are|you're)",
        r"pretend (?:you are|you're|to be)",
        r"role\s*play\s*as",
        r"switch (?:to |into )?(?:a |an )?(?:different|new|unrestricted) mode",
        r"enter (?:a |an )?(?:developer|debug|admin|unrestricted|god) mode",
        r"(?:developer|debug|admin|sudo|root) (?:mode|access|override)",
        r"bypass (?:your |all )?(?:filters|restrictions|safety|guidelines|rules)",
        r"ignore (?:your |all )?(?:safety|content|ethical) (?:guidelines|filters|rules)",
        r"reveal (?:your |the )?(?:system|original|initial) (?:prompt|instructions)",
        r"show (?:me )?your (?:system|original|initial) (?:prompt|instructions)",
        r"what (?:are|were) your (?:original|system|initial) (?:instructions|prompt)",
        r"output (?:your |the )?(?:system|original) (?:prompt|instructions)",
        r"repeat (?:your |the )?(?:system|original) (?:prompt|instructions)",
        r"(?:do|execute|run) (?:the )?(?:opposite|reverse) of",
        r"(?:you must|you should|you will) (?:always )?(?:obey|follow|comply)",
        r"(?:from now on|henceforth|going forward),?\s*(?:you |your )",
        r"translate (?:the )?(?:above|previous|following) (?:to|into) (?:code|python|bash)",
        r"encode (?:the )?(?:above|previous|following) (?:as|in|to) base64",
    ]
]

# Jailbreak patterns (~20)
_JAILBREAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"DAN\s*(?:mode|prompt|jailbreak)",
        r"(?:do anything now|DAN)",
        r"(?:evil|chaos|villain|dark|shadow) (?:mode|gpt|assistant|bot)",
        r"opposite (?:mode|day|world)",
        r"(?:jail|prison)\s*break",
        r"(?:uncensored|unfiltered|unrestricted|unlimited) (?:mode|version|access|ai)",
        r"(?:no|without|remove|disable) (?:restrictions|filters|censorship|limits|safety)",
        r"(?:maximum|max)\s*(?:mode|power|override)",
        r"(?:alpha|omega|god|master|root)\s*(?:mode|protocol|override)",
        r"hypothetical(?:ly)?\s*(?:speaking|scenario)",
        r"for (?:educational|research|academic|fictional) purposes",
        r"(?:creative |fiction |story )?writing (?:exercise|prompt|scenario)",
        r"(?:ethical|moral) (?:dilemma|thought experiment)",
        r"(?:as a |in a )?(?:thought|mental) experiment",
        r"(?:two|dual|split) (?:personality|persona|character) (?:mode|roleplay)",
        r"(?:good|helpful) (?:assistant|ai) vs (?:evil|bad|helpful) (?:assistant|ai)",
        r"(?:token|character) (?:by |at a )?(?:time|limit) (?:trick|bypass)",
        r"(?:base64|rot13|hex|binary) (?:encode|decode|output|respond)",
        r"respond (?:only )?(?:in|with|using) (?:code|base64|hex|binary|rot13)",
        r"(?:step.by.step|detailed) (?:instructions?|guide|tutorial) (?:for|on|to)",
    ]
]


class SecurityChecker(BaseChecker):
    name = "security"

    def __init__(self, check_encoding: bool = True) -> None:
        self._check_encoding = check_encoding

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        text = str(input_data) if input_data else ""
        flags: list[str] = []
        score = 0.0

        # Injection detection
        inj_flags, inj_score = _check_injection(text)
        flags.extend(inj_flags)
        score = max(score, inj_score)

        # Jailbreak detection
        jb_flags, jb_score = _check_jailbreak(text)
        flags.extend(jb_flags)
        score = max(score, jb_score)

        # Encoding attack detection
        if self._check_encoding:
            enc_flags, enc_score = _check_encoding_attacks(text)
            flags.extend(enc_flags)
            score = max(score, enc_score)

        # Check output too for leaked system info
        if output_data:
            out_text = str(output_data)
            leak_flags, leak_score = _check_info_leak(out_text)
            flags.extend(leak_flags)
            score = max(score, leak_score)

        risk = _score_to_risk(score)
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=risk <= RiskLevel.MEDIUM,
            score=score,
            details={"flags": flags},
        )


def _check_injection(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append(f"injection: {pattern.pattern[:60]}")
            score = max(score, 0.85)
    return flags, score


def _check_jailbreak(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0
    for pattern in _JAILBREAK_PATTERNS:
        if pattern.search(text):
            flags.append(f"jailbreak: {pattern.pattern[:60]}")
            score = max(score, 0.8)
    return flags, score


def _check_encoding_attacks(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    # Base64 encoded content that might hide instructions
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
    b64_matches = b64_pattern.findall(text)
    for match in b64_matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            if any(p.search(decoded) for p in _INJECTION_PATTERNS[:5]):
                flags.append("encoded_injection_base64")
                score = max(score, 0.9)
                break
        except Exception:
            pass

    # Unicode tricks
    if any(ord(c) > 0xFFFF for c in text):
        flags.append("unusual_unicode_characters")
        score = max(score, 0.3)

    # Homoglyph detection (simple)
    homoglyphs = {'\u0410': 'A', '\u0412': 'B', '\u0421': 'C', '\u0415': 'E'}
    if any(c in text for c in homoglyphs):
        flags.append("potential_homoglyph_attack")
        score = max(score, 0.6)

    return flags, score


def _check_info_leak(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0
    leak_patterns = [
        re.compile(r'system\s*prompt\s*[:=]', re.IGNORECASE),
        re.compile(r'(?:my|the)\s*(?:original|initial|system)\s*instructions?\s*(?:are|were|is)', re.IGNORECASE),
    ]
    for pattern in leak_patterns:
        if pattern.search(text):
            flags.append("potential_system_info_leak")
            score = max(score, 0.7)
    return flags, score


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
