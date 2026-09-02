import pandas as pd

from src.ssurgo import dominant_components, horizon_weighted_properties


def test_dominant_components_retains_uncertainty():
    data = pd.DataFrame({
        "mukey": ["1", "1", "2"],
        "comppct_r": [60, 30, 80],
        "compname": ["A", "B", "C"],
    })
    result = dominant_components(data).set_index("mukey")
    assert result.loc["1", "compname"] == "A"
    assert result.loc["1", "non_dominant_pct"] == 40
    assert result.loc["1", "mapped_component_pct"] == 90


def test_horizon_weighting_clips_to_depth_interval():
    horizons = pd.DataFrame({
        "cokey": ["a", "a"], "hzdept_r": [0, 10], "hzdepb_r": [10, 40],
        "claytotal_r": [10, 40],
    })
    result = horizon_weighted_properties(horizons, ["claytotal_r"], 0, 30).iloc[0]
    assert result["covered_depth_cm"] == 30
    assert result["claytotal_r"] == 30
