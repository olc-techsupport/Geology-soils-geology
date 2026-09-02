import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box
from src.soil_evidence import assess_coverage, require_coverage, SoilCoverageError, validate_governed_profiles, GovernanceError


def test_coverage_gate_rejects_partial_context():
    boundary = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10)], crs="EPSG:5070")
    data = gpd.GeoDataFrame(geometry=[box(0, 0, 5, 10)], crs="EPSG:5070")
    assert assess_coverage(data, boundary, "test").coverage_fraction == pytest.approx(.5)
    with pytest.raises(SoilCoverageError):
        require_coverage(data, boundary, "test")


def test_governance_gate_requires_authorization_fields():
    with pytest.raises(GovernanceError):
        validate_governed_profiles(pd.DataFrame({"profile_id": ["x"]}))


def test_governance_gate_requires_exact_controlled_purpose_and_date():
    data = pd.DataFrame({
        "data_authority": ["Authorized body"],
        "access_level": ["restricted"],
        "authorized_use": ["soils-analysis and anything else"],
        "authorization_date": ["not-a-date"],
    })
    with pytest.raises(GovernanceError):
        validate_governed_profiles(data, "soils-analysis")


def test_governance_gate_accepts_exact_purpose():
    data = pd.DataFrame({
        "data_authority": ["Authorized body"],
        "access_level": ["restricted"],
        "authorized_use": ["soils-analysis"],
        "authorization_date": ["2026-01-01"],
    })
    assert len(validate_governed_profiles(data, "soils-analysis")) == 1
