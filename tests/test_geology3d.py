from pathlib import Path

from src.geology3d import display_name, horizon_catalog
from src.loaders import resolve_wsd_horizon_layer


def test_horizon_display_name():
    assert display_name("WSD_TopPierreShale") == "Pierre Shale"


def test_horizons_follow_published_order_and_separate_intrusive():
    catalog = horizon_catalog()
    assert len(catalog) == 25
    assert catalog.iloc[0]["name"] == "post-Ogallala"
    assert catalog.iloc[-2]["name"] == "Precambrian basement"
    assert catalog.iloc[-1]["name"] == "Tertiary intrusive"
    assert catalog.iloc[-1]["cross_cutting"]
    assert catalog["name"].is_unique


def test_human_and_raw_horizon_names_resolve():
    assert resolve_wsd_horizon_layer("Ogallala Group") == "WSD_TopOgallalaGroup"
    assert resolve_wsd_horizon_layer("pre-Ogallala") == "WSD_TopPreOgallala"
    assert resolve_wsd_horizon_layer("WSD_TopMadisonGroup") == "WSD_TopMadisonGroup"
