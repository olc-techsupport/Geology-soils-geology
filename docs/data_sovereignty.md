# Data governance operating guide

> Status: technical operating draft. Substantive sovereignty and governance
> language is pending review by OST/OLC-designated colleagues.

## Storage classes

- `data/public/` or the legacy `data/raw/geology` and `data/raw/ssurgo` paths:
  redistributable or reacquirable public source data, subject to source terms.
- `data/governed/`: Nation- or OLC-controlled records. Git denies this directory
  by default and code must apply an authorization gate before use.
- `data/processed/`: generated intermediate products. A workflow must not place
  governed derivatives here unless the directory is protected equivalently.
- `outputs/`: publication candidates, not automatically approved releases.

## Minimum governed-record metadata

Every governed record must identify the authorized body (`data_authority`),
access class, controlled purpose identifier, and authorization date. Supported
purpose identifiers are `soils-analysis`, `aquifer-geology`,
`geologic-hazards`, and `education`. Missing or malformed metadata denies use.

An authorization gate is not publication approval. Before sharing any derived
artifact, confirm aggregation, location precision, audience, permitted purpose,
attribution, retention, withdrawal, and review requirements with the designated
authority.

## Incident response

If governed material is committed, stop distribution, notify the designated
OLC/OST contact, preserve an access-controlled incident record, remove the data
from the working tree and Git history, rotate any exposed credentials, and
document who may retain or destroy prior copies. Do not paste sensitive values
into public issues or commit messages.
