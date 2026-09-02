# Tribal Soils and Geology

> **Stage 2 release candidate.** Technical hardening is in progress. Data
> sovereignty and governance language is a draft pending OST/OLC review. Do not
> treat repository availability as publication approval for governed records or
> derived products.

Developed by: Lilly Jones, PhD, Daear Consulting LLC                                                                               
Developed for: Oglala Lakota College                                                                                            
Funding: This material was developed as part of a project funded by the USDA National Institute of Food and Agriculture (NIFA). The award number, official project title, and required agency disclaimer must be confirmed by OLC before a tagged public release.
Project role: Daear Consulting LLC developed the geospatial code, workflows, documentation, and instructional materials under contract to Oglala Lakota College.                                                                                                                      

License: Apache License 2.0 for original code. Rights for documentation,
templates, curriculum, generated products, and third-party data are described
in `THIRD_PARTY_DATA.md`; OLC review of non-code materials is pending.

## Data Sovereignty and Governance (draft under review)
This repository contains workflows developed for use in support of Oglala Lakota College and Oglala Sioux Tribe–related research, education, and data activities. Public availability of code or documentation does not imply that Tribal data, knowledge, or derived information are open or unrestricted. Use of Tribal data and knowledge remains subject to applicable Tribal governance, permissions, protocols, and data sovereignty requirements.                                                                               

## Overview

This repository provides a modular, reproducible geoscience analysis series
for Pine Ridge and Rosebud Reservations, grounded in Tribal data sovereignty
frameworks. It acquires and visualizes publicly available soils and geology
data, and provides intake frameworks for Tribal-collected field data.

The series is designed for use by PhD geologists, geological engineers, soil
scientists, and Tribal resource managers. Visualizations are accessible to
community members and Tribal decision makers after scientific and governance review.

## Notebook Series

| Notebook | Topic |
|---|---|
| 01 | Territorial and Geologic Context |
| 02 | Surficial Geology |
| 03 | Bedrock Geology |
| 04 | 3D Geologic Model (Spangler 2024) |
| 05 | Soil Survey SSURGO |
| 06 | Soil Profiles and Horizons |
| 07 | Geologic Hazards |
| 08 | Aquifer Geology |
| 09 | Data Gaps and Sovereignty |

## 3D Model

**USGS 3D Geological Model of Western South Dakota**
Spangler, L.R., 2024. DOI: [10.5066/P9LK4QHJ](https://doi.org/10.5066/P9LK4QHJ)

A regional-scale volumetric 3D geologic model covering all of western South
Dakota including Pine Ridge and Rosebud entirely. Contains 25 subsurface
horizon rasters and 35 fault surfaces. Licensed CC0 (public domain).
The stratigraphic column includes the Ogallala Group (Arikaree aquifer),
Pierre Shale, Hell Creek Formation, Madison Group, and 20 additional units.

This dataset has never been visualized in a Tribal land sovereignty context.
Notebook 04 provides depth-to-formation maps and fault visualization. The
reproducible full-model builder in `scripts/build_3d_model.py` renders every
available model-top raster as an interactive, toggleable surface and samples a
real Pine Ridge cross-section from those rasters. The viewer orders 24
stratigraphic surfaces using the published `HierarchyKey`; the Tertiary
intrusive surface is shown separately because it cross-cuts the sequence.

## Data Sources

### Public source data

| Source | What | Notebooks |
|---|---|---|
| USGS ScienceBase | 3D Geologic Model (Spangler 2024) | 04 |
| USGS mrdata.usgs.gov | South Dakota state geologic map | 02, 03 |
| USDA SSURGO | Soil map units, components, horizons | 05, 06 |
| USGS NWIS | Well logs, groundwater sites | 08 |
| USGS National Map | Elevation (3DEP) | 01 |
| Census TIGER AIANNH | Tribal boundaries | All |
| USGS NHD | Stream network | 01 |

### Tribal-collected data (sensitive data: gitignored)

Field data collected by or in partnership with Tribal natural resource
departments lives in the local-only `data/governed/` directory and is denied by
Git. Legacy `data/raw/soil_profiles.*`, `well_logs.*`, and field-observation
paths are also ignored during migration. See `docs/data_sovereignty.md`.

| Template | What |
|---|---|
| `soil_profile_template.xlsx` | Horizon-by-horizon field soil profiles |
| `well_log_template.xlsx` | Lithologic well logs |
| `field_observation_template.xlsx` | Geologic field notes and measurements |

## Setup

The supported baseline is a 64-bit Conda environment with Python 3.11. Budget at
least 10 GB of free disk space for the environment, public inputs, caches, and
outputs. See `docs/olc_operator_guide.md` for Windows, Linux, offline use, and
troubleshooting.

### 1. Download required datasets

**3D Geologic Model** (242 MB GDB required for notebook 04):
1. Go to https://doi.org/10.5066/P9LK4QHJ
2. Download `WSouthDakota3D.gdb.zip` and `WSD_NonspatialTables.zip`
3. Extract to `data/raw/geology/`

**SSURGO soil data** (required for notebooks 05–06):
1. Validate candidate survey symbols in `config/config.yaml` against the live
   SDA `sacatalog` using `src.ssurgo.survey_status`.
2. Download the validated surveys from Web Soil Survey or Soil Data Access.
3. Extract each survey below `data/raw/ssurgo/`. Nested directories are
   supported; the loader recursively discovers `.gdb` directories.
4. Do not use `.ppkx` ArcGIS project packages as SSURGO inputs. They can contain
   map projects and watershed products but are not soil geodatabases.

Survey symbols must not be inferred from county FIPS codes. Catalog names and
availability are validated at run time because soil-survey geography and county
geography are not interchangeable.

Notebooks 05–07 enforce an evidence boundary: Notebook 05 audits public
availability and geographic coverage, Notebook 06 accepts only explicitly
authorized Tribal-controlled profiles, and Notebook 07 suppresses soil-hazard
outputs wherever verified soil coverage or authorized observations are absent.
Adjacent-county surveys may be shown as regional context but never substitute
for Oglala Lakota soils.

**South Dakota state geology** (required for notebooks 02–03):
1. Go to https://mrdata.usgs.gov/geology/state/
2. Download South Dakota state geologic map GDB
3. Place in `data/raw/geology/`

### 2. Create and activate the conda environment

```bash
conda env create -f environment.yml
conda activate tribal-soils-geology

python -m pip install --no-deps --editable .
python -m scripts.check_release
python -m pytest

python -m ipykernel install --user --name tribal-soils-geology \
    --display-name "Python (tribal-soils-geology)"

jupyter lab Notebooks/
```

Run notebooks 01 through 09 in order. A skipped public API refresh is reported
as `not_checked_this_run`; it is never interpreted as zero records. Generated
files are publication candidates and require review before distribution.

## Data Sovereignty

This repository implements the following frameworks:

- **OCAP®**: Ownership, Control, Access, Possession
  https://fnigc.ca/ocap-training/
- **CARE Principles**: Collective Benefit, Authority to Control, Responsibility, Ethics
  https://www.gida-global.org/care
- **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
  https://www.go-fair.org/fair-principles/
- **IEEE 2890-2025**: Recommended Practice for Provenance of Indigenous Peoples' Data
  https://standards.ieee.org/ieee/2890/10318/

Federal geological surveys and soil surveys conducted on Pine Ridge and Rosebud
describe the subsurface resources of sovereign Tribal territories. Public data
covering these lands does not transfer authority to federal agencies or
researchers. Tribal-collected field data is governed by OCAP® and is never
committed to version control.

Earlier exploratory queries did not find a public SDA catalog record for the
candidate symbol SD102. That observation does **not** establish why a record is
absent, whether the symbol is correct, or whether a Tribal Nation requested a
restriction. Endpoint failures, survey-history differences, catalog changes,
and access policy must be investigated separately. The project therefore
reports the machine-observed status as `not_listed`, preserves response
metadata, and treats causation as unknown unless it is confirmed through
authoritative documentation or direct Nation-to-Nation consultation. No
absence is characterized as a Tribal data-sovereignty decision without that
evidence.

### Build the interactive 3D model

```bash
conda activate tribal-soils-geology
python scripts/build_3d_model.py
```

This creates `outputs/04_full_3d_geology_model.html` and a CSV containing a
cross-section sampled from the real model horizons. The HTML is standalone and
supports rotation, zooming, hover inspection, and per-formation visibility.
Displayed Z coordinates remain the published model elevations. Vertical
exaggeration changes only the scene aspect ratio, and Tribal outlines are
identified as a reference plane rather than terrain-draped boundaries.

The 3D model is regional screening context. Resampling does not increase the
source model's accuracy. Verify horizontal CRS, vertical datum, units, nodata,
effective resolution, and independent controls before decision use; see
`docs/scientific_method.md`.

## Adapting for Another Nation

1. Obtain approval from the relevant Nation/organization for governance text,
   names, geography, inputs, and permitted outputs.
2. Update `config/config.yaml` and the current Census-name mapping in
   `src/constants.py`.
3. Validate SSURGO survey identifiers against SDA; do not infer them from county
   codes.
4. Acquire and checksum source data, run `python -m scripts.check_release`, then
   run tests and notebooks in order.

Adaptation is not fully automatic: scientific assumptions, jurisdictional
geography, source fitness, governance, citations, and publication rules require
local review.

## Reproducibility, citation, and contribution

- `CITATION.cff`: preferred software citation metadata.
- `THIRD_PARTY_DATA.md`: rights and attribution boundaries.
- `docs/data_intake_guide.md`: acquisition metadata and governed intake.
- `docs/scientific_method.md`: validation and evidence requirements.
- `CONTRIBUTING.md`: review and testing expectations.
- `CHANGELOG.md`: release history.

## Connections to Related Repositories

- **tribal_water_monitoring** Notebook 08 (Aquifer Geology) provides the
  subsurface context for the Arikaree aquifer analysis in that series
- **he_sapa_mining_twin** The Black Hills uplift that structures He Sapa
  also controls the regional dip of formations across Pine Ridge
- **tribal_agricultural_science** Soils data from this series feeds
  land capability and erosion analysis in the agriculture series

