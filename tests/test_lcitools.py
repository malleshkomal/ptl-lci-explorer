import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore", module="openpyxl")

from lcitools.model import inventory, scaling_vector, upstream  # noqa: E402
from lcitools.reader import (dataset_paths, read_brightway_csv,  # noqa: E402
                             read_metadata, read_properties)
from lcitools.validate import (check_counts, check_links,  # noqa: E402
                               check_production, run_all)

PATHS = dataset_paths(ROOT / "data/original/power-to-liquid")


@pytest.fixture(scope="module")
def data():
    return read_brightway_csv(PATHS["csv"])


def amount(totals, name):
    return totals.loc[totals["name"] == name, "scaled amount"].sum()


def test_parsed_counts_match_properties_file(data):
    db, acts, excs = data
    assert check_counts(db, acts, excs, read_properties(PATHS["properties"])) == []
    assert (len(acts), len(excs)) == (14, 80)


def test_every_activity_has_one_matching_production_exchange(data):
    _, acts, excs = data
    assert check_production(acts, excs) == []


def test_metadata_licence_is_read():
    meta = read_metadata(PATHS["metadata"])
    assert meta["License / SPDX Identifier"] == "CC-BY-NC-4.0"


def test_dangling_foreground_links_are_flagged(data):
    db, acts, excs = data
    findings = check_links(db, acts, excs)
    assert len(findings) == 1
    assert "Alkaline electrolyser construction" in findings[0].message


def test_demand_is_met_exactly(data):
    _, acts, excs = data
    s = scaling_vector(acts, excs, {"GTL production": 1.0})
    assert s["GTL production"] == pytest.approx(1.0)
    # 2.3 kg syngas x 0.875 kg CO per kg syngas
    assert s["CO production via RWGS"] == pytest.approx(2.3 * 0.875)


def test_unrelated_branches_are_exactly_zero(data):
    _, acts, excs = data
    s = scaling_vector(acts, excs, {"GTL production": 1.0})
    assert s["Hydrogen liquefaction"] == 0.0
    assert "Direct air capture" not in upstream(acts, excs, {"Hydrogen liquefaction"})


def test_lh2_electricity_is_sum_of_process_steps(data):
    _, acts, excs = data
    totals, _ = inventory(acts, excs, {"Hydrogen liquefaction": 1.0})
    expected = 6.86985 + 1.01625 * (0.66 + 56.7)
    assert amount(totals, "electricity production, wind, 1-3MW turbine, onshore") \
        == pytest.approx(expected)


def test_ptl_carbon_uptake_matches_co2_stoichiometry(data):
    _, acts, excs = data
    totals, _ = inventory(acts, excs, {"GTL production": 1.0})
    assert amount(totals, "Carbon dioxide, in air") == pytest.approx(2.3 * 0.875 * 1.57)


def test_inventory_scales_linearly(data):
    _, acts, excs = data
    one, _ = inventory(acts, excs, {"GTL production": 1.0})
    ten, _ = inventory(acts, excs, {"GTL production": 10.0})
    pd.testing.assert_series_equal(ten["scaled amount"], one["scaled amount"] * 10)


def test_no_structural_errors(data):
    db, acts, excs = data
    findings = run_all(db, acts, excs, read_properties(PATHS["properties"]),
                       read_metadata(PATHS["metadata"]))
    assert not [f for f in findings if f.level == "error"]
