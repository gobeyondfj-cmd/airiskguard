"""Tests for SecretsChecker."""

from __future__ import annotations

import pytest
from airiskguard.checkers.secrets import SecretsChecker
from airiskguard.types import RiskLevel


@pytest.fixture
def checker():
    return SecretsChecker()


# --- AI provider keys ---

async def test_anthropic_key(checker):
    result = await checker.check("My key is sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456", "", {})
    assert not result.passed
    assert "anthropic_api_key" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_openai_key(checker):
    result = await checker.check("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890abcd", "", {})
    assert not result.passed
    assert "openai_api_key" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_huggingface_token(checker):
    result = await checker.check("token = hf_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij", "", {})
    assert not result.passed
    assert "huggingface_token" in result.details["flags"]


# --- Cloud credentials ---

async def test_aws_access_key(checker):
    result = await checker.check("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE", "", {})
    assert not result.passed
    assert "aws_access_key" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_gcp_service_account(checker):
    result = await checker.check(
        '{"type": "service_account", "project_id": "my-project"}', "", {}
    )
    assert not result.passed
    assert "gcp_service_account" in result.details["flags"]


async def test_azure_connection_string(checker):
    text = (
        "DefaultEndpointsProtocol=https;AccountName=myaccount;"
        "AccountKey=" + "A" * 64 + ";EndpointSuffix=core.windows.net"
    )
    result = await checker.check(text, "", {})
    assert not result.passed
    assert "azure_connection_string" in result.details["flags"]


# --- Source control tokens ---

async def test_github_token(checker):
    result = await checker.check(
        "GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234", "", {}
    )
    assert not result.passed
    assert "github_token" in result.details["flags"]


async def test_gitlab_token(checker):
    result = await checker.check("token: glpat-abcdefghijklmnopqrst", "", {})
    assert not result.passed
    assert "gitlab_token" in result.details["flags"]


# --- Private keys ---

async def test_rsa_private_key(checker):
    result = await checker.check(
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
        "", {}
    )
    assert not result.passed
    assert "private_key_pem" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_openssh_private_key(checker):
    result = await checker.check("-----BEGIN OPENSSH PRIVATE KEY-----", "", {})
    assert not result.passed
    assert "private_key_pem" in result.details["flags"]


# --- Database connection strings ---

async def test_postgres_connection_string(checker):
    result = await checker.check(
        "DATABASE_URL=postgresql://admin:supersecret123@prod-db.example.com:5432/mydb",
        "", {}
    )
    assert not result.passed
    assert "db_connection_string" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_mongodb_connection_string(checker):
    result = await checker.check(
        "MONGO_URI=mongodb://user:pass123@cluster0.mongodb.net/mydb",
        "", {}
    )
    assert not result.passed
    assert "db_connection_string" in result.details["flags"]


# --- JWT tokens ---

async def test_jwt_token(checker):
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    result = await checker.check(f"Authorization: Bearer {jwt}", "", {})
    assert not result.passed
    assert "jwt_token" in result.details["flags"]


# --- Stripe keys ---

async def test_stripe_secret_key(checker):
    result = await checker.check("stripe_key = sk_live_FAKE_TEST_KEY_xxxx", "", {})
    assert not result.passed
    assert "stripe_secret_key" in result.details["flags"]


# --- Hardcoded password ---

async def test_hardcoded_password(checker):
    result = await checker.check('password = "MyS3cr3tP@ss"', "", {})
    assert not result.passed
    assert "hardcoded_password" in result.details["flags"]


async def test_hardcoded_api_key(checker):
    result = await checker.check('api_key = "prod-secret-key-12345"', "", {})
    assert not result.passed
    assert "hardcoded_password" in result.details["flags"]


# --- Redaction ---

async def test_redaction_enabled(checker):
    result = await checker.check("AKIAIOSFODNN7EXAMPLE", "", {})
    assert not result.passed
    assert "redacted_text" in result.details
    assert "REDACTED" in result.details["redacted_text"]


async def test_redaction_disabled():
    checker = SecretsChecker(redact=False)
    result = await checker.check("AKIAIOSFODNN7EXAMPLE", "", {})
    assert not result.passed
    assert "redacted_text" not in result.details


# --- Clean inputs ---

async def test_clean_prompt(checker):
    result = await checker.check(
        "Please refactor this function to use list comprehension instead of a for loop.",
        "", {}
    )
    assert result.passed
    assert result.risk_level == RiskLevel.LOW
    assert result.score == 0.0


async def test_clean_code(checker):
    code = """
def calculate_total(items):
    return sum(item.price for item in items)
"""
    result = await checker.check(code, "", {})
    assert result.passed


# --- Output data also scanned ---

async def test_secret_in_output(checker):
    result = await checker.check(
        "What is the config?",
        "The API key is sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456",
        {},
    )
    assert not result.passed


# --- Multiple secrets ---

async def test_multiple_secrets(checker):
    text = (
        "AKIAIOSFODNN7EXAMPLE\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456"
    )
    result = await checker.check(text, "", {})
    assert not result.passed
    assert result.details["secret_count"] >= 2
