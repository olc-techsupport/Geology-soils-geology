# Scientific method and validation

The Stage 2 products are regional screening and instructional analyses. They do
not replace site investigation, engineering design, resource decisions, or
Nation-authorized interpretation of governed observations.

## Required checks

1. Confirm source identity, vintage, checksum, and license.
2. Validate geometry, CRS, vertical datum, units, nodata, and spatial extent.
3. Clip decision-level summaries to an explicitly approved geography; bounding
   boxes are acquisition/context extents only.
4. Report source resolution and effective analytical resolution. Resampling does
   not create new accuracy.
5. Preserve uncertainty, missingness, component mixtures, and depth coverage.
6. Validate derived surfaces against independent control observations where
   available and report sample size and error metrics.
7. Treat negative surface-minus-horizon differences as diagnostics, not automatic
   outcrop classifications.
8. Treat absent or unqueried records as unknown, not zero.

Claims about disparities or their causes require a saved evidence record with a
query date, endpoint, parameters, comparison geography, metric, result,
limitations, and authoritative citation.
