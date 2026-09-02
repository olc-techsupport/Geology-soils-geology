# OLC operator guide

## Supported baseline

- Windows 10/11 or current Linux
- Miniforge/Conda with 64-bit Python 3.11
- At least 10 GB free space for environment, public inputs, caches, and outputs
- Internet access for initial environment creation and optional public refreshes

From PowerShell:

```powershell
conda env create --file environment.yml
conda activate tribal-soils-geology
python -m pip install --no-deps --editable .
python -m scripts.check_release
python -m pytest
jupyter lab Notebooks
```

Run notebooks 01 through 09 in order. Public API refreshes are deliberately off
by default where a failed query could otherwise be confused with absent data.
Enable them only for a recorded refresh.

If GDAL/FileGDB errors occur, confirm that the Conda environment is activated,
`python` resolves inside it, and `GDAL_DATA` is populated by Conda. Do not use an
unrelated system Python.

For an offline demonstration, use previously verified public inputs. Governed
records remain optional and their absence is a valid, non-error outcome.
