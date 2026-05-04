"""Tests for VulnChecker."""

from __future__ import annotations

import pytest
from airiskguard.checkers.vuln import VulnChecker
from airiskguard.types import RiskLevel


@pytest.fixture
def checker():
    return VulnChecker()


# --- SQL injection ---

async def test_sql_injection_format_string(checker):
    code = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "sql_injection" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_sql_injection_fstring(checker):
    code = 'cursor.execute(f"SELECT * FROM users WHERE name = {name}")'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "sql_injection" in result.details["flags"]


async def test_sql_injection_concatenation(checker):
    code = '"SELECT * FROM orders WHERE id = " + user_input'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "sql_injection" in result.details["flags"]


# --- Command injection ---

async def test_shell_true(checker):
    code = "subprocess.run(cmd, shell=True)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "command_injection" in result.details["flags"]
    assert result.risk_level == RiskLevel.CRITICAL


async def test_os_system(checker):
    code = "os.system('ls -la')"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "command_injection" in result.details["flags"]


async def test_eval_user_input(checker):
    code = "result = eval(request.args.get('expr'))"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "command_injection" in result.details["flags"]


# --- Insecure deserialization ---

async def test_pickle_loads(checker):
    code = "data = pickle.loads(user_data)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_deserialization" in result.details["flags"]


async def test_yaml_load_unsafe(checker):
    code = "config = yaml.load(file_content)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_deserialization" in result.details["flags"]


# --- Weak cryptography ---

async def test_md5_hash(checker):
    code = "digest = hashlib.md5(password.encode()).hexdigest()"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "weak_cryptography" in result.details["flags"]


async def test_sha1_hash(checker):
    code = "digest = hashlib.sha1(data).hexdigest()"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "weak_cryptography" in result.details["flags"]


# --- Insecure random ---

async def test_random_module(checker):
    code = "token = random.randint(0, 999999)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_random" in result.details["flags"]


# --- Hardcoded credentials ---

async def test_hardcoded_password_in_code(checker):
    code = 'password = "supersecret123"'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "hardcoded_credentials" in result.details["flags"]


async def test_hardcoded_api_key(checker):
    code = 'api_key = "prod-key-abc123def456"'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "hardcoded_credentials" in result.details["flags"]


# --- Path traversal ---

async def test_open_with_user_input(checker):
    code = "with open(request.args['filename']) as f:"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "path_traversal" in result.details["flags"]


# --- Debug in production ---

async def test_debug_true(checker):
    code = "app.run(host='0.0.0.0', port=5000, debug=True)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "debug_in_production" in result.details["flags"]


# --- Insecure HTTP ---

async def test_http_not_https(checker):
    code = 'response = requests.get("http://api.internal-service.company.com/data")'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_http" in result.details["flags"]


async def test_ssl_verify_false(checker):
    code = "requests.get(url, verify=False)"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_http" in result.details["flags"]


# --- Insecure CORS ---

async def test_cors_wildcard(checker):
    code = 'response.headers["Access-Control-Allow-Origin"] = "*"'
    result = await checker.check("", code, {})
    assert not result.passed
    assert "insecure_cors" in result.details["flags"]


# --- Category filter ---

async def test_category_filter():
    checker = VulnChecker(categories=["sql_injection"])
    code = "os.system('rm -rf /') + cursor.execute('SELECT * FROM users WHERE id = %s' % uid)"
    result = await checker.check("", code, {})
    assert "sql_injection" in result.details["flags"]
    assert "command_injection" not in result.details["flags"]


# --- Clean code ---

async def test_clean_code(checker):
    code = """
import secrets
import hashlib

def create_token():
    return secrets.token_hex(32)

def hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
"""
    result = await checker.check("", code, {})
    assert result.passed
    assert result.risk_level == RiskLevel.LOW


async def test_clean_sql_with_params(checker):
    code = 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'
    result = await checker.check("", code, {})
    assert result.passed


# --- Matched lines in details ---

async def test_matched_lines_reported(checker):
    code = "os.system('whoami')"
    result = await checker.check("", code, {})
    assert not result.passed
    assert "command_injection" in result.details["matched_lines"]
    assert len(result.details["matched_lines"]["command_injection"]) > 0


# --- Multiple vulnerabilities ---

async def test_multiple_vulns(checker):
    code = """
password = "admin123"
cursor.execute("SELECT * FROM users WHERE name = '%s'" % name)
subprocess.run(cmd, shell=True)
"""
    result = await checker.check("", code, {})
    assert not result.passed
    assert result.details["vuln_count"] >= 2
    assert result.risk_level == RiskLevel.CRITICAL
