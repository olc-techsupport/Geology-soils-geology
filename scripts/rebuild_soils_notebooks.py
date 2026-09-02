"""Build evidence-bounded soils notebooks 05–07."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
KERNEL = {"display_name": "Python (tribal-soils-geology)", "language": "python", "name": "tribal-soils-geology"}


def notebook(cells):
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = KERNEL
    nb.metadata["language_info"] = {"name": "python", "version": "3.11"}
    return nb


setup = '''import sys
from pathlib import Path
REPO_ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p/"src").is_dir())
sys.path.insert(0, str(REPO_ROOT)) if str(REPO_ROOT) not in sys.path else None
import pandas as pd
import geopandas as gpd
import yaml
from IPython.display import display
from src.constants import REPO_ROOT as ROOT, OUTPUTS_DIR
from src.loaders import load_tribal_boundaries
with open(ROOT/"config"/"config.yaml") as stream: CONFIG = yaml.safe_load(stream)
primary = load_tribal_boundaries(["Pine Ridge", "Rosebud"])
pine_ridge = primary[primary["NAME"] == "Pine Ridge"]
rosebud = primary[primary["NAME"] == "Rosebud"]'''


def build_05():
    cells = [
        nbf.v4.new_markdown_cell('''# 05 — Public Soils Availability and Coverage

This notebook audits public soil-data availability. It does **not** assume that Oglala Lakota soils are available, and it does not use adjacent-county soils as a substitute. A missing catalog record documents public availability status only; it does not establish why data are absent.'''),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_markdown_cell('''## Local inventory

`.ppkx` watershed projects are reported but rejected as SSURGO sources. Only actual soil geodatabases enter coverage assessment.'''),
        nbf.v4.new_code_cell('''from src.loaders import ssurgo_inventory, load_ssurgo_mapunits
inventory = ssurgo_inventory()
display(inventory)
mapunits = load_ssurgo_mapunits()
print(f"Usable local SSURGO polygons: {len(mapunits):,}")'''),
        nbf.v4.new_markdown_cell('''## Reproducible public-catalog check

Set `RUN_LIVE_AUDIT=True` only when intentionally contacting USDA. Record the timestamp, endpoint, requested identifiers, and exact machine-observed status. `not_listed` and request failure are different outcomes; neither establishes causation.'''),
        nbf.v4.new_code_cell('''from datetime import datetime, timezone
from src.ssurgo import SDA_TABULAR_URL, SDAError, survey_status
RUN_LIVE_AUDIT = False
candidates = sorted({s for group in CONFIG["ssurgo_areasymbol"].values() for s in group})
audit = pd.DataFrame({"requested_areasymbol": candidates})
audit["checked_at_utc"] = pd.NA
audit["endpoint"] = SDA_TABULAR_URL
audit["machine_status"] = "not_checked_this_run"
if RUN_LIVE_AUDIT:
    checked = datetime.now(timezone.utc).isoformat()
    try:
        live = survey_status(candidates).rename(columns={"areasymbol": "requested_areasymbol"})
        audit = audit.drop(columns=["machine_status"]).merge(live, on="requested_areasymbol", how="left")
        audit["checked_at_utc"] = checked
        audit["endpoint"] = SDA_TABULAR_URL
    except SDAError as exc:
        audit["checked_at_utc"] = checked
        audit["machine_status"] = f"request_failed: {exc}"
display(audit)
print("Practical conclusion: no Oglala Lakota SSURGO source has been obtained through the tested regular public pathways.")'''),
        nbf.v4.new_markdown_cell('''## Geographic coverage gate

Analytical coverage is measured against each reservation polygon. The analysis stops below the configured threshold; nearby polygons may be displayed only as explicitly labeled regional context.'''),
        nbf.v4.new_code_cell('''from src.soil_evidence import assess_coverage, require_coverage, SoilCoverageError
reports = [assess_coverage(mapunits, boundary, name) for name, boundary in [("Pine Ridge public SSURGO", pine_ridge), ("Rosebud public SSURGO", rosebud)]]
display(pd.DataFrame([r.__dict__ for r in reports]))
try:
    require_coverage(mapunits, pine_ridge, "Pine Ridge public SSURGO")
    print("Pine Ridge public-soils analysis authorized by coverage gate.")
except SoilCoverageError as exc:
    print(exc)
    print("Result: Pine Ridge soil attributes remain UNKNOWN; adjacent surveys are context only.")'''),
        nbf.v4.new_markdown_cell('''## Defensible conclusion

> Oglala Lakota soils data were not obtained through the tested public USDA pathways as of the recorded checks.

Cause is unconfirmed. Legitimate next routes are Nation-authorized access, a Nation-to-Nation/institutional agreement with NRCS, or Tribal-owned field collection. This notebook does not interpolate surrounding counties into the missing geography.'''),
    ]
    nbf.write(notebook(cells), ROOT/"Notebooks"/"05_soil_survey_ssurgo.ipynb")


def build_06():
    cells = [
        nbf.v4.new_markdown_cell('''# 06 — Tribal-Controlled Soil Profiles

This notebook analyzes only explicitly authorized field records. Public SSURGO horizons are not expected for Pine Ridge and are not a prerequisite. Empty authorized input is a valid outcome, not an invitation to substitute surrounding-county data.'''),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_markdown_cell('''## Governance and authorization gate

Required record fields are `data_authority`, `access_level`, `authorized_use`, and `authorization_date`. The template example row is illustrative and is never loaded automatically.'''),
        nbf.v4.new_code_cell('''from src.loaders import load_tribal_soil_profiles
from src.soil_evidence import validate_governed_profiles, GovernanceError, REQUIRED_GOVERNANCE_FIELDS
profiles = load_tribal_soil_profiles()
print(f"Records discovered in governed raw-data location: {len(profiles):,}")
try:
    authorized_profiles = validate_governed_profiles(profiles, authorized_use="soils analysis")
except GovernanceError as exc:
    authorized_profiles = pd.DataFrame()
    print(f"Governance gate stopped analysis: {exc}")
print(f"Records authorized for this use: {len(authorized_profiles):,}")'''),
        nbf.v4.new_markdown_cell('''## Field-data quality checks

Checks are applied only after authorization. They validate identifiers, coordinates, horizon depth order, overlap, and plausible field ranges without altering raw observations.'''),
        nbf.v4.new_code_cell('''if authorized_profiles.empty:
    print("No authorized profiles: soil properties remain UNKNOWN. No maps or summaries are produced.")
else:
    q = authorized_profiles.copy()
    for column in ["lat", "lon", "depth_top_cm", "depth_bottom_cm", "ph"]:
        q[column] = pd.to_numeric(q[column], errors="coerce")
    q["valid_coordinates"] = q["lat"].between(42, 46) & q["lon"].between(-105, -96)
    q["valid_depth_order"] = q["depth_top_cm"].ge(0) & q["depth_bottom_cm"].gt(q["depth_top_cm"])
    q["valid_ph"] = q["ph"].isna() | q["ph"].between(0, 14)
    q["quality_pass"] = q[["valid_coordinates", "valid_depth_order", "valid_ph"]].all(axis=1)
    display(q[["profile_id", "horizon", "quality_pass", "valid_coordinates", "valid_depth_order", "valid_ph"]])
    analysis_profiles = q[q["quality_pass"]].copy()
    print(f"Authorized records passing quality checks: {len(analysis_profiles):,}")'''),
        nbf.v4.new_markdown_cell('''## Evidence limit

Results from authorized profiles describe sampled locations only. They are not reservation-wide estimates unless a separately reviewed sampling design supports that inference.'''),
    ]
    nbf.write(notebook(cells), ROOT/"Notebooks"/"06_soil_profiles_horizons.ipynb")


def build_07():
    cells = [
        nbf.v4.new_markdown_cell('''# 07 — Geologic Hazards and Evidence Boundaries

Hazard evidence is separated into geology-supported, public-soils-supported, field-supported, and unknown. This notebook does not derive a reservation-wide soil-hazard map from absent Pine Ridge SSURGO coverage.'''),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell('''from src.soil_evidence import evidence_register
register = evidence_register()
display(register)'''),
        nbf.v4.new_markdown_cell('''## Geology-supported evidence

The Spangler model can support statements about modeled formation-top elevation and relative subsurface position. It cannot by itself supply soil texture, shrink–swell measurements, erodibility, or site-specific geotechnical properties.'''),
        nbf.v4.new_code_cell('''depth_figure = ROOT/"outputs"/"figures"/"04_depth_to_pierre_shale.png"
cross_section = ROOT/"outputs"/"04_pine_ridge_cross_section.csv"
display(pd.DataFrame([
    ["Depth-to-Pierre diagnostic", depth_figure.exists(), "geology-supported", "DEM/model datum and resolution uncertainty applies"],
    ["Modeled horizon cross-section", cross_section.exists(), "geology-supported", "regional model; not site investigation"],
], columns=["artifact", "available", "evidence_level", "constraint"]))'''),
        nbf.v4.new_markdown_cell('''## Public-soils coverage gate

Expansive-soil, hydrologic-group, farmland, and erodibility outputs require verified local soil polygons and attributes. The gate prevents adjacent surveys from becoming implicit Pine Ridge estimates.'''),
        nbf.v4.new_code_cell('''from src.loaders import load_ssurgo_mapunits
from src.soil_evidence import require_coverage, SoilCoverageError
mapunits = load_ssurgo_mapunits()
try:
    require_coverage(mapunits, pine_ridge, "Pine Ridge public SSURGO")
    public_soil_hazards_allowed = True
except SoilCoverageError as exc:
    public_soil_hazards_allowed = False
    print(exc)
if not public_soil_hazards_allowed:
    print("No reservation-wide SSURGO soil-hazard classification is produced.")'''),
        nbf.v4.new_markdown_cell('''## Field-supported evidence

Authorized field observations can support sampled-site interpretations after governance and quality gates. Unsampled Pine Ridge soils remain `unknown`; absence of data is not evidence of low hazard or uniform conditions.'''),
        nbf.v4.new_code_cell('''hazard_summary = pd.DataFrame([
    ["Pierre Shale proximity", "geology-supported", "Screening only; verify datum and investigate site"],
    ["Expansive soil", "unknown without authorized soil measurements", "Do not map reservation-wide"],
    ["Soil erodibility", "unknown without authorized soil measurements", "Do not infer from adjacent counties"],
    ["Site geotechnical suitability", "site investigation required", "No regional dataset substitutes for design investigation"],
], columns=["question", "current_evidence", "permitted_interpretation"])
display(hazard_summary)'''),
    ]
    nbf.write(notebook(cells), ROOT/"Notebooks"/"07_geologic_hazards.ipynb")


if __name__ == "__main__":
    build_05(); build_06(); build_07()
