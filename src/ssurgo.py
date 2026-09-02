from __future__ import annotations

"""Reproducible USDA Soil Data Access queries and soil-property summaries."""

from io import BytesIO
from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

SDA_TABULAR_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
SDA_SPATIAL_URL = "https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84Geographic.wfs"


class SDAError(RuntimeError):
    """Raised when Soil Data Access returns an invalid or unsuccessful response."""


def sda_query(sql: str, timeout: int = 120, session=None) -> pd.DataFrame:
    """Run an SDA tabular query and return a DataFrame with named columns."""
    client = session or requests
    response = client.post(
        SDA_TABULAR_URL,
        json={"query": " ".join(sql.split()), "format": "JSON+COLUMNNAME"},
        timeout=timeout,
    )
    try:
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise SDAError(f"SDA tabular request failed ({response.status_code})") from exc
    table = payload.get("Table") or []
    if not table:
        return pd.DataFrame()
    return pd.DataFrame(table[1:], columns=[str(c).lower() for c in table[0]])


def survey_catalog(areasymbols: Iterable[str] | None = None) -> pd.DataFrame:
    """Return authoritative SDA catalog records, optionally for selected surveys."""
    where = ""
    if areasymbols:
        symbols = sorted({str(symbol).upper() for symbol in areasymbols})
        quoted = ",".join(f"'{symbol}'" for symbol in symbols)
        where = f" WHERE areasymbol IN ({quoted})"
    return sda_query(
        "SELECT areasymbol, areaname, saverest, tabularversion "
        f"FROM sacatalog{where} ORDER BY areasymbol"
    )


def survey_status(areasymbols: Iterable[str]) -> pd.DataFrame:
    """Compare requested survey symbols with the current public SDA catalog."""
    requested = pd.DataFrame({"areasymbol": sorted({s.upper() for s in areasymbols})})
    catalog = survey_catalog(requested["areasymbol"])
    status = requested.merge(catalog, on="areasymbol", how="left", indicator=True)
    status["public_sda_status"] = status.pop("_merge").map(
        {"both": "present", "left_only": "not_listed", "right_only": "unexpected"}
    )
    return status


def fetch_mapunit_polygons(areasymbol: str, timeout: int = 300) -> gpd.GeoDataFrame:
    """Fetch public map-unit polygons for one catalog-validated survey area."""
    symbol = areasymbol.upper()
    response = requests.get(
        SDA_SPATIAL_URL,
        params={
            "SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
            "TYPENAME": "MapunitPoly", "OUTPUTFORMAT": "application/json",
            "Filter": (
                '<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">'
                '<ogc:PropertyIsEqualTo><ogc:PropertyName>areasymbol</ogc:PropertyName>'
                f'<ogc:Literal>{symbol}</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>'
            ),
        },
        timeout=timeout,
    )
    try:
        response.raise_for_status()
        result = gpd.read_file(BytesIO(response.content)).to_crs("EPSG:4326")
    except Exception as exc:
        raise SDAError(f"SDA spatial request failed for {symbol} ({response.status_code})") from exc
    result.columns = [str(column).lower() for column in result.columns]
    result["areasymbol"] = symbol
    return result


def dominant_components(components: pd.DataFrame) -> pd.DataFrame:
    """Return the largest component per map unit while retaining uncertainty fields."""
    required = {"mukey", "comppct_r"}
    missing = required - set(components.columns)
    if missing:
        raise ValueError(f"Component table is missing: {sorted(missing)}")
    frame = components.copy()
    frame["comppct_r"] = pd.to_numeric(frame["comppct_r"], errors="coerce")
    frame = frame.sort_values(["mukey", "comppct_r"], ascending=[True, False])
    dominant = frame.drop_duplicates("mukey").copy()
    dominant["mapped_component_pct"] = frame.groupby("mukey")["comppct_r"].transform("sum").loc[dominant.index]
    dominant["dominant_component_pct"] = dominant["comppct_r"]
    dominant["non_dominant_pct"] = (100 - dominant["dominant_component_pct"]).clip(lower=0)
    return dominant.reset_index(drop=True)


def horizon_weighted_properties(
    horizons: pd.DataFrame,
    properties: Iterable[str],
    top_cm: float = 0,
    bottom_cm: float = 30,
) -> pd.DataFrame:
    """Thickness-weight horizon properties over a requested depth interval."""
    required = {"cokey", "hzdept_r", "hzdepb_r"}
    missing = required - set(horizons.columns)
    if missing:
        raise ValueError(f"Horizon table is missing: {sorted(missing)}")
    frame = horizons.copy()
    top = pd.to_numeric(frame["hzdept_r"], errors="coerce")
    bottom = pd.to_numeric(frame["hzdepb_r"], errors="coerce")
    frame["overlap_cm"] = np.maximum(0, np.minimum(bottom, bottom_cm) - np.maximum(top, top_cm))
    frame = frame[frame["overlap_cm"] > 0]
    rows = []
    for cokey, group in frame.groupby("cokey"):
        row = {"cokey": cokey, "covered_depth_cm": group["overlap_cm"].sum()}
        for prop in properties:
            values = pd.to_numeric(group.get(prop), errors="coerce")
            valid = values.notna()
            row[prop] = np.average(values[valid], weights=group.loc[valid, "overlap_cm"]) if valid.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)
