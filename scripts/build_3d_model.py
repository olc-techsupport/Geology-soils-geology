"""Build the full interactive 3D model and a real Pine Ridge cross-section."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shapely.geometry import LineString
from src.constants import OUTPUTS_DIR, ensure_project_directories
from src.geology3d import build_interactive_model, sample_cross_section
from src.loaders import load_tribal_boundaries, load_wsd_fault_points


def main() -> None:
    ensure_project_directories()
    boundaries = load_tribal_boundaries(["Pine Ridge", "Rosebud"])
    faults = load_wsd_fault_points()
    output = OUTPUTS_DIR/"04_full_3d_geology_model.html"
    build_interactive_model(output, faults=faults, boundaries=boundaries)
    transect = LineString([(-103.45, 43.15), (-101.55, 43.15)])
    sample_cross_section(transect).to_csv(
        OUTPUTS_DIR/"04_pine_ridge_cross_section.csv", index=False
    )
    print(output)


if __name__ == "__main__":
    main()
