# Data intake guide

## Public datasets

For every acquisition, record source URL or DOI, steward, retrieval timestamp,
source version/vintage, original filename, SHA-256 checksum, license/terms,
horizontal CRS, vertical datum, units, spatial extent, and expected layers.
Preserve source metadata alongside the data or in the release manifest.

Run `python -m scripts.check_release --json` after placing inputs. Presence is
only a structural check; scientific suitability still requires review.

## Governed records

Store governed workbooks only in `data/governed/` on an access-controlled OLC
system. Never upload them to GitHub. Use copies of the templates in
`Field data forms/`, replace example rows, and complete all governance fields.
The workflow denies records without an exact controlled purpose and valid date.

## Coordinate and unit conventions

- Latitude/longitude: decimal degrees, WGS 84, longitude negative west.
- Dates: ISO `YYYY-MM-DD`.
- Soil depth: centimeters.
- Well depth: feet in the current intake schema; record conversions explicitly.
- Strike/dip: use a documented right-hand-rule or quadrant convention.

Do not silently infer a CRS, datum, unit, missing value, or authorization.
