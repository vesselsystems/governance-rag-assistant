"""Shared, honest metadata for offline evaluation reports."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .corpus import sha256_file


def _git_value(root: Path, *arguments: str) -> str | None:
    """Read a non-secret git value when the repository metadata is available."""
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def build_run_metadata(
    root: Path,
    *,
    manifest_path: Path | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return reproducibility metadata without manufacturing unavailable values.

    The timestamp describes report generation, not source retrieval.  A manifest
    digest is computed from the checked-in manifest bytes; no URL in the manifest
    is contacted.  ``None`` is retained when git metadata is unavailable.
    """
    root = Path(root).resolve()
    manifest = (
        Path(manifest_path)
        if manifest_path is not None
        else root / "data" / "corpus_manifest.json"
    )
    manifest = manifest.resolve()
    manifest_digest = sha256_file(manifest) if manifest.is_file() else None
    revision = _git_value(root, "rev-parse", "HEAD")
    status = _git_value(root, "status", "--porcelain")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "generated_at_utc": timestamp,
        "timestamp_utc": timestamp,
        "corpus_manifest_sha256": manifest_digest,
        "corpus_manifest_hash": manifest_digest,
        "corpus_manifest_path": (
            manifest.relative_to(root).as_posix()
            if manifest.is_relative_to(root)
            else str(manifest)
        ),
        "code_revision": revision,
        "working_tree_dirty": None if status is None else bool(status),
        "config": config or {},
    }
