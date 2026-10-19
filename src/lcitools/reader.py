"""Read a Brightway2 CSV export (LCIS2024 layout) into tidy tables."""

import csv
from pathlib import Path

import pandas as pd

ACTIVITY_FIELDS = ["code", "comment", "location", "production amount",
                   "reference product", "unit", "worksheet name"]


def read_brightway_csv(path):
    """Parse a Brightway CSV export.

    Each activity is a block of ``key,value`` rows followed by an
    ``Exchanges`` table whose header can differ between activities
    (biosphere exchanges add a ``categories`` column).

    Returns (database_name, activities, exchanges) where activities has one
    row per activity and exchanges one row per exchange, with an
    ``activity`` column naming the activity that consumes or emits it.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    database = None
    activities, exchanges = [], []
    current, header = None, None

    for row in rows:
        if not row or not any(cell.strip() for cell in row):
            current, header = None, None
            continue
        key = row[0]
        if key == "Database":
            database = row[1]
        elif key == "Activity":
            current = {"name": row[1]}
            activities.append(current)
            header = None
        elif current is None:
            continue
        elif key == "Exchanges":
            header = "pending"
        elif header == "pending":
            header = row
        elif header is not None:
            exc = dict(zip(header, row))
            exc["activity"] = current["name"]
            exchanges.append(exc)
        elif key in ACTIVITY_FIELDS:
            current[key] = row[1]

    acts = pd.DataFrame(activities)
    acts["production amount"] = pd.to_numeric(acts["production amount"])

    excs = pd.DataFrame(exchanges)
    excs["amount"] = pd.to_numeric(excs["amount"])
    excs = excs.fillna("")
    cols = ["activity", "name", "amount", "unit", "type", "database",
            "location", "categories", "reference product", "Comment"]
    excs = excs[[c for c in cols if c in excs.columns]]
    return database, acts, excs


def read_properties(path):
    """Read the ``*_properties.csv`` file into a dict."""
    df = pd.read_csv(path)
    return dict(zip(df["Property"], df["Value"]))


def read_metadata(path):
    """Read the Metadata sheet of an LCIS2024 metadata workbook.

    Returns a dict keyed by "Section / Field" (e.g. "License / SPDX Identifier").
    """
    raw = pd.read_excel(path, sheet_name="Metadata", header=None,
                        usecols=[0, 1, 2])
    meta, section = {}, None
    for sec, field, value in raw.itertuples(index=False):
        if pd.notna(sec):
            section = str(sec).strip()
        if pd.isna(field):
            continue
        meta[f"{section} / {str(field).strip()}"] = (
            None if pd.isna(value) else value)
    return meta


def dataset_paths(root):
    """Locate the files of one dataset folder (e.g. data/original/power-to-liquid)."""
    root = Path(root)
    name = root.name
    return {
        "csv": root / "dataset" / f"{name}.csv",
        "properties": root / "dataset" / f"{name}_properties.csv",
        "metadata": root / "metadata" / "metadata.xlsx",
        "graphml": root / "network" / f"{name}.graphml",
    }
