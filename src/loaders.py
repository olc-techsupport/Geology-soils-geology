from __future__ import annotations

"""
loaders.py Public data loaders for tribal_soils_geology.

All functions follow the same pattern:
  - Check cache first, download only if needed
  - force_refresh=True to re-download
  - Return clean GeoDataFrame or DataFrame
  - Treat missing/sparse data as a policy finding, not an error

Data sources:
  Census TIGER  : AIANNH Tribal boundaries
  USGS NWIS     : Well logs and groundwater sites
  USGS 3D Model : Spangler 2024, loaded from local GDB
  USDA SSURGO   : Loaded from local GDB (ESRI Soil Data Downloader)
  USGS State Geology : Loaded from local GDB (mrdata.usgs.gov)
  USGS 3DEP     : Digital elevation model tiles
  NHD           : Stream network and watershed boundaries
"""

import io
import json
import logging
import warnings
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
from io import BytesIO
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.constants import (
    CACHE_DIR,
    CRS_GEOGRAPHIC,
    CRS_PROJECTED,
    CENSUS_TIGER_BASE,
    USGS_NWIS_SITE_URL,
    NHD_FLOWLINE_URL,
    WBD_HUC8_URL,
    CENSUS_TO_COMMON,
    WSD_3D_MODEL,
    GEOLOGY_DIR,
    SSURGO_DIR,
    STATE_GEOLOGY_FILENAME,
)

log = logging.getLogger(__name__)

_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)


# Tribal boundaries
def load_tribal_boundaries(
    nation_names: list[str] | None = None,
    force_refresh: bool = False,
) -> gpd.GeoDataFrame:
    """
    Load AIANNH Tribal boundaries from Census TIGER.

    Parameters
    nation_names  : Census NAME field values to filter.
                    Defaults to Pine Ridge only.
    force_refresh : Re-download even if cached.

    Returns
    GeoDataFrame with columns: NAME, common_name, area_km2, geometry
    """
    if nation_names is None:
        nation_names = ["Pine Ridge"]

    cache_path = CACHE_DIR / "tl_2023_us_aiannh.geojson"

    if not cache_path.exists() or force_refresh:
        log.info("Downloading Census TIGER AIANNH boundaries...")
        url = f"{CENSUS_TIGER_BASE}/TIGER2023/AIANNH/tl_2023_us_aiannh.zip"
        r   = requests.get(url, timeout=300)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            with tempfile.TemporaryDirectory() as tmp:
                z.extractall(tmp)
                shp = next(Path(tmp).glob("*.shp"))
                all_aiannh = gpd.read_file(shp).to_crs(CRS_GEOGRAPHIC)
        all_aiannh.to_file(cache_path, driver="GeoJSON")
        log.info("AIANNH cached: %d features", len(all_aiannh))
    else:
        all_aiannh = gpd.read_file(cache_path)

    from shapely.validation import make_valid
    gdf = all_aiannh[all_aiannh["NAME"].isin(nation_names)].copy()
    gdf = gdf.dissolve(by="NAME", as_index=False)
    gdf["geometry"]    = gdf.geometry.apply(make_valid)
    gdf["common_name"] = gdf["NAME"].map(CENSUS_TO_COMMON)
    gdf["area_km2"]    = gdf.to_crs(CRS_PROJECTED).geometry.area / 1e6
    return gdf.reset_index(drop=True)


# NHD stream network
@_retry
def load_nhd_flowlines(bbox, min_stream_order=2, named_only=False):
    NHD_URL = (
        "https://hydro.nationalmap.gov/arcgis/rest/services/"
        "NHDPlus_HR/MapServer/3/query"
    )

    where_parts = [f"streamorde >= {min_stream_order}"]
    if named_only:
        where_parts.append("gnis_name IS NOT NULL AND gnis_name <> ''")
    where = " AND ".join(where_parts)

    all_features = []
    offset = 0
    batch_size = 2000

    while True:
        r = requests.get(NHD_URL, params={
            "where":             where,
            "outFields":         "reachcode,gnis_name,streamorde,lengthkm",
            "f":                 "geojson",
            "returnGeometry":    "true",
            "outSR":             "4326",
            "geometry":          f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "geometryType":      "esriGeometryEnvelope",
            "inSR":              "4326",
            "resultOffset":      offset,
            "resultRecordCount": batch_size,
        }, timeout=120)

        if r.status_code != 200 or len(r.content) < 100:
            break

        batch = gpd.read_file(BytesIO(r.content))
        if batch.empty:
            break

        all_features.append(batch)
        print(f"  Fetched {len(batch)} features (offset {offset})")

        if len(batch) < batch_size:
            break
        offset += batch_size

    if not all_features:
        return gpd.GeoDataFrame()

    streams = pd.concat(all_features, ignore_index=True)
    streams = streams.set_crs("EPSG:4326", allow_override=True)
    print(f"Total stream segments: {len(streams):,}")
    return streams


# HUC watershed boundaries

@_retry
def load_huc_boundary(
    bbox: tuple[float, float, float, float],
    huc_level: int = 8,
    force_refresh: bool = False,
) -> gpd.GeoDataFrame:
    """Load USGS WBD HUC polygons within a bounding box."""
    cache_key  = (f"wbd_huc{huc_level}_{bbox[0]:.2f}_{bbox[1]:.2f}"
                  f"_{bbox[2]:.2f}_{bbox[3]:.2f}.geojson")
    cache_file = CACHE_DIR/cache_key

    if cache_file.exists() and not force_refresh:
        return gpd.read_file(cache_file)

    layer_map = {2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6}
    layer_id  = layer_map.get(huc_level, 4)
    url = (f"https://hydro.nationalmap.gov/arcgis/rest/services/"
           f"wbd/MapServer/{layer_id}/query")

    r = requests.get(
        url,
        params={
            "where":          "1=1",
            "outFields":      f"huc{huc_level},name,areasqkm",
            "f":              "geojson",
            "returnGeometry": "true",
            "outSR":          "4326",
            "geometry":       f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "geometryType":   "esriGeometryEnvelope",
            "spatialRel":     "esriSpatialRelIntersects",
            "inSR":           "4326",
        },
        timeout=120,
    )
    if r.status_code == 500:
        return gpd.GeoDataFrame()
    r.raise_for_status()
    try:
        payload = r.json()
    except Exception:
        return gpd.GeoDataFrame()
    if not payload.get("features"):
        return gpd.GeoDataFrame()
    gdf = gpd.read_file(io.BytesIO(r.content))
    if not gdf.empty:
        gdf = gdf.set_crs(CRS_GEOGRAPHIC, allow_override=True)
        gdf.to_file(cache_file, driver="GeoJSON")
    return gdf


# USGS NWIS well sites

def load_usgs_well_sites(
    bbox: tuple[float, float, float, float],
    force_refresh: bool = False,
) -> gpd.GeoDataFrame:
    """
    Fetch USGS groundwater monitoring well sites within a bounding box.

    Returned records are an endpoint inventory, not a causal coverage analysis.
    Compare timestamped, geometry-clipped inventories before reporting a gap.
    """
    bbox_str   = f"{bbox[0]:.2f}_{bbox[1]:.2f}_{bbox[2]:.2f}_{bbox[3]:.2f}"
    cache_file = CACHE_DIR/f"usgs_gw_sites_{bbox_str}.csv"

    if cache_file.exists() and not force_refresh:
        df = pd.read_csv(cache_file, dtype=str)
    else:
        try:
            r = requests.get(
                "https://waterservices.usgs.gov/nwis/site/",
                params={
                    "format":     "rdb",
                    "bBox":       f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                    "siteType":   "GW",
                    "siteStatus": "all",
                },
                timeout=60,
            )
            r.raise_for_status()
            df = _parse_nwis_site_rdb(r.text)
            df.to_csv(cache_file, index=False)
        except Exception as e:
            warnings.warn(
                f"USGS well site query failed: {e}. "
                "A request failure is not evidence of zero sites or its cause.",
                UserWarning, stacklevel=2,
            )
            return gpd.GeoDataFrame()

    if df.empty:
        warnings.warn(
            "The USGS query returned no records. This does not establish why: "
            "verify endpoint status, parameters, timestamp, and geography.",
            UserWarning, stacklevel=2,
        )
        return gpd.GeoDataFrame()

    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower()
                    or "long" in c.lower()), None)
    if not lat_col or not lon_col:
        return gpd.GeoDataFrame(df)

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)
    df = df.rename(columns={lat_col: "dec_lat_va", lon_col: "dec_long_va"})

    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["dec_long_va"], df["dec_lat_va"]),
        crs=CRS_GEOGRAPHIC,
    )


# USGS 3D Geological Model (local file)

def load_wsd_3d_model_boundary() -> gpd.GeoDataFrame:
    """
    Load the model boundary polygon from the WSD 3D Model GDB.
    This defines the geographic footprint of the Spangler 2024 model.

    Requires: data/raw/geology/WSouthDakota3D.gdb/
    Download: https://doi.org/10.5066/P9LK4QHJ
    """
    gdb_path = WSD_3D_MODEL["gdb_path"]
    if not gdb_path.exists():
        warnings.warn(
            "WSouthDakota3D.gdb not found in data/raw/geology/. "
            "Download from https://doi.org/10.5066/P9LK4QHJ and extract there.",
            UserWarning, stacklevel=2,
        )
        return gpd.GeoDataFrame()

    try:
        gdf = gpd.read_file(gdb_path, layer="ModelBoundary")
        return gdf.to_crs(CRS_GEOGRAPHIC)
    except Exception as e:
        warnings.warn(f"Could not read ModelBoundary from GDB: {e}", UserWarning)
        return gpd.GeoDataFrame()


def load_wsd_fault_points() -> gpd.GeoDataFrame:
    """
    Load fault point data from the WSD 3D Model GDB.
    35 fault surfaces represented as point clouds.

    Requires: data/raw/geology/WSouthDakota3D.gdb/
    """
    gdb_path = WSD_3D_MODEL["gdb_path"]
    if not gdb_path.exists():
        warnings.warn(
            "WSouthDakota3D.gdb not found. "
            "Download from https://doi.org/10.5066/P9LK4QHJ",
            UserWarning, stacklevel=2,
        )
        return gpd.GeoDataFrame()

    try:
        gdf = gpd.read_file(gdb_path, layer="FaultPoints")
        return gdf.to_crs(CRS_GEOGRAPHIC)
    except Exception as e:
        warnings.warn(f"Could not read FaultPoints from GDB: {e}", UserWarning)
        return gpd.GeoDataFrame()


def load_wsd_model_units() -> pd.DataFrame:
    """
    Load the DescriptionOfModelUnits table from WSD nonspatial tables.
    Contains formation names, descriptions, and modeling notes.

    Requires: data/raw/geology/WSD_NonspatialTables/
    """
    gdb_path = WSD_3D_MODEL["gdb_path"]
    if gdb_path.exists():
        try:
            table = gpd.read_file(gdb_path, layer="DescriptionOfModelUnits")
            return pd.DataFrame(table.drop(columns="geometry", errors="ignore"))
        except Exception as exc:
            warnings.warn(f"Could not read DescriptionOfModelUnits from GDB: {exc}", UserWarning)

    tables_path = WSD_3D_MODEL["tables_path"]
    candidates  = list(tables_path.glob("*ModelUnit*")) if tables_path.exists() else []
    if not candidates:
        # Also check for CSV files
        candidates = list(tables_path.glob("*.csv")) if tables_path.exists() else []

    if not candidates:
        warnings.warn(
            "WSD_NonspatialTables not found in data/raw/geology/. "
            "Download from https://doi.org/10.5066/P9LK4QHJ",
            UserWarning, stacklevel=2,
        )
        return pd.DataFrame()

    try:
        # Try DescriptionOfModelUnits first
        model_units_file = next(
            (f for f in candidates if "ModelUnit" in f.name),
            candidates[0]
        )
        return pd.read_csv(model_units_file, dtype=str)
    except Exception as e:
        warnings.warn(f"Could not read model units table: {e}", UserWarning)
        return pd.DataFrame()


_WSD_HORIZON_LAYER_CACHE: tuple[str, ...] | None = None


def resolve_wsd_horizon_layer(unit_name: str) -> str:
    """Resolve a published unit name or raw GDB name to a raster subdataset."""
    import rasterio
    gdb_path = WSD_3D_MODEL["gdb_path"]
    if not gdb_path.exists():
        raise FileNotFoundError(gdb_path)
    global _WSD_HORIZON_LAYER_CACHE
    if _WSD_HORIZON_LAYER_CACHE is None:
        with rasterio.open(gdb_path) as dataset:
            _WSD_HORIZON_LAYER_CACHE = tuple(
                item.rsplit(":", 1)[-1] for item in dataset.subdatasets
            )
    layers = list(_WSD_HORIZON_LAYER_CACHE)
    if unit_name in layers:
        return unit_name

    normalise = lambda value: "".join(c for c in str(value).lower() if c.isalnum())
    lookup = {normalise(layer.removeprefix("WSD_Top")): layer for layer in layers}
    aliases = {
        normalise("Stony Mountain Formation"): "WSD_TopStoneyMountainFormation",
        normalise("Three Forks Shale"): "WSD_TopThreeForksFormation",
    }
    lookup.update({key: layer for key, layer in aliases.items() if layer in layers})
    key = normalise(unit_name)
    if key not in lookup:
        known = load_wsd_model_units()
        names = sorted(known["Name"].dropna().astype(str)) if "Name" in known else []
        raise KeyError(f"Unknown model unit {unit_name!r}. Known unit names: {names}")
    return lookup[key]


def load_wsd_horizon_raster(unit_name: str) -> object | None:
    """
    Load a single horizon raster from the WSD 3D Model GDB.
    Returns a rasterio DatasetReader or None if not available.

    Parameters
    unit_name : Formation name matching DescriptionOfModelUnits
                ex. "Ogallala Group", "Pierre Shale"

    Requires: data/raw/geology/WSouthDakota3D.gdb/
    """
    try:
        import rasterio
        gdb_path = WSD_3D_MODEL["gdb_path"]
        if not gdb_path.exists():
            warnings.warn(
                "WSouthDakota3D.gdb not found. "
                "Download from https://doi.org/10.5066/P9LK4QHJ",
                UserWarning, stacklevel=2,
            )
            return None
        layer_name = resolve_wsd_horizon_layer(unit_name)
        ds = rasterio.open(f"OpenFileGDB:{gdb_path}:{layer_name}")
        return ds
    except KeyError as e:
        warnings.warn(str(e), UserWarning, stacklevel=2)
        return None
    except Exception as e:
        warnings.warn(
            f"Could not open horizon raster '{unit_name}': {e}. "
            "The GDB exists, but the resolved raster could not be read.",
            UserWarning, stacklevel=2,
        )
        return None


# SSURGO (local file)

def discover_ssurgo_geodatabases() -> list[Path]:
    """Return unique SSURGO geodatabases found anywhere below ``SSURGO_DIR``.

    ArcGIS project packages (``.ppkx``) are intentionally ignored: they are map
    projects, not SSURGO source databases.  Recursive discovery supports both a
    flat download directory and the usual one-directory-per-survey layout.
    """
    paths = {path.resolve() for path in SSURGO_DIR.rglob("*.gdb") if path.is_dir()}
    return sorted(paths, key=lambda path: str(path).lower())


def _normalise_ssurgo_frame(frame: pd.DataFrame, source: Path) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).lower() for column in frame.columns]
    frame["source_gdb"] = source.name
    return frame


def ssurgo_inventory() -> pd.DataFrame:
    """Inventory usable databases and flag unrelated ArcGIS project packages."""
    rows = []
    for path in discover_ssurgo_geodatabases():
        rows.append({"path": str(path), "kind": "geodatabase", "usable": True})
    for path in sorted(SSURGO_DIR.rglob("*.ppkx")):
        rows.append({"path": str(path), "kind": "arcgis_project_package", "usable": False})
    return pd.DataFrame(rows, columns=["path", "kind", "usable"])

def load_ssurgo_mapunits(
    state_code: str | None = None,
) -> gpd.GeoDataFrame:
    """
    Load SSURGO soil map unit polygons from local GDB.

    Requires: data/raw/ssurgo/ containing the ESRI Soil Data Downloader output.
    Download by AREASYMBOL from: https://websoilsurvey.nrcs.usda.gov/

    Parameters
    state_code : Optional filter (ex. 'SD') applied if a merged GDB is present.
    """
    # Look for any GDB in the ssurgo directory
    gdbs = discover_ssurgo_geodatabases()
    if not gdbs:
        warnings.warn(
            "No SSURGO GDB found in data/raw/ssurgo/. "
            "Download from https://websoilsurvey.nrcs.usda.gov/ using "
            "the ESRI Soil Data Downloader. See docs/data_intake_guide.md.",
            UserWarning, stacklevel=2,
        )
        return gpd.GeoDataFrame()

    parts = []
    for gdb in gdbs:
        try:
            import fiona
            layers = fiona.listlayers(str(gdb))
            mapunit_layer = next(
                (l for l in layers if "mapunit" in l.lower() and
                 "poly" in l.lower()), None
            )
            if mapunit_layer is None:
                mapunit_layer = next(
                    (l for l in layers if "mupolygon" in l.lower()), None
                )
            if mapunit_layer:
                gdf = gpd.read_file(gdb, layer=mapunit_layer)
                parts.append(_normalise_ssurgo_frame(gdf, gdb))
                log.info("SSURGO mapunits loaded from %s: %d polygons",
                         gdb.name, len(gdf))
        except Exception as e:
            warnings.warn(f"Could not read {gdb.name}: {e}", UserWarning)

    if not parts:
        warnings.warn(
            "SSURGO GDB found but no map unit polygon layer could be read. "
            "Expected layer name: MUPOLYGON or similar.",
            UserWarning, stacklevel=2,
        )
        return gpd.GeoDataFrame()

    result = pd.concat(parts, ignore_index=True)
    if not isinstance(result, gpd.GeoDataFrame):
        result = gpd.GeoDataFrame(result)
    if "areasymbol" in result.columns and state_code:
        result = result[result["areasymbol"].astype(str).str.startswith(state_code.upper())]
    dedupe = [column for column in ["areasymbol", "mukey", "geometry"] if column in result.columns]
    if dedupe:
        result = result.drop_duplicates(subset=dedupe)
    return result.to_crs(CRS_GEOGRAPHIC)


def load_ssurgo_components() -> pd.DataFrame:
    """
    Load SSURGO component table (one row per component per map unit).
    Contains drainage class, hydrologic group, erodibility, etc.

    Requires: data/raw/ssurgo/ GDB with component table.
    """
    gdbs = discover_ssurgo_geodatabases()
    if not gdbs:
        warnings.warn(
            "No SSURGO GDB found. See load_ssurgo_mapunits docstring.",
            UserWarning, stacklevel=2,
        )
        return pd.DataFrame()

    parts = []
    for gdb in gdbs:
        try:
            import fiona
            layers  = fiona.listlayers(str(gdb))
            comp_layer = next(
                (l for l in layers if l.lower() == "component"), None
            )
            if comp_layer:
                # Components table is nonspatial — read as DataFrame
                gdf = gpd.read_file(gdb, layer=comp_layer)
                table = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
                parts.append(_normalise_ssurgo_frame(table, gdb))
        except Exception as e:
            warnings.warn(f"Could not read component table from {gdb.name}: {e}",
                          UserWarning)

    if not parts:
        return pd.DataFrame()
    result = pd.concat(parts, ignore_index=True)
    keys = [column for column in ["areasymbol", "cokey"] if column in result.columns]
    return result.drop_duplicates(subset=keys or None).reset_index(drop=True)


def load_ssurgo_horizons() -> pd.DataFrame:
    """
    Load SSURGO chorizon table (one row per horizon per component).
    Contains texture, pH, organic matter, bulk density, AWC, etc.

    This is the most data-dense table in SSURGO — horizon-level
    physical and chemical properties.

    Requires: data/raw/ssurgo/ GDB with chorizon table.
    """
    gdbs = discover_ssurgo_geodatabases()
    if not gdbs:
        return pd.DataFrame()

    parts = []
    for gdb in gdbs:
        try:
            import fiona
            layers     = fiona.listlayers(str(gdb))
            horiz_layer = next(
                (l for l in layers if "chorizon" in l.lower()), None
            )
            if horiz_layer:
                gdf = gpd.read_file(gdb, layer=horiz_layer)
                table = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
                parts.append(_normalise_ssurgo_frame(table, gdb))
        except Exception as e:
            warnings.warn(f"Could not read chorizon table from {gdb.name}: {e}",
                          UserWarning)

    if not parts:
        return pd.DataFrame()
    result = pd.concat(parts, ignore_index=True)
    keys = [column for column in ["areasymbol", "chkey"] if column in result.columns]
    return result.drop_duplicates(subset=keys or None).reset_index(drop=True)



# State geologic map (local file)

def load_state_geology(bbox=None):
    shp = GEOLOGY_DIR/STATE_GEOLOGY_FILENAME
    if not shp.exists():
        warnings.warn("SD_geol_poly.shp not found in data/raw/geology/", UserWarning)
        return gpd.GeoDataFrame()

    gdf = gpd.read_file(str(shp))
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # Join unit descriptions from SD_units.csv
    units_csv = GEOLOGY_DIR / "SD_units.csv"
    if units_csv.exists():
        units = pd.read_csv(units_csv, dtype=str)
        # Normalize join key to uppercase to match shapefile
        units = units.rename(columns={"unit_link": "UNIT_LINK"})
        gdf = gdf.merge(units, on="UNIT_LINK", how="left")
        log.info("Joined SD_units.csv: added unit_name, unitdesc, rocktype columns")

    if bbox is not None:
        from shapely.geometry import box
        gdf = gdf[gdf.geometry.intersects(box(*bbox))].copy()

    log.info("State geology loaded: %d features", len(gdf))
    return gdf


# Tribal-collected data (local files)

def load_tribal_soil_profiles(
    path=None,
) -> "pd.DataFrame":
    """
    Load Tribal-collected soil profile data from local Excel or CSV.

    This data is denied by Git and stays in local governed storage.
    See Field data forms/soil_profile_template.xlsx for the expected format.
    Returns empty DataFrame with correct columns if file not found.
    """
    from src.constants import SOIL_PROFILE_FIELDS, GOVERNED_DIR, RAW_DIR
    if path is None:
        candidates = [
            GOVERNED_DIR/"soil_profiles.csv",
            GOVERNED_DIR/"soil_profiles.xlsx",
            RAW_DIR/"soil_profiles.csv",
            RAW_DIR/"soil_profiles.xlsx",
        ]
        path = next((p for p in candidates if p.exists()), None)

    if path is None:
        warnings.warn(
            "No Tribal soil profile data found in data/governed/. "
            "See Field data forms/soil_profile_template.xlsx to begin "
            "collecting field measurements.",
            UserWarning, stacklevel=2,
        )
        return pd.DataFrame(columns=SOIL_PROFILE_FIELDS)

    path = Path(path)
    df   = pd.read_excel(path) if path.suffix in (".xlsx", ".xls") \
           else pd.read_csv(path)
    df.columns = df.columns.str.lower().str.strip()
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    return df.dropna(subset=["profile_id", "date"]).reset_index(drop=True)


def load_tribal_well_logs(
    path=None,
) -> "pd.DataFrame":
    """
    Load Tribal-collected well log data from local Excel or CSV.

    This data is denied by Git and stays in local governed storage.
    See Field data forms/well_log_template.xlsx for the expected format.
    """
    from src.constants import WELL_LOG_FIELDS, GOVERNED_DIR, RAW_DIR
    if path is None:
        candidates = [
            GOVERNED_DIR/"well_logs.csv",
            GOVERNED_DIR/"well_logs.xlsx",
            RAW_DIR/"well_logs.csv",
            RAW_DIR/"well_logs.xlsx",
        ]
        path = next((p for p in candidates if p.exists()), None)

    if path is None:
        warnings.warn(
            "No Tribal well log data found in data/governed/. "
            "See Field data forms/well_log_template.xlsx.",
            UserWarning, stacklevel=2,
        )
        return pd.DataFrame(columns=WELL_LOG_FIELDS)

    path = Path(path)
    df   = pd.read_excel(path) if path.suffix in (".xlsx", ".xls") \
           else pd.read_csv(path)
    df.columns = df.columns.str.lower().str.strip()
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    return df.dropna(subset=["well_id", "date"]).reset_index(drop=True)


# Internal helpers

def _parse_nwis_site_rdb(text: str) -> "pd.DataFrame":
    """Parse a USGS NWIS site inventory RDB response."""
    from io import StringIO
    lines      = [l for l in text.splitlines() if not l.startswith("#")]
    if len(lines) < 3:
        return pd.DataFrame()
    cols       = lines[0].split("\t")
    data_lines = [l for l in lines[2:] if l.strip()]
    if not data_lines:
        return pd.DataFrame()
    return pd.read_csv(
        StringIO("\n".join(data_lines)),
        sep="\t", header=None, names=cols, dtype=str,
    )
