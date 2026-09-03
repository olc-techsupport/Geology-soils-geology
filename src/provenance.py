from __future__ import annotations

"""Machine-readable provenance sidecars for generated artifacts."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.constants import REPO_ROOT


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def write_sidecar(artifact: Path, *, sources: list[dict[str, Any]],
                  parameters: dict[str, Any], evidence_class: str,
                  review_status: str = "not-approved-for-publication") -> Path:
    artifact = Path(artifact)
    sidecar = artifact.with_suffix(artifact.suffix + ".provenance.json")
    payload = {
        "schema_version": 1,
        "artifact": artifact.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "processing_commit": git_commit(),
        "sources": sources,
        "parameters": parameters,
        "evidence_class": evidence_class,
        "review_status": review_status,
        "governance_text_review": "pending OST/OLC review",
    }
    sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return sidecar
