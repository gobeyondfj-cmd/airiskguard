"""SHA-256 hashing utilities and hash chain support."""

from __future__ import annotations

import hashlib

from airiskguard.utils.serialization import canonical_json


def sha256_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_object(obj: object) -> str:
    return sha256_hash(canonical_json(obj))


def hash_chain(current_data: str, previous_hash: str) -> str:
    combined = f"{previous_hash}:{current_data}"
    return sha256_hash(combined)
