import pytest
from fastapi import HTTPException
from app.security import sanitize_filename, validate_pdf_file, SimpleRateLimiter


def test_sanitize_filename_traversal():
    # Verify path traversal attempts are stripped
    assert sanitize_filename("../../../secret.pdf") == "secret.pdf"
    assert sanitize_filename("..\\..\\passwords.txt") == "passwords.txt.pdf"
    assert sanitize_filename("file name with spaces.pdf") == "file_name_with_spaces.pdf"
    assert sanitize_filename("") == "document.pdf"


def test_validate_pdf_file_valid():
    # Valid PDF bytes starting with %PDF- header
    valid_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj"
    validate_pdf_file(valid_content, "test.pdf", max_size_mb=10)


def test_validate_pdf_file_rejects_non_pdf():
    # Rejects content missing the magic bytes
    invalid_content = b"This is just a text file masquerading as a PDF"
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_file(invalid_content, "fake.pdf", max_size_mb=10)
    assert exc_info.value.status_code == 415
    assert "not a valid PDF document" in exc_info.value.detail


def test_validate_pdf_file_rejects_oversized():
    # Rejects file exceeding size limit (e.g. 1 MB limit test)
    oversized_content = b"%PDF-" + b"0" * (2 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_file(oversized_content, "large.pdf", max_size_mb=1)
    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed size" in exc_info.value.detail


def test_rate_limiter():
    limiter = SimpleRateLimiter(requests_per_minute=2)
    limiter.check("127.0.0.1")
    limiter.check("127.0.0.1")
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("127.0.0.1")
    assert exc_info.value.status_code == 429
