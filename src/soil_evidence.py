"""Evidence boundaries and governance checks for soils analyses."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import geopandas as gpd
import pandas as pd

REQUIRED_GOVERNANCE_FIELDS = [
    "data_authority", "access_level", "authorized_use", "authorization_date",
]
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
                     source: str, threshold: float = 0.95) -> CoverageReport:
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
    if authorized_use is not None:
        result = result[result["authorized_use"].astype(str).str.contains(
            authorized_use, case=False, regex=False, na=False
        )]
    return result.reset_index(drop=True)


def evidence_register() -> pd.DataFrame:
    return pd.DataFrame([
        ["Modeled geology", "regional", "geology-supported", "Formation tops; not soil properties"],
        ["Public SSURGO", "verified polygons only", "public-soils-supported", "No spatial extrapolation"],
        ["Tribal field profiles", "authorized records only", "field-supported", "Governance gate required"],
        ["Pine Ridge soils without authorized observations", "unknown", "unknown", "No soil inference"],
    ], columns=["source", "valid_scope", "evidence_level", "constraint"])
