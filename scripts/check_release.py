"""Read-only release and input verification for a clean OLC checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from src.constants import GOVERNED_DIR, REPO_ROOT, WSD_3D_MODEL
from src.loaders import discover_ssurgo_geodatabases


SENSITIVE_NAMES = {
    "soil_profiles.csv", "soil_profiles.xlsx", "well_logs.csv", "well_logs.xlsx",
    "field_observations.csv", "field_observations.xlsx",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tracked_files() -> set[str]:
    run = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True, capture_output=True,
    )
    return {item.decode("utf-8") for item in run.stdout.split(b"\0") if item}


def verify() -> dict:
    tracked = tracked_files()
    governed_prefix = GOVERNED_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    sensitive_tracked = sorted(
        path for path in tracked
        if (path.startswith(governed_prefix) and not path.endswith("/.gitkeep"))
        or Path(path).name.lower() in SENSITIVE_NAMES
    )
    model_path = Path(WSD_3D_MODEL["gdb_path"])
    geology_files = [
        REPO_ROOT/"data/raw/geology/SD_geol_poly.shp",
        REPO_ROOT/"data/raw/geology/SD_units.csv",
    ]
    return {
        "release_status": "blocked" if sensitive_tracked else "technical-controls-pass",
        "governance_text_review": "pending OST/OLC review",
        "sensitive_tracked_files": sensitive_tracked,
        "inputs": {
            "wsd_3d_model": model_path.exists(),
            "state_geology": all(path.exists() for path in geology_files),
            "ssurgo_geodatabases": len(discover_ssurgo_geodatabases()),
        },
        "notes": [
            "Input presence is not scientific validation.",
            "Run from a Git checkout; this command does not inspect governed file contents.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    report = verify()
    print(json.dumps(report, indent=2) if args.json else "\n".join([
        f"Release controls: {report['release_status']}",
        f"Governance review: {report['governance_text_review']}",
        f"Sensitive tracked files: {len(report['sensitive_tracked_files'])}",
        f"Inputs: {report['inputs']}",
    ]))
    raise SystemExit(1 if report["sensitive_tracked_files"] else 0)


if __name__ == "__main__":
    main()
