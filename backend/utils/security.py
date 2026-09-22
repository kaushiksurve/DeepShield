import re
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings

def sanitize_filename(filename: str) -> str:
    """Remove path components and dangerous characters."""
    name = Path(filename).name
    name = re.sub(r'[^\w\s\-.]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:128]

def validate_video_file(file: UploadFile, content: bytes) -> None:
    """Validate file extension and size. Raises HTTPException on failure."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"File type '{ext}' not supported. Allowed: {settings.allowed_extensions}")

    # Skip strict MIME check — browsers/proxies send inconsistent content-types
    # Trust the file extension instead.

    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(413, f"File too large ({size_mb:.1f} MB). Maximum is {settings.max_upload_mb} MB")

def cleanup_file(path: str) -> None:
    """Safely delete a file."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
