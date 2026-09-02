"""Build the full interactive 3D model and a real Pine Ridge cross-section."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shapely.geometry import LineString
from src.constants import OUTPUTS_DIR, ensure_project_directories
from src.geology3d import build_interactive_model, sample_cross_section
from src.loaders import load_tribal_boundaries, load_wsd_fault_points
from src.provenance import write_sidecar
from src.constants import WSD_3D_MODEL, ANALYSIS_CONFIG


def main() -> None:
    ensure_project_directories()
    boundaries = load_tribal_boundaries(["Pine Ridge"])
    faults = load_wsd_fault_points()
    output = OUTPUTS_DIR/"04_full_3d_geology_model.html"
    build_interactive_model(
        output, faults=faults, boundaries=boundaries,
        stride=ANALYSIS_CONFIG["model_3d_stride"],
        vertical_exaggeration=ANALYSIS_CONFIG["vertical_exaggeration"],
    )
    transect = LineString([(-103.45, 43.15), (-101.55, 43.15)])
    cross_section = OUTPUTS_DIR/"04_pine_ridge_cross_section.csv"
    sample_cross_section(transect).to_csv(cross_section, index=False)
    source = [{"title": "USGS Western South Dakota 3D model", "doi": WSD_3D_MODEL["doi"]}]
    write_sidecar(output, sources=source,
                  parameters={
                      "stride": ANALYSIS_CONFIG["model_3d_stride"],
                      "vertical_exaggeration": ANALYSIS_CONFIG["vertical_exaggeration"],
                  },
                  evidence_class="regional-geology-screening")
    write_sidecar(cross_section, sources=source,
                  parameters={"n_points": 500, "transect_wgs84": list(transect.coords)},
                  evidence_class="regional-geology-screening")
    print(output)


if __name__ == "__main__":
    main()
