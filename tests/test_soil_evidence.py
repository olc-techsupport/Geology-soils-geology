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
