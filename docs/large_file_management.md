# Large-file and generated-artifact policy

Ordinary Git stores source code, configuration, notebooks, tests, templates,
documentation, and small fixtures. It does not store public raw geodatabases,
ArcGIS project packages, caches, or generated outputs.

Acquire public inputs from the sources in `data/PUBLIC_DATA_MANIFEST.yaml`, then
record retrieval metadata and checksums. Reviewed publication artifacts should
be attached to a tagged release or deposited in an approved repository with a
persistent identifier, rather than committed as routine build output.

The current Git history contains legacy large blobs, including an approximately
213 MB fault-point table and a historical notebook cache. History cleanup must
be planned with the repository owner because it changes commit identifiers and
requires every clone to rebase or reclone. Until that coordinated operation,
new commits and CI prevent reintroducing the files.
