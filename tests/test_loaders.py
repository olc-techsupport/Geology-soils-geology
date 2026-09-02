from pathlib import Path

from src import loaders


def test_discovery_is_recursive_and_ignores_ppkx(tmp_path, monkeypatch):
    (tmp_path/"survey"/"soil.gdb").mkdir(parents=True)
    (tmp_path/"map.ppkx").write_bytes(b"not a soil database")
    monkeypatch.setattr(loaders, "SSURGO_DIR", tmp_path)
    assert loaders.discover_ssurgo_geodatabases() == [(tmp_path/"survey"/"soil.gdb").resolve()]
    inventory = loaders.ssurgo_inventory()
    assert set(inventory["kind"]) == {"geodatabase", "arcgis_project_package"}
