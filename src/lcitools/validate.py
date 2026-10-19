"""Consistency checks for a published LCI dataset.

Each check returns a list of Finding(level, check, message). "error" means
the dataset is structurally inconsistent; "warning" means it loads but
something should be reviewed before reuse.
"""

from dataclasses import dataclass

# Metadata fields the LCIS2024 schema treats as essential for reuse.
REQUIRED_METADATA = [
    "Dataset / Name", "Dataset / Description", "Dataset / Functional Units",
    "Dataset / System boundary", "Dataset / LCI Model",
    "Authors / Name", "Background / Name", "Background / Version",
    "License / SPDX Identifier",
]

MOJIBAKE = ("Ã", "Â", "â€")


@dataclass
class Finding:
    level: str
    check: str
    message: str


def check_counts(database, activities, exchanges, properties):
    """Compare parsed contents against the counts declared in the properties file."""
    out = []
    declared = {
        "Dataset Name": database,
        "Total Activities": len(activities),
        "Total Exchanges": len(exchanges),
        "Total Biosphere flows": int((exchanges["type"] == "biosphere").sum()),
        "Total Technosphere flows": int((exchanges["type"] == "technosphere").sum()),
        "Total Reference products": int(activities["reference product"].nunique()),
    }
    for key, found in declared.items():
        expected = properties.get(key)
        if expected is None:
            continue
        if str(expected) != str(found):
            out.append(Finding("error", "counts",
                               f"{key}: properties file says {expected}, dataset has {found}"))
    return out


def check_production(activities, exchanges):
    """Each activity needs exactly one production exchange equal to its production amount."""
    out = []
    prod = exchanges[exchanges["type"] == "production"]
    for name, amount in zip(activities["name"], activities["production amount"]):
        rows = prod[prod["activity"] == name]
        if len(rows) != 1:
            out.append(Finding("error", "production",
                               f"'{name}' has {len(rows)} production exchanges"))
        elif rows["amount"].iloc[0] != amount:
            out.append(Finding("error", "production",
                               f"'{name}': production exchange {rows['amount'].iloc[0]} "
                               f"!= production amount {amount}"))
    return out


def check_links(database, activities, exchanges):
    """Technosphere inputs labelled with the foreground database must exist in it."""
    out = []
    foreground = set(activities["name"])
    tech = exchanges[exchanges["type"] == "technosphere"]
    dangling = tech[(tech["database"] == database) & ~tech["name"].isin(foreground)]
    for act, rows in dangling.groupby("activity"):
        out.append(Finding(
            "warning", "links",
            f"'{act}': {len(rows)} input(s) labelled database '{database}' but not "
            f"defined in it (likely background flows, e.g. '{rows['name'].iloc[0]}')"))
    return out


def check_amounts(exchanges):
    """Flag non-positive amounts, which usually indicate a sign or entry error."""
    bad = exchanges[exchanges["amount"] <= 0]
    return [Finding("warning", "amounts",
                    f"'{r.activity}' -> '{r.name}': amount {r.amount}")
            for r in bad.itertuples(index=False)]


def check_encoding(activities):
    """Detect UTF-8 text that was decoded as Latin-1 (e.g. 'RenÃ©' for 'René')."""
    out = []
    for act in activities.itertuples(index=False):
        if any(m in str(act.comment) for m in MOJIBAKE):
            out.append(Finding("warning", "encoding",
                               f"'{act.name}': comment contains mis-encoded characters"))
    return out


def check_metadata(metadata):
    """Required metadata fields must be filled."""
    return [Finding("warning", "metadata", f"missing metadata field: {field}")
            for field in REQUIRED_METADATA if not metadata.get(field)]


def run_all(database, activities, exchanges, properties, metadata):
    return (check_counts(database, activities, exchanges, properties)
            + check_production(activities, exchanges)
            + check_links(database, activities, exchanges)
            + check_amounts(exchanges)
            + check_encoding(activities)
            + check_metadata(metadata))
