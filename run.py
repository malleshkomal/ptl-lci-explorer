"""Load the power-to-liquid LCI, validate it and scale it to its functional units.

Usage: python run.py [path/to/dataset-folder]
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
warnings.filterwarnings("ignore", module="openpyxl")

from lcitools.model import electricity_by_process, inventory  # noqa: E402
from lcitools.plots import electricity_chart  # noqa: E402
from lcitools.reader import (dataset_paths, read_brightway_csv,  # noqa: E402
                             read_metadata, read_properties)
from lcitools.validate import run_all  # noqa: E402

# Functional units declared in the metadata: 1 kg LH2 and 1 kg e-kerosene.
FUNCTIONAL_UNITS = {
    "1 kg liquid hydrogen (LH2)": "Hydrogen liquefaction",
    "1 kg PtL fuel (Fischer-Tropsch)": "GTL production",
}

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"


def main(folder):
    paths = dataset_paths(folder)
    database, activities, exchanges = read_brightway_csv(paths["csv"])
    properties = read_properties(paths["properties"])
    metadata = read_metadata(paths["metadata"])

    print(f"Dataset   {database} (schema {properties.get('Schema Version')}, "
          f"v{properties.get('Dataset Version')})")
    print(f"Contents  {len(activities)} activities, {len(exchanges)} exchanges")
    print(f"Licence   {metadata.get('License / SPDX Identifier')}")
    print(f"Background {metadata.get('Background / Name')} "
          f"{metadata.get('Background / Version')} {metadata.get('Background / Type')}\n")

    findings = run_all(database, activities, exchanges, properties, metadata)
    print(f"Validation: {len(findings)} finding(s)")
    for f in findings:
        print(f"  [{f.level}] {f.check}: {f.message}")

    RESULTS.mkdir(exist_ok=True)
    activities.to_csv(RESULTS / "activities.csv", index=False)
    exchanges.to_csv(RESULTS / "exchanges.csv", index=False)

    panels = []
    for label, activity in FUNCTIONAL_UNITS.items():
        totals, contributions = inventory(activities, exchanges, {activity: 1.0})
        slug = activity.lower().replace(" ", "_")
        totals.to_csv(RESULTS / f"inventory_{slug}.csv", index=False)
        elec = electricity_by_process(contributions)
        panels.append((label, elec))

        def total(name):
            return totals.loc[totals["name"] == name, "scaled amount"].sum()

        print(f"\n{label}")
        print(f"  electricity (wind)    {elec.sum():8.2f} kWh")
        for act, kwh in elec.items():
            print(f"    {act:<42} {kwh:6.2f} kWh")
        print(f"  deionised water       {total('market for water, deionised'):8.2f} kg")
        print(f"  CO2 captured from air {total('Carbon dioxide, in air'):8.2f} kg")

    electricity_chart(panels, RESULTS / "electricity_per_kg.png")
    print(f"\nWrote tidy tables, inventories and chart to {RESULTS.relative_to(ROOT)}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data/original/power-to-liquid")
