"""Unit tests for SSRF URL validation."""

from app.core.security import is_safe_repository_url


def test_safe_public_github_url():
    is_safe, reason = is_safe_repository_url("https://github.com/fastapi/fastapi.git")
    assert is_safe is True
    assert "safe" in reason.lower() or "valid" in reason.lower()


def test_reject_localhost():
    is_safe, reason = is_safe_repository_url("http://localhost:8000/repo.git")
    assert is_safe is False
    assert "localhost" in reason.lower() or "loopback" in reason.lower()


def test_reject_loopback_ip():
    is_safe, reason = is_safe_repository_url("http://127.0.0.1:8080/my-repo")
    assert is_safe is False


def test_reject_invalid_scheme():
    is_safe, reason = is_safe_repository_url("ftp://github.com/user/repo")
    assert is_safe is False
    assert "scheme" in reason.lower() or "https://" in reason.lower()


def test_reject_empty_url():
    is_safe, reason = is_safe_repository_url("")
    assert is_safe is False
