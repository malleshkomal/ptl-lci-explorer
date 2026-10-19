"""Scale the foreground inventory to a functional unit.

The foreground system is a square technosphere matrix A (one column per
activity, production on the diagonal, inputs as negative entries). Solving
A · s = f gives the scaling vector s: how much of each foreground activity
is needed to deliver the demand f. Background (ecoinvent) inputs and
elementary (biosphere) flows are then summed as s-weighted exchanges.

No background database is needed: results are life cycle *inventory*
quantities (kWh, kg, m²·a ...), not impact scores.
"""

import numpy as np
import pandas as pd


def foreground_matrix(activities, exchanges):
    """Return (A, names) for the foreground technosphere."""
    names = list(activities["name"])
    index = {n: i for i, n in enumerate(names)}
    A = np.zeros((len(names), len(names)))
    for exc in exchanges.itertuples(index=False):
        if exc.name not in index:
            continue
        row, col = index[exc.name], index[exc.activity]
        if exc.type == "production":
            A[row, col] += exc.amount
        elif exc.type == "technosphere":
            A[row, col] -= exc.amount
    return A, names


def upstream(activities, exchanges, start):
    """Foreground activities reachable from ``start`` through technosphere inputs."""
    foreground = set(activities["name"])
    tech = exchanges[(exchanges["type"] == "technosphere")
                     & exchanges["name"].isin(foreground)]
    inputs = tech.groupby("activity")["name"].apply(set).to_dict()
    seen, stack = set(), list(start)
    while stack:
        name = stack.pop()
        if name not in seen:
            seen.add(name)
            stack.extend(inputs.get(name, ()))
    return seen


def scaling_vector(activities, exchanges, demand):
    """Solve A · s = f for a demand dict {activity name: amount}.

    Only the activities upstream of the demand are solved, so unrelated
    branches are exactly zero rather than floating-point noise.
    """
    A, names = foreground_matrix(activities, exchanges)
    needed = upstream(activities, exchanges, demand)
    idx = [i for i, n in enumerate(names) if n in needed]
    f = np.array([demand.get(names[i], 0.0) for i in idx])
    s = np.zeros(len(names))
    s[idx] = np.linalg.solve(A[np.ix_(idx, idx)], f)
    return pd.Series(s, index=names, name="scaling")


def inventory(activities, exchanges, demand):
    """Background inputs and biosphere flows per functional unit.

    Returns a DataFrame with one row per (flow, unit, type) and a
    ``contributions`` breakdown by foreground activity in long format.
    """
    s = scaling_vector(activities, exchanges, demand)
    foreground = set(activities["name"])
    ext = exchanges[(exchanges["type"] != "production")
                    & ~exchanges["name"].isin(foreground)].copy()
    ext["scaled amount"] = ext["amount"] * ext["activity"].map(s)
    ext = ext[ext["scaled amount"] != 0]

    keys = ["type", "name", "unit"]
    totals = (ext.groupby(keys, as_index=False)["scaled amount"].sum()
              .sort_values(keys).reset_index(drop=True))
    contributions = ext[["activity"] + keys + ["scaled amount"]]
    return totals, contributions


def electricity_by_process(contributions):
    """Electricity (kWh) per functional unit, broken down by foreground activity."""
    elec = contributions[contributions["name"].str.startswith("electricity")
                         & (contributions["unit"] == "kilowatt hour")]
    return (elec.groupby("activity")["scaled amount"].sum()
            .sort_values(ascending=False))
