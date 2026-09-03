from __future__ import annotations

"""Normalize notebook cell IDs and remove machine-specific execution state."""

from pathlib import Path
import nbformat
from nbformat.validator import normalize

ROOT = Path(__file__).resolve().parents[1]


def prepare(path: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    _, notebook = normalize(notebook)
    nbformat.validate(notebook)
    nbformat.write(notebook, path)


def main() -> None:
    for path in sorted((ROOT / "Notebooks").glob("*.ipynb")):
        prepare(path)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
