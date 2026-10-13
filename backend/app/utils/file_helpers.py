"""
QueryForge - File Helpers
File type detection, name sanitization, and size validation.
"""
import os
import mimetypes
from pathlib import Path
from app.core.config import settings

ALLOWED_EXTENSIONS = {".csv", ".sql", ".sqlite", ".db"}


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    import re
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()
    safe = re.sub(r'[^\w\-_. ]', '_', stem)
    return f"{safe}{ext}"


def check_file_size(file_path: str) -> bool:
    """Returns True if file is within the allowed size limit."""
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return size_mb <= settings.MAX_UPLOAD_SIZE_MB


def get_file_type(filename: str) -> str:
    ext = get_file_extension(filename)
    type_map = {
        ".csv": "csv",
        ".sql": "sql",
        ".sqlite": "sqlite",
        ".db": "sqlite",
    }
    return type_map.get(ext, "unknown")
