from __future__ import annotations

"""
sovereignty.py Data governance acknowledgment for tribal_soils_geology.

Implements draft OCAP®, CARE, FAIR, and IEEE 2890-2025 framing for geological
and soils data describing Pine Ridge Reservation lands, pending OST/OLC review.

Subsurface governance note
The geology and soils of Pine Ridge are the material foundation of
Lakota sovereignty. The Arikaree aquifer, the Pierre Shale, the Badlands formations 
are the land itself. Federal geological surveys conducted on these territories produce 
data that describes Tribal resources. That data is subject to OCAP® principles: Tribal 
Nations retain the right to Ownership, Control, Access, and Possession of data about their 
lands, regardless of which agency collected it.

This module ensures every notebook in the series opens with this framing
and every data export includes provenance sufficient to trace the data back
to its source and its governance obligations.
"""

from src.constants import TREATY_PROVENANCE, GOVERNANCE_REFS, WSD_3D_MODEL

# Data source registry
_DATA_SOURCES: dict[str, dict] = {

    "usgs_3d_model": {
        "name":     "USGS 3D Geological Model of Western South Dakota",
        "citation": WSD_3D_MODEL["citation"],
        "url":      f"https://doi.org/{WSD_3D_MODEL['doi']}",
        "steward":  "US Geological Survey, Rocky Mountain Region",
        "license":  "CC0 1.0 Universal (Public Domain)",
        "note":     (
            "Subsurface horizon rasters and fault surfaces for western SD. "
            "25 stratigraphic units, 35 fault surfaces. "
            "Model uncertainty documented in accompanying README."
        ),
    },

    "usda_ssurgo": {
        "name":     "USDA NRCS SSURGO Soil Survey Geographic Database",
        "citation": (
            "Soil Survey Staff, Natural Resources Conservation Service, "
            "United States Department of Agriculture. Web Soil Survey. "
            "Available online at https://websoilsurvey.nrcs.usda.gov/."
        ),
        "url":      "https://websoilsurvey.nrcs.usda.gov/",
        "steward":  "USDA Natural Resources Conservation Service (NRCS)",
        "license":  "Public domain",
        "note":     (
            "SSURGO sampling density on Tribal lands is frequently lower than "
            "adjacent non-Tribal lands. Sparse sampling is a federal investment "
            "gap, not evidence of uniform soil conditions. "
            "Tribal-collected soil profiles fill this gap."
        ),
    },

    "usgs_state_geology": {
        "name":     "USGS Mineral Resources South Dakota State Geologic Map",
        "citation": (
            "US Geological Survey, Mineral Resources Online Spatial Data. "
            "State Geologic Map Compilation. "
            "https://mrdata.usgs.gov/geology/state/"
        ),
        "url":      "https://mrdata.usgs.gov/geology/state/",
        "steward":  "US Geological Survey",
        "license":  "Public domain",
        "note":     None,
    },

    "census_aiannh": {
        "name":     "US Census Bureau TIGER/Line AIANNH Boundaries",
        "citation": (
            "US Census Bureau. TIGER/Line Shapefiles: American Indian / "
            "Alaska Native / Native Hawaiian Areas (AIANNH). "
            "https://www.census.gov/geographies/mapping-files/time-series/"
            "geo/tiger-line-file.html"
        ),
        "url":      "https://www.census.gov/geographies/mapping-files/",
        "steward":  "US Census Bureau",
        "license":  "Public domain",
        "note":     (
            "Census-defined boundaries are for statistical purposes only. "
            "They do not represent legal jurisdiction or Tribal self-definition."
        ),
    },

    "usgs_nwis_wells": {
        "name":     "USGS NWIS Well Logs and Groundwater Data",
        "citation": (
            "U.S. Geological Survey, 2024, National Water Information System "
            "data available on the World Wide Web (USGS Water Data for the Nation). "
            "https://waterdata.usgs.gov/nwis/"
        ),
        "url":      "https://waterdata.usgs.gov/nwis/",
        "steward":  "US Geological Survey",
        "license":  "Public domain",
        "note":     (
            "A monitoring-gap conclusion requires a timestamped spatial query, "
            "an approved comparison geography, and documented evidence."
        ),
    },

    "usgs_landslide": {
        "name":     "USGS National Landslide Hazards Program",
        "citation": (
            "Jessee, M.A.N., and others, 2018, A global empirical model for "
            "near-real-time assessment of seismically induced landslides. "
            "Journal of Geophysical Research: Earth Surface."
        ),
        "url":      "https://www.usgs.gov/programs/landslide-hazards",
        "steward":  "US Geological Survey",
        "license":  "Public domain",
        "note":     None,
    },

    "tribal_soil_profiles": {
        "name":     "Tribal-Collected Soil Profile Data",
        "citation": (
            "Data collected by or in partnership with the Oglala Sioux Tribe "
            "or Oglala Lakota College. "
            "Governed by OCAP®: Tribal Nations retain ownership and control."
        ),
        "url":      "data/governed/ (local only, denied by Git)",
        "steward":  "Tribal Nation natural resource department",
        "license":  "Tribal: governed by OCAP®",
        "note":     (
            "This data is denied by Git and stays in governed local storage. "
            "It is never uploaded to GitHub or shared without explicit "
            "Tribal authorization. See docs/data_sovereignty.md."
        ),
    },

    "tribal_well_logs": {
        "name":     "Tribal-Collected Well Log Data",
        "citation": (
            "Data collected by or in partnership with the Oglala Sioux Tribe "
            "or Oglala Lakota College. "
            "Governed by OCAP®: Tribal Nations retain ownership and control."
        ),
        "url":      "data/governed/ (local only, denied by Git)",
        "steward":  "Tribal Nation natural resource department",
        "license":  "Tribal: governed by OCAP®",
        "note":     (
            "Tribal-collected well logs fill the USGS monitoring gap on "
            "reservation lands when collection and use are authorized. "
            "This data is denied by Git."
        ),
    },
}


def print_data_acknowledgment(source_keys: list[str] | None = None) -> None:
    """
    Print the full data governance acknowledgment for a notebook.
    Call at the top of every notebook after imports.
    """
    print("TRIBAL SOILS AND GEOLOGY DATA GOVERNANCE ACKNOWLEDGMENT")
    print()
    print(
        "This analysis uses data that describes the lands and subsurface\n"
        "resources of the Oglala Sioux Tribe and the Oglala Lakota people.\n"
        "peoples. This data is governed by the following frameworks:"
    )
    print()
    print("OCAP\u00ae  : Tribal Nations have the right to Ownership, Control,")
    print("         Access, and Possession of data about their lands,")
    print("         including subsurface geological and soil data.")
    print(f"         Reference: {GOVERNANCE_REFS['ocap']}")
    print()
    print("CARE   : Data use must deliver Collective Benefit to Indigenous")
    print("         peoples, respect their Authority to Control, uphold")
    print("         Responsibility to communities, and center Ethics.")
    print(f"         Reference: {GOVERNANCE_REFS['care']}")
    print()
    print("FAIR   : Data is Findable, Accessible, Interoperable, Reusable.")
    print("         FAIR governs technical standards; CARE and OCAP\u00ae govern")
    print("         the ethical obligations FAIR alone does not address.")
    print(f"         Reference: {GOVERNANCE_REFS['fair']}")
    print()
    print("IEEE 2890-2025 : Recommended Practice for Provenance of")
    print("         Indigenous Peoples' Data. First international standard")
    print("         for Indigenous data provenance.")
    print(f"         Reference: {GOVERNANCE_REFS['ieee_2890']}")
    print()
    print("TERRITORIAL PROVENANCE")
    print(f"  {TREATY_PROVENANCE['treaty_territory']}")
    print(f"  {TREATY_PROVENANCE['subsurface_note']}")
    print()

    if source_keys:
        print("DATA SOURCES USED IN THIS NOTEBOOK")
        for key in source_keys:
            src = _DATA_SOURCES.get(key)
            if not src:
                continue
            print(f"\n  {src['name']}")
            print(f"  Steward : {src['steward']}")
            print(f"  License : {src['license']}")
            if src.get("note"):
                print(f"  Note    : {src['note']}")
        print()


def generate_citations(source_keys: list[str]) -> str:
    """Return a plain-text citation block for notebook outputs."""
    lines = []
    lines.append("DATA CITATIONS")
    
    for key in source_keys:
        src = _DATA_SOURCES.get(key)
        if not src:
            continue
        lines.append(f"\n{src['name']}")
        if src.get("citation"):
            lines.append(f"  {src['citation']}")
        lines.append(f"  {src['url']}")
        lines.append(f"  Steward: {src['steward']} | License: {src['license']}")

    lines.append("\nTERRITORIAL PROVENANCE")
    lines.append(f"  {TREATY_PROVENANCE['treaty_territory']}")
    lines.append(f"  {TREATY_PROVENANCE['treaty_status']}")
    lines.append(f"  {TREATY_PROVENANCE['legal_citation']}")

    lines.append("\nGOVERNANCE FRAMEWORKS: OCAP\u00ae | CARE | FAIR | IEEE 2890-2025")
    for name, url in GOVERNANCE_REFS.items():
        lines.append(f"  {name.upper()}: {url}")

    return "\n".join(lines)


def attach_provenance(gdf, source_key: str) -> object:
    """
    Attach IEEE 2890-2025 provenance attributes to a GeoDataFrame.
    Adds columns: data_source, steward, license, treaty_territory.
    """
    src = _DATA_SOURCES.get(source_key, {})
    gdf = gdf.copy()
    gdf["data_source"]      = src.get("name", source_key)
    gdf["steward"]          = src.get("steward", "Unknown")
    gdf["license"]          = src.get("license", "Unknown")
    gdf["treaty_territory"] = TREATY_PROVENANCE["treaty_territory"]
    gdf["treaty_status"]    = TREATY_PROVENANCE["treaty_status"]
    gdf["legal_citation"]   = TREATY_PROVENANCE["legal_citation"]
    return gdf
