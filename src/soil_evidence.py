"""Evidence boundaries and governance checks for soils analyses."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import geopandas as gpd
import pandas as pd

REQUIRED_GOVERNANCE_FIELDS = [
    "data_authority", "access_level", "authorized_use", "authorization_date",
]
PURPOSE_IDS = {"soils-analysis", "aquifer-geology", "geologic-hazards", "education"}
ALLOWED_ACCESS_LEVELS = {"internal", "restricted", "public"}


class SoilCoverageError(RuntimeError):
    pass


class GovernanceError(ValueError):
    pass


@dataclass(frozen=True)
class CoverageReport:
    source: str
    coverage_fraction: float
    threshold: float
    feature_count: int
    status: str


def assess_coverage(data: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame,
                    source: str, threshold: float = 0.95) -> CoverageReport:
    """Measure actual polygon coverage of a requested sovereign geography."""
    if boundary.empty:
        raise ValueError("Boundary is empty")
    if data.empty or "geometry" not in data:
        return CoverageReport(source, 0.0, threshold, 0, "unavailable")
    target = boundary.to_crs("EPSG:5070").geometry.union_all()
    valid = data[data.geometry.notna() & ~data.geometry.is_empty].to_crs("EPSG:5070")
    covered = valid.geometry.union_all().intersection(target).area
    fraction = min(1.0, covered / target.area) if target.area else 0.0
    status = "sufficient" if fraction >= threshold else "insufficient"
    return CoverageReport(source, fraction, threshold, len(valid), status)


def require_coverage(data: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame,
                     source: str, threshold: float = 0.95,
                     expected_areasymbols: set[str] | None = None) -> CoverageReport:
    if expected_areasymbols is not None:
        if "areasymbol" not in data.columns:
            raise SoilCoverageError(f"{source} has no areasymbol field; source relevance cannot be verified")
        observed = set(data["areasymbol"].dropna().astype(str).str.upper())
        unexpected = observed - {value.upper() for value in expected_areasymbols}
        if unexpected:
            raise SoilCoverageError(f"{source} includes unapproved survey areas: {sorted(unexpected)}")
    report = assess_coverage(data, boundary, source, threshold)
    if report.status != "sufficient":
        raise SoilCoverageError(
            f"{source} covers {report.coverage_fraction:.1%} of the requested geography; "
            f"{report.threshold:.1%} is required. Analysis stopped—adjacent data are context only."
        )
    return report


def validate_governed_profiles(frame: pd.DataFrame, authorized_use: str | None = None) -> pd.DataFrame:
    """Validate field profiles and return only explicitly authorized records."""
    missing = [field for field in REQUIRED_GOVERNANCE_FIELDS if field not in frame.columns]
    if missing:
        raise GovernanceError(f"Missing governance fields: {missing}")
    result = frame.copy()
    result["access_level"] = result["access_level"].astype(str).str.lower()
    invalid = ~result["access_level"].isin(ALLOWED_ACCESS_LEVELS)
    if invalid.any():
        raise GovernanceError("Invalid access_level; use internal, restricted, or public")
    for field in ["data_authority", "authorized_use", "authorization_date"]:
        if result[field].isna().any() or result[field].astype(str).str.strip().eq("").any():
            raise GovernanceError(f"Every record requires {field}")
    result["authorized_use"] = result["authorized_use"].astype(str).str.strip().str.lower()
    invalid_purposes = ~result["authorized_use"].isin(PURPOSE_IDS)
    if invalid_purposes.any():
        raise GovernanceError(f"authorized_use must be one of: {sorted(PURPOSE_IDS)}")
    result["authorization_date"] = pd.to_datetime(result["authorization_date"], errors="coerce")
    if result["authorization_date"].isna().any():
        raise GovernanceError("authorization_date must be a valid date")
    if authorized_use is not None:
        purpose = authorized_use.strip().lower()
        if purpose not in PURPOSE_IDS:
            raise GovernanceError(f"Requested purpose must be one of: {sorted(PURPOSE_IDS)}")
        result = result[result["authorized_use"] == purpose]
    return result.reset_index(drop=True)


def validate_governed_records(frame: pd.DataFrame, purpose: str) -> pd.DataFrame:
    """Apply the common deny-by-default governance gate to any record type."""
    return validate_governed_profiles(frame, authorized_use=purpose)


def evidence_register() -> pd.DataFrame:
    return pd.DataFrame([
        ["Modeled geology", "regional", "geology-supported", "Formation tops; not soil properties"],
        ["Public SSURGO", "verified polygons only", "public-soils-supported", "No spatial extrapolation"],
        ["Tribal field profiles", "authorized records only", "field-supported", "Governance gate required"],
        ["Pine Ridge soils without authorized observations", "unknown", "unknown", "No soil inference"],
    ], columns=["source", "valid_scope", "evidence_level", "constraint"])
