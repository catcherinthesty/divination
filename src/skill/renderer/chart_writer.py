"""Deterministic file writer with atomic writes.

Prevents partial outputs by writing to a temp file then renaming.
Verifies file size > 0 after write (FR-010: deterministic artifacts).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write(path: str | Path, content: str) -> None:
    """Write content to a file atomically.

    Writes to a temp file in the same directory, then renames to the
    target path. This prevents partial files if the process is interrupted.

    Args:
        path: Target file path.
        content: String content to write (UTF-8).

    Raises:
        IOError: If the file cannot be written or is empty after write.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)

        # Verify non-empty
        if os.path.getsize(tmp_path) == 0:
            raise IOError(f"Atomic write produced empty file: {path}")

        # Atomic rename
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def verify_output(path: str | Path) -> bool:
    """Verify an output file exists and is non-empty."""
    path = Path(path)
    return path.exists() and path.stat().st_size > 0
