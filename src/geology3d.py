"""Scientifically ordered rendering and cross-sections for Spangler (2024)."""
from __future__ import annotations

from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import rasterio
from pyproj import Transformer
from shapely.geometry import LineString
from src.constants import WSD_3D_MODEL
from src.loaders import load_wsd_model_units

_LAYER_ALIASES = {
    "WSD_TopStoneyMountainFormation": "Stony Mountain Formation",
    "WSD_TopThreeForksFormation": "Three Forks Shale",
}


def _normalise_name(value: str) -> str:
    return "".join(c for c in str(value).lower() if c.isalnum())


def horizon_catalog(gdb_path: Path | None = None) -> pd.DataFrame:
    """Join all raster subdatasets to authoritative model-unit metadata.

    HierarchyKey gives top-to-basement order. The Tertiary intrusive surface is
    cross-cutting, so it is identified separately and placed after the 24
    stratigraphic surfaces.
    """
    path = Path(gdb_path or WSD_3D_MODEL["gdb_path"])
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as dataset:
        names = [item.rsplit(":", 1)[-1] for item in dataset.subdatasets]
    layers = [name for name in names if name.lower().startswith("wsd_top")]
    metadata = load_wsd_model_units().copy()
    if metadata.empty:
        raise ValueError("DescriptionOfModelUnits is required to order horizon rasters")
    metadata["_key"] = metadata["Name"].map(_normalise_name)
    lookup = metadata.set_index("_key")
    rows = []
    for layer in layers:
        expected = _LAYER_ALIASES.get(layer, layer.removeprefix("WSD_Top"))
        key = _normalise_name(expected)
        if key not in lookup.index:
            raise ValueError(f"No DescriptionOfModelUnits match for raster {layer}")
        unit = lookup.loc[key]
        cross_cutting = str(unit["Name"]).lower() == "tertiary intrusive"
        rows.append({
            "layer": layer, "name": unit["Name"], "full_name": unit["FullName"],
            "age": unit["Age"], "hierarchy_key": unit["HierarchyKey"],
            "cross_cutting": cross_cutting,
        })
    catalog = pd.DataFrame(rows)
    catalog["_group"] = catalog["cross_cutting"].astype(int)
    return catalog.sort_values(["_group", "hierarchy_key"]).drop(columns="_group").reset_index(drop=True)


def horizon_layers(gdb_path: Path | None = None) -> list[str]:
    """Return all 25 rasters in metadata-defined geological order."""
    return horizon_catalog(gdb_path)["layer"].tolist()


def display_name(layer: str, gdb_path: Path | None = None) -> str:
    catalog = horizon_catalog(gdb_path)
    match = catalog.loc[catalog["layer"] == layer, "name"]
    return match.iloc[0] if not match.empty else layer.removeprefix("WSD_Top")


def _surface(layer: str, stride: int, gdb_path: Path):
    with rasterio.open(f"OpenFileGDB:{gdb_path}:{layer}") as source:
        z = source.read(1, masked=True)[::stride, ::stride].astype("float64")
        rows = np.arange(0, source.height, stride)
        cols = np.arange(0, source.width, stride)
        x = source.transform.c + (cols + 0.5) * source.transform.a
        y = source.transform.f + (rows + 0.5) * source.transform.e
    return x, y, z.filled(np.nan)


def build_interactive_model(
    output_html: Path,
    gdb_path: Path | None = None,
    faults: gpd.GeoDataFrame | None = None,
    boundaries: gpd.GeoDataFrame | None = None,
    stride: int = 12,
    vertical_exaggeration: float = 10.0,
    max_fault_points: int = 20_000,
) -> go.Figure:
    """Render 24 ordered horizons plus the cross-cutting intrusive surface.

    Z values remain true elevations; exaggeration changes only scene aspect.
    """
    path = Path(gdb_path or WSD_3D_MODEL["gdb_path"])
    catalog = horizon_catalog(path)
    figure = go.Figure()
    ex = {"xmin": np.inf, "xmax": -np.inf, "ymin": np.inf, "ymax": -np.inf,
          "zmin": np.inf, "zmax": -np.inf}
    for index, unit in catalog.iterrows():
        x, y, z = _surface(unit["layer"], max(1, stride), path)
        finite = z[np.isfinite(z)]
        if finite.size:
            ex["zmin"], ex["zmax"] = min(ex["zmin"], finite.min()), max(ex["zmax"], finite.max())
        ex["xmin"], ex["xmax"] = min(ex["xmin"], x.min()), max(ex["xmax"], x.max())
        ex["ymin"], ex["ymax"] = min(ex["ymin"], y.min()), max(ex["ymax"], y.max())
        figure.add_surface(
            x=x, y=y, z=z, name=unit["name"], showscale=False,
            opacity=0.55 if unit["cross_cutting"] else 0.82,
            visible=index < 8 or unit["cross_cutting"],
            hovertemplate=(f"x=%{{x:.0f}}<br>y=%{{y:.0f}}<br>"
                           f"modeled top elevation=%{{z:.0f}} m NAVD88<extra>{unit['name']}</extra>"),
        )
    if faults is not None and not faults.empty:
        sample = faults.iloc[::max(1, len(faults) // max_fault_points)].copy()
        if not {"x", "y", "z"}.issubset(sample.columns):
            raise ValueError("FaultPoints must contain native model x, y, and z coordinates")
        figure.add_scatter3d(
            x=pd.to_numeric(sample["x"], errors="coerce"),
            y=pd.to_numeric(sample["y"], errors="coerce"),
            z=pd.to_numeric(sample["z"], errors="coerce"),
            mode="markers", marker={"size": 1, "color": "#C0392B"},
            name="Fault elevation control points",
            hovertemplate="x=%{x:.0f}<br>y=%{y:.0f}<br>elevation=%{z:.0f} m NAVD88<extra>Fault control point</extra>",
        )
    if boundaries is not None and not boundaries.empty:
        outlines = boundaries.to_crs("EPSG:5070")
        reference_z = ex["zmax"] + max(25, (ex["zmax"] - ex["zmin"]) * 0.02)
        for _, row in outlines.iterrows():
            geometries = list(row.geometry.geoms) if row.geometry.geom_type == "MultiPolygon" else [row.geometry]
            for polygon in geometries:
                bx, by = polygon.exterior.xy
                figure.add_scatter3d(
                    x=np.asarray(bx), y=np.asarray(by), z=np.full(len(bx), reference_z), mode="lines",
                    line={"color": "#00E5FF", "width": 6},
                    name=str(row.get("common_name", "Tribal boundary")) + " (reference plane)",
                    showlegend=False,
                )
    x_range = ex["xmax"] - ex["xmin"]
    aspect = {"x": 1, "y": (ex["ymax"] - ex["ymin"]) / x_range,
              "z": max(0.02, (ex["zmax"] - ex["zmin"]) / x_range * vertical_exaggeration)}
    figure.update_layout(
        title="USGS Western South Dakota 3D Model — 24 ordered horizons + cross-cutting intrusive surface",
        scene={"aspectmode": "manual", "aspectratio": aspect,
               "xaxis_title": "Easting (m, NAD83 / CONUS Albers)",
               "yaxis_title": "Northing (m, NAD83 / CONUS Albers)",
               "zaxis_title": "Modeled top elevation (m NAVD88)"},
        legend={"itemsizing": "constant"}, margin={"l": 0, "r": 0, "t": 55, "b": 0},
    )
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(output_html, include_plotlyjs=True, full_html=True)
    return figure


def sample_cross_section(transect: LineString, n_points: int = 500,
                         gdb_path: Path | None = None) -> pd.DataFrame:
    """Sample ordered real horizon-top elevations along a WGS84 transect."""
    path = Path(gdb_path or WSD_3D_MODEL["gdb_path"])
    fractions = np.linspace(0, 1, n_points)
    points = [transect.interpolate(f, normalized=True) for f in fractions]
    result = pd.DataFrame({"longitude": [p.x for p in points],
                           "latitude": [p.y for p in points],
                           "distance_km": fractions * _geodesic_length_km(points)})
    catalog = horizon_catalog(path)
    transform = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)
    coords = [transform.transform(p.x, p.y) for p in points]
    for _, unit in catalog.iterrows():
        grid_x, grid_y, grid_z = _surface(unit["layer"], 1, path)
        cols = np.rint((np.array([c[0] for c in coords]) - grid_x[0]) / (grid_x[1] - grid_x[0])).astype(int)
        rows = np.rint((np.array([c[1] for c in coords]) - grid_y[0]) / (grid_y[1] - grid_y[0])).astype(int)
        values = np.full(len(coords), np.nan)
        valid = ((rows >= 0) & (rows < grid_z.shape[0]) & (cols >= 0) & (cols < grid_z.shape[1]))
        values[valid] = grid_z[rows[valid], cols[valid]]
        result[unit["name"]] = values
    return result


def _geodesic_length_km(points) -> float:
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    return sum(geod.inv(a.x, a.y, b.x, b.y)[2] for a, b in zip(points, points[1:])) / 1000
