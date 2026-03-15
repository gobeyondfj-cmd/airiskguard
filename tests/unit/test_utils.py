"""Tests for utility modules."""

import json

from airiskguard.utils.hashing import hash_chain, hash_object, sha256_hash
from airiskguard.utils.serialization import canonical_json
from airiskguard.utils.time_utils import utc_now, utc_now_iso
from airiskguard.utils.validators import validate_model_id, validate_non_empty, validate_score

import pytest
from airiskguard.exceptions import ConfigError


def test_sha256_hash():
    h = sha256_hash("hello")
    assert len(h) == 64
    assert h == sha256_hash("hello")  # deterministic


def test_hash_object():
    h1 = hash_object({"a": 1, "b": 2})
    h2 = hash_object({"b": 2, "a": 1})
    assert h1 == h2  # canonical ordering


def test_hash_chain():
    h = hash_chain("data", "prev")
    assert len(h) == 64
    assert h != hash_chain("data", "other_prev")


def test_canonical_json():
    result = canonical_json({"b": 2, "a": 1})
    assert json.loads(result) == {"a": 1, "b": 2}


def test_utc_now():
    dt = utc_now()
    assert dt.tzinfo is not None


def test_utc_now_iso():
    iso = utc_now_iso()
    assert "T" in iso


def test_validate_score():
    assert validate_score(0.5) == 0.5
    with pytest.raises(ValueError):
        validate_score(1.5)
    with pytest.raises(ValueError):
        validate_score(-0.1)


def test_validate_non_empty():
    assert validate_non_empty("hello", "test") == "hello"
    with pytest.raises(ConfigError):
        validate_non_empty("", "test")
    with pytest.raises(ConfigError):
        validate_non_empty("   ", "test")


def test_validate_model_id():
    assert validate_model_id("model-1") == "model-1"
    with pytest.raises(ConfigError):
        validate_model_id("")
