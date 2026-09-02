"""Regression tests for the Pine Ridge Reservation-only design boundary."""

from pathlib import Path
import ast

import nbformat
import yaml

from src.constants import PINE_RIDGE_BBOX, PRIMARY_NATIONS_CENSUS, STUDY_BBOX


ROOT = Path(__file__).resolve().parents[1]


def test_config_has_one_study_extent():
    config = yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))
    assert list(config["bounding_box"]) == ["pine_ridge"]
    assert STUDY_BBOX == PINE_RIDGE_BBOX
    assert PRIMARY_NATIONS_CENSUS == ["Pine Ridge"]


def test_repository_has_no_out_of_scope_reservation_names():
    prohibited = ("rose" + "bud", "sican" + "gu", "oce" + "ti")
    roots = [ROOT / "README.md", ROOT / "config", ROOT / "docs", ROOT / "src", ROOT / "scripts", ROOT / "Notebooks"]
    checked_suffixes = {".md", ".py", ".yaml", ".yml", ".ipynb", ".cff"}
    findings = []
    for root in roots:
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in checked_suffixes:
                continue
            text = path.read_text(encoding="utf-8").lower()
            if any(name in text for name in prohibited):
                findings.append(str(path.relative_to(ROOT)))
    assert not findings, f"Out-of-scope place or collective names found in: {findings}"


def test_notebook_code_cells_parse_after_scope_edits():
    for path in (ROOT / "Notebooks").glob("*.ipynb"):
        notebook = nbformat.read(path, as_version=4)
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            source = "\n".join(
                line for line in cell.source.splitlines() if not line.lstrip().startswith("%")
            )
            try:
                ast.parse(source)
            except SyntaxError as error:
                raise AssertionError(f"Invalid Python in {path.name}, cell {index}: {error}") from error
