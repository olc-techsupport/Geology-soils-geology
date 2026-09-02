from __future__ import annotations

"""
constants.py Project-wide constants for tribal_soils_geology.

All values that change when adapting for a different Nation live in
config/config.yaml. Constants here are technically stable values:
CRS definitions, URL bases, field name standards, data source references,
and the 3D model metadata.

Data sovereignty note
This repository describes the subsurface geology and soils of lands
belonging to the Oglala Lakota and Sicangu Lakota peoples. Public federal
datasets (USGS, USDA) covering these territories do not transfer authority
over these lands or their resources to federal agencies or researchers.
All data use is governed by OCAP®, CARE, FAIR, and IEEE 2890-2025.
"""

from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[1]

# Coordinate reference systems
CRS_GEOGRAPHIC = "EPSG:4326"    # WGS84 lat/lon all spatial data
CRS_PROJECTED  = "EPSG:5070"    # Albers Equal Area CONUS area calculations
CRS_UTM14      = "EPSG:32614"   # UTM Zone 14N local precision (SD)
CRS_WEB        = "EPSG:3857"    # Web Mercator basemap tiles

# Data directories
CACHE_DIR     = REPO_ROOT/"data"/"cache"
RAW_DIR       = REPO_ROOT/"data"/"raw"
PROCESSED_DIR = REPO_ROOT/"data"/"processed"
GEOLOGY_DIR   = RAW_DIR/"geology"
SSURGO_DIR    = RAW_DIR/"ssurgo"
TEMPLATE_DIR  = REPO_ROOT/"Field data forms"
OUTPUTS_DIR   = REPO_ROOT/"outputs"
FIGURES_DIR   = OUTPUTS_DIR/"figures"

def ensure_project_directories() -> None:
    """Create runtime directories explicitly instead of during module import."""
    for directory in [CACHE_DIR, PROCESSED_DIR, GEOLOGY_DIR, SSURGO_DIR,
                      TEMPLATE_DIR, OUTPUTS_DIR, FIGURES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# Study area: Pine Ridge and Rosebud Reservations
# Bounding boxes (WGS84: min_lon, min_lat, max_lon, max_lat)
PINE_RIDGE_BBOX    = (-103.5, 42.5, -101.5, 43.8)
ROSEBUD_BBOX       = (-101.5, 42.8,  -99.8, 43.6)
COMBINED_BBOX      = (-103.5, 42.5,  -99.8, 43.8)  # both reservations
STUDY_BBOX         = (-104.5, 42.3, -99.0, 44.0)  # extended regional context

# Approximate centroids (WGS84)
PINE_RIDGE_CENTROID = (-102.5, 43.1)
ROSEBUD_CENTROID    = (-100.7, 43.2)

# Census TIGER Nation names
# Exact strings from the AIANNH shapefile NAME field
PRIMARY_NATIONS_CENSUS = ["Pine Ridge", "Rosebud"]
PRIMARY_NATIONS_COMMON = {
    "Pine Ridge": "Oglala Lakota",
    "Rosebud":    "Sicangu Lakota (Rosebud)",
}

OCETI_SAKOWIN_CENSUS_NAMES = [
    "Pine Ridge", "Rosebud", "Standing Rock", "Cheyenne River",
    "Lower Brule", "Crow Creek", "Lake Traverse", "Flandreau",
]

CENSUS_TO_COMMON = {
    "Pine Ridge":     "Oglala Lakota",
    "Rosebud":        "Sicangu Lakota (Rosebud)",
    "Standing Rock":  "Standing Rock Sioux",
    "Cheyenne River": "Cheyenne River Sioux",
    "Lower Brule":    "Lower Brule Sioux",
    "Crow Creek":     "Crow Creek Sioux",
    "Lake Traverse":  "Sisseton Wahpeton Oyate",
    "Flandreau":      "Flandreau Santee Sioux",
}

# API base URLs
CENSUS_TIGER_BASE  = "https://www2.census.gov/geo/tiger"
NHD_FLOWLINE_URL   = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/3/query"
WBD_HUC8_URL       = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/4/query"
USGS_NWIS_BASE     = "https://waterservices.usgs.gov/nwis"
USGS_NWIS_SITE_URL = f"{USGS_NWIS_BASE}/site/"
USGS_3DEP_URL      = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"

# USGS Landslide hazards REST service
USGS_LANDSLIDE_URL = (
    "https://maps.ngdc.noaa.gov/arcgis/rest/services/"
    "web_mercator/hazards/MapServer/0/query"
)

# USGS 3D Geological Model of western South Dakota
# Spangler 2024 ScienceBase doi:10.5066/P9LK4QHJ
# CC0 no restrictions on use
# Study area: west of Missouri River to Wyoming border (covers Pine Ridge and Rosebud)
WSD_3D_MODEL = {
    "sciencebase_id": "642c5a73d34ee8d4add22046",
    "doi":            "10.5066/P9LK4QHJ",
    "citation":       (
        "Spangler, L.R., 2024, Digital data for a 3D Geological Model of "
        "western South Dakota, USA: U.S. Geological Survey data release, "
        "https://doi.org/10.5066/P9LK4QHJ."
    ),
    "license":        "CC0 1.0 Universal (Public Domain)",
    "wms_url":        (
        "https://www.sciencebase.gov/catalogMaps/mapping/ows/"
        "642c5a73d34ee8d4add22046"
        "?service=wms&request=getcapabilities&version=1.3.0"
    ),
    # Local paths: files placed in data/raw/geology/ after manual download
    "gdb_path":        GEOLOGY_DIR/"WSouthDakota3D.gdb",
    "shapefiles_path": GEOLOGY_DIR/"Shapefiles",
    "tables_path":     GEOLOGY_DIR/"NonspatialTables",
    "n_horizons":      25,
    "n_faults":        35,
    "crs":             "EPSG:4269",   # NAD83 geographic is used in the GDB
}

# Stratigraphic units modeled in the 3D model (top to bottom, approximate)
# Sources: WSD_NonspatialTables/DescriptionOfModelUnits
WSD_STRATIGRAPHY = [
    "Glacial sediments",
    "Ogallala Group",          # Arikaree aquifer 
    "Hell Creek Formation",
    "Lance Formation",
    "Fox Hills Formation",
    "Pierre Shale",            # thick, expansive controls slope stability
    "Niobrara Formation",
    "Carlile Shale",
    "Greenhorn Formation",
    "Mowry Shale",
    "Belle Fourche Shale",
    "Morrison Formation",
    "Sundance Formation",
    "Inyan Kara Group",
    "Minnelusa Formation",
    "Minnekahta Formation",
    "Spearfish Formation",
    "Three Forks Shale",
    "Madison Group",           # deep confined aquifer
    "Deadwood Formation",
    "Precambrian basement",
]

# Units of particular significance for land and water management
WSD_KEY_UNITS = {
    "pre-Ogallala":      "Aggregated model unit that includes the Arikaree Group; not a formation-specific aquifer surface",
    "Pierre Shale":      "Expansive clay controls slope instability, swelling soils",
    "Hell Creek Formation": "Near-surface on eastern portion paleontological resources",
    "Madison Group":     "Deep confined aquifer artesian potential in parts of study area",
    "Niobrara Formation": "Fractured chalk secondary aquifer in some areas",
}

# SSURGO field name standards
# Must match the ESRI Soil Data Downloader output schema
SSURGO_MAP_UNIT_FIELDS = [
    "mukey", "musym", "muname", "mukind", "mustatus",
    "slopegraddcp", "slopegradwta", "brockdepmin", "wtdepannmin",
    "wtdepaprjunmin", "flodfreqdcd", "pondfreqprs",
    "drainagecl", "hydgrpdcd", "corcon", "corsteel",
    "taxclname", "taxorder", "taxsuborder", "taxgrtgroup",
    "taxsubgrp", "taxpartsize", "farmlndcl", "k factor",
]

SSURGO_HORIZON_FIELDS = [
    "cokey", "chkey", "hzname", "hzdept_r", "hzdepb_r",
    "sandtotal_r", "silttotal_r", "claytotal_r",
    "om_r", "ph1to1h2o_r", "cec7_r", "ecec_r",
    "ksat_r", "awc_r", "dbthirdbar_r", "lep_r",
    "texture", "texdesc",
]

# Intake template field standards
SOIL_PROFILE_FIELDS = [
    "profile_id", "date", "observer", "lat", "lon",
    "horizon", "depth_top_cm", "depth_bottom_cm",
    "texture", "color_moist", "color_dry",
    "structure", "consistence", "roots", "ph",
    "notes", "data_authority", "access_level", "authorized_use",
    "authorization_date",
]

WELL_LOG_FIELDS = [
    "well_id", "date", "observer", "lat", "lon",
    "total_depth_ft", "casing_depth_ft", "water_depth_ft",
    "unit_top_ft", "unit_bottom_ft", "lithology",
    "color", "grain_size", "notes",
]

FIELD_OBSERVATION_FIELDS = [
    "obs_id", "date", "observer", "lat", "lon",
    "formation", "rock_type", "structure",
    "strike", "dip", "notes", "photo_ids",
]

# Data sovereignty
TREATY_PROVENANCE = {
    "treaty_territory": (
        "1868 Fort Laramie Treaty Oceti Sakowin territory, "
        "including the Great Sioux Reservation"
    ),
    "treaty_status": (
        "The lands of Pine Ridge and Rosebud Reservations are the sovereign "
        "territory of the Oglala Lakota and Sicangu Lakota peoples respectively. "
        "Federal and state geological surveys conducted on these lands do not "
        "transfer authority over subsurface resources to federal agencies."
    ),
    "legal_citation": (
        "United States v. Sioux Nation of Indians, 448 U.S. 371 (1980). "
        "The Sioux Nations have declined financial compensation, maintaining "
        "that the land was never legally transferred."
    ),
    "subsurface_note": (
        "Subsurface geological data (including aquifer characterization, "
        "formation mapping, and soil surveys) describing Tribal lands is "
        "subject to OCAP® principles. Data ownership and stewardship rights "
        "belong to the relevant Tribal Nations."
    ),
}

GOVERNANCE_REFS = {
    "ocap":          "https://fnigc.ca/ocap-training/",
    "care":          "https://www.gida-global.org/care",
    "fair":          "https://www.go-fair.org/fair-principles/",
    "ieee_2890":     "https://standards.ieee.org/ieee/2890/10318/",
    "local_contexts":"https://localcontexts.org/",
}
