"""Idempotently replace exploratory notebook cells with shared tested workflows."""
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def replace_cell(notebook, marker, source, cell_type="code"):
    matches = [index for index, cell in enumerate(notebook.cells) if marker in cell.source]
    if not matches:
        if any(cell.source == source for cell in notebook.cells):
            return
        raise RuntimeError(f"Notebook marker not found: {marker}")
    new_cell = nbformat.v4.new_code_cell(source) if cell_type == "code" else nbformat.v4.new_markdown_cell(source)
    notebook.cells[matches[0]] = new_cell


def update_soils():
    path = ROOT/"Notebooks"/"05_soil_survey_ssurgo.ipynb"
    notebook = nbformat.read(path, as_version=4)
    replace_cell(notebook, "# Validate candidate survey symbols", '''# Validate candidate survey symbols against the authoritative live catalog.
from src.ssurgo import survey_status
from src.ssurgo import SDAError
from src.loaders import ssurgo_inventory

candidates = sorted({
    symbol
    for group in CONFIG["ssurgo_areasymbol"].values()
    for symbol in group
})
print("Local soil-data inventory:")
display(ssurgo_inventory())
print("\nCurrent public SDA catalog status (absence does not establish causation):")
try:
    catalog_status = survey_status(candidates)
    display(catalog_status)
except SDAError as exc:
    catalog_status = pd.DataFrame()
    print(f"Live catalog unavailable: {exc}")
    print("No availability or causation inference is made from a failed request.")
''')
    for marker in [
        "Previous attempts to download NRCS soils", "def get_ssurgo_wfs",
        "Try all known SDA endpoint variations", "df_sd = sda_query",
        "Test 3: WSS survey info", "# Print findings",
    ]:
        replace_cell(notebook, marker,
            "Exploratory endpoint tests were replaced by the tested functions in `src.ssurgo`. "
            "A survey reported as `not_listed` is an observed catalog status, not evidence of its cause.",
            "markdown")
    nbformat.write(notebook, path)


def update_geology():
    path = ROOT/"Notebooks"/"04_3d_geologic_model.ipynb"
    notebook = nbformat.read(path, as_version=4)
    replace_cell(notebook, "# Build a full-extent interactive model", '''# Build a scientifically ordered full-extent model from all WSD_Top* rasters.
from src.geology3d import build_interactive_model, horizon_catalog

interactive_path = OUTPUTS_DIR/"04_full_3d_geology_model.html"
catalog_3d = horizon_catalog(gdb_path)
print(f"Rendering {len(catalog_3d)} model-top rasters in published geological order")
display(catalog_3d)
model_figure = build_interactive_model(
    interactive_path,
    faults=faults,
    boundaries=primary,
    stride=CONFIG["analysis"]["model_3d_stride"],
    vertical_exaggeration=CONFIG["analysis"]["vertical_exaggeration"],
)
print(f"Standalone interactive model: {interactive_path}")
model_figure.show()
''')
    replace_cell(notebook, "# List all layers in the GDB", '''# FileGDB inventories use different GDAL APIs for vector/table and raster content.
import fiona
from src.geology3d import horizon_catalog

vector_table_layers = sorted(fiona.listlayers(str(gdb_path)))
model_tops = horizon_catalog(gdb_path)
print(f"Vector/table layers exposed by Fiona ({len(vector_table_layers)}):")
for layer in vector_table_layers:
    print(f"  {layer}")
print(f"\nRaster model-top subdatasets exposed by Rasterio ({len(model_tops)}):")
display(model_tops[["hierarchy_key", "name", "age", "layer", "cross_cutting"]])
print("\nThe intrusive surface is cross-cutting; it is not a stratigraphic interval boundary.")
''')
    replace_cell(notebook, "# Real west-east cross-section", '''# Real west-east cross-section sampled from every available horizon raster.
from shapely.geometry import LineString
from src.geology3d import sample_cross_section

transect = LineString([(-103.45, 43.15), (-101.55, 43.15)])
cross_section = sample_cross_section(transect, n_points=500, gdb_path=gdb_path)
horizon_columns = [c for c in cross_section.columns
                   if c not in {"longitude", "latitude", "distance_km"}]

fig, ax = plt.subplots(figsize=(15, 8))
for column in horizon_columns:
    ax.plot(cross_section["distance_km"], cross_section[column], linewidth=1, label=column)
ax.set_xlabel("Distance along transect (km, west to east)")
ax.set_ylabel("Modeled horizon elevation (m)")
ax.set_title("Pine Ridge cross-section sampled from Spangler (2024) horizon rasters")
ax.legend(fontsize=6, ncol=3, loc="upper left", bbox_to_anchor=(1.01, 1))
ax.grid(alpha=.2)
plt.tight_layout()
cross_section.to_csv(OUTPUTS_DIR/"04_pine_ridge_cross_section.csv", index=False)
fig.savefig(FIGURES_DIR/"04_cross_section_real.png", dpi=150, bbox_inches="tight")
plt.show()
''')
    replace_cell(notebook, "# Cross-section plotting framework",
        "The former synthetic cross-section demonstration was removed. The preceding cell now samples and plots all available model horizons directly.",
        "markdown")
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        original = cell.source
        cell.source = cell.source.replace(
            "% negative (above surface / outcrop)",
            "% negative (horizon above DEM; inspect datum, resolution, and model uncertainty)",
        ).replace(
            "% negative (above surface/outcrop)",
            "% negative (horizon above DEM; not automatically outcrop)",
        ).replace(
            "Negative = formation would be above the surface (outcrop/model edge artifact)",
            "Negative = modeled top exceeds DEM; may reflect exposure, datum/grid mismatch, or model uncertainty",
        ).replace(
            "# Show locations where the Pierre outcrops",
            "# Diagnose cells where the modeled Pierre top is at or above the DEM",
        ).replace(
            "# Two-tone: outcrop (negative) in one colormap, buried (positive) in another",
            "# Negative differences are diagnostic mismatches, not an outcrop classification by themselves",
        ).replace(
            '"Gray = outcrop / eroded to surface | Color = depth where buried"',
            '"Gray = modeled top at/above DEM (diagnostic) | Color = positive DEM-minus-horizon difference"',
        ).replace(
            "outcrop_mask", "nonphysical_mask",
        ).replace(
            "outcrop_plot", "nonphysical_plot",
        ).replace(
            '04_depth_to_pierre_shale_outcrop.png', '04_depth_to_pierre_shale_diagnostic.png',
        )
        if cell.source != original:
            cell.outputs = []
            cell.execution_count = None
        stale_output = str(cell.get("outputs", []))
        if ("above surface / outcrop" in stale_output or
                "above surface/outcrop" in stale_output):
            cell.outputs = []
            cell.execution_count = None
    nbformat.write(notebook, path)


def update_hazards():
    path = ROOT/"Notebooks"/"07_geologic_hazards.ipynb"
    notebook = nbformat.read(path, as_version=4)
    replace_cell(notebook, "# Optional public landslide layer", '''# The former HAZUS GeoServer endpoint is not a reproducible notebook input.
# Keep the analysis deterministic and use locally validated SSURGO slope plus
# the Notebook 04 depth-to-Pierre product for a documented proxy.
landslides = gpd.GeoDataFrame()
print("Remote landslide service disabled for reproducibility.")
print("Use validated SSURGO slope and the Notebook 04 depth-to-Pierre artifact.")
''')
    replace_cell(notebook, "PIERRE_SHALE_UNIT =", '''# Depth-to-Pierre is computed once in Notebook 04 from a surface DEM minus
# the modeled horizon. Reuse that derived artifact here instead of reopening
# the large FileGDB raster in a second notebook kernel.
pierre_depth_figure = FIGURES_DIR/"04_depth_to_pierre_shale.png"
print("Depth-to-Pierre artifact:", pierre_depth_figure)
print("Available:", pierre_depth_figure.exists())
''')
    nbformat.write(notebook, path)


def update_aquifer():
    path = ROOT/"Notebooks"/"08_aquifer_geology.ipynb"
    notebook = nbformat.read(path, as_version=4)
    notebook.metadata["kernelspec"] = {
        "display_name": "tribal-soils-geology",
        "language": "python",
        "name": "tribal-soils-geology",
    }
    replace_cell(notebook, "import fiona",
        "Model-layer inventory is maintained in Notebook 04. This notebook opens only the three aquifer-relevant rasters to avoid repeatedly mixing FileGDB vector and raster drivers in one Windows kernel.",
        "markdown")
    replace_cell(notebook, 'print("Loading USGS groundwater well sites', '''# Live NWIS access is optional so the geology workflow is reproducible offline.
# Set this to True only when you intentionally want to refresh the public-well
# inventory; a failed or empty query is not evidence about the cause of a gap.
RUN_LIVE_WELL_QUERY = False

if RUN_LIVE_WELL_QUERY:
    from src.loaders import load_usgs_well_sites
    print("Refreshing the public USGS groundwater-site inventory...")
    wells_pr = load_usgs_well_sites(PINE_RIDGE_BBOX)
    wells_rb = load_usgs_well_sites(ROSEBUD_BBOX)
    print(f"Pine Ridge bounding-box sites: {len(wells_pr)}")
    print(f"Rosebud bounding-box sites: {len(wells_rb)}")
    print("These are bounding-box inventory counts, not a causal monitoring-equity analysis.")
else:
    wells_pr = gpd.GeoDataFrame()
    wells_rb = gpd.GeoDataFrame()
    print("Live NWIS query skipped (RUN_LIVE_WELL_QUERY=False).")
    print("No claim about current well coverage is made in this run.")
''')
    replace_cell(notebook, "# Well coverage map", '''# Map only a deliberately refreshed inventory; never imply that an unrun query
# or a network failure represents zero monitoring sites.
if not RUN_LIVE_WELL_QUERY:
    print("Well map skipped because the live public inventory was not refreshed.")
elif wells_pr.empty and wells_rb.empty:
    print("No mappable records were returned; no coverage inference is made.")
else:
    fig, ax = plt.subplots(figsize=(12, 9))
    primary.to_crs(CRS_WEB).plot(
        ax=ax, facecolor=TEAL_LT, edgecolor=TEAL,
        linewidth=2, alpha=0.3, zorder=2,
    )
    for wells, label, color in [
        (wells_pr, "Pine Ridge query", "#2166AC"),
        (wells_rb, "Rosebud query", "#B2182B"),
    ]:
        if not wells.empty:
            wells.to_crs(CRS_WEB).plot(ax=ax, color=color, markersize=18, label=label, zorder=3)
    ax.set_title("Public USGS groundwater sites returned by this deliberate refresh")
    ax.legend()
    ax.set_axis_off()
    plt.show()
''')
    replace_cell(notebook, "AQUIFER_UNITS =", '''from src.loaders import load_wsd_horizon_raster, resolve_wsd_horizon_layer

# The regional model aggregates the Arikaree Group within "pre-Ogallala";
# it does not provide a formation-specific Arikaree aquifer top.
AQUIFER_UNITS = {
    "pre-Ogallala": (
        "Aggregated unit includes Arikaree Group; use as regional context only, "
        "not as an Arikaree-specific aquifer surface"
    ),
    "Niobrara Formation": "Secondary aquifer in locally fractured chalk",
    "Madison Group": "Deep confined carbonate aquifer system",
}

print("AQUIFER UNIT STATUS — USGS 3D MODEL")
for unit, description in AQUIFER_UNITS.items():
    layer = resolve_wsd_horizon_layer(unit)
    ds = load_wsd_horizon_raster(unit)
    print()
    print(f"{unit} -> {layer}")
    print(f"  {description}")
    if ds is None:
        print("  Raster unavailable; see the preceding warning for the specific cause.")
        continue
    with ds:
        data = ds.read(1, masked=True)
        print(f"  Modeled top elevation: {data.min():.1f} to {data.max():.1f} m NAVD88")
        print(f"  Grid size: {data.shape[0]} x {data.shape[1]}")
''')
    nbformat.write(notebook, path)


if __name__ == "__main__":
    update_soils()
    update_geology()
    update_hazards()
    update_aquifer()
