import os
import re
import time
from pathlib import Path
from typing import Dict, List
from fastapi import HTTPException, status


def sanitize_filename(filename: str) -> str:
    # Strip any directory path components to prevent path traversal attacks
    base_name = Path(filename).name
    # Keep only alphanumeric, dashes, underscores, and dots
    clean_name = re.sub(r"[^\w\s.-]", "", base_name).strip()
    clean_name = re.sub(r"[\s]+", "_", clean_name)
    if not clean_name:
        clean_name = "document.pdf"
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
    return clean_name


def validate_pdf_file(content: bytes, filename: str, max_size_mb: int = 10) -> None:
    # Enforce maximum file size limit
    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{filename}' exceeds maximum allowed size of {max_size_mb} MB."
        )

    # Validate file type using magic bytes (%PDF-), not just file extension
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File '{filename}' is not a valid PDF document (missing %PDF- header)."
        )


class SimpleRateLimiter:
    # Basic in-memory sliding window rate limiter per client IP
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}

    def check(self, client_ip: str) -> None:
        now = time.time()
        window_start = now - 60.0
        # Clean expired timestamps
        history = [ts for ts in self.requests.get(client_ip, []) if ts > window_start]
        if len(history) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before sending more requests."
            )
        history.append(now)
        self.requests[client_ip] = history


rate_limiter = SimpleRateLimiter(requests_per_minute=60)
