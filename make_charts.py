"""Draw the findings charts as PNG files in results/charts/.

Usage: python make_charts.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
warnings.filterwarnings("ignore", module="openpyxl")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

from lcitools.model import electricity_by_process, inventory, scaling_vector  # noqa: E402
from lcitools.reader import dataset_paths, read_brightway_csv  # noqa: E402

ROOT = Path(__file__).parent
OUT = ROOT / "results" / "charts"

SURFACE, TEXT, TEXT_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#b9b8b1"
SOURCE = "Source: foreground LCI of Nair et al. (DLR), CC BY-NC 4.0; scaled with lcitools."

FU = {"ptl": "GTL production", "lh2": "Hydrogen liquefaction"}
FU_NAME = {"ptl": "PtL fuel", "lh2": "Liquid hydrogen"}
LHV = {"lh2": 33.3, "ptl": 11.9}  # kWh/kg: H2 120 MJ/kg, kerosene-like fuel 43 MJ/kg
ELEC = "electricity production, wind, 1-3MW turbine, onshore"
SHORT = {
    "Hydrogen production, alkaline electrolysis": "Electrolysis",
    "Hydrogen liquefaction": "Liquefaction",
    "Hydrogen compression to 25 bar": "Compression",
    "Direct air capture": "Air capture",
}
EQUIPMENT = {
    "GTL plant construction": ("Fischer-Tropsch plant", "PtL fuel"),
    "Fixed bed reactor construction": ("RWGS reactor", "carbon monoxide"),
    "Hydrogen liquefaction plant construction": ("Liquefaction plant", "liquid hydrogen"),
    "Hydrogen compressor production": ("H₂ compressor", "compressed hydrogen"),
    "Direct air capture (DAC) equipment": ("DAC unit", "CO₂ captured"),
    "Alkaline electrolyser construction": ("Electrolyser", "hydrogen"),
}


def figure(w, h, title, subtitle=None):
    fig = plt.figure(figsize=(w, h), facecolor=SURFACE)
    fig.text(0.02, 0.97, title, fontsize=15, fontweight="bold", color=TEXT, va="top")
    if subtitle:
        fig.text(0.02, 0.905, subtitle, fontsize=10.5, color=TEXT_2, va="top")
    fig.text(0.02, 0.015, SOURCE, fontsize=8, color=TEXT_2)
    return fig


def style(ax, grid_axis="x"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=TEXT_2, length=0, labelsize=10)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))


def hbar_labels(ax, bars, values, fmt):
    xmax = ax.get_xlim()[1]
    for b, v in zip(bars, values):
        ax.text(b.get_width() + xmax * 0.01, b.get_y() + b.get_height() / 2, fmt(v),
                va="center", fontsize=10, color=TEXT)


def mass_flows(acts, excs):
    """kg moved between process steps per kg PtL fuel, plus water by difference."""
    s = scaling_vector(acts, excs, {FU["ptl"]: 1.0})
    label = {"Direct air capture": "Direct air capture", "Hydrogen production, alkaline electrolysis": "Electrolysis",
             "Hydrogen compression to 25 bar": "H₂ compression", "CO production via RWGS": "Reverse water-gas shift",
             "Syngas production": "Syngas mixing", "GTL production": "Fischer-Tropsch"}
    links = [("CO₂ in air", "Direct air capture", s["Direct air capture"], "CO₂")]
    material = {"Direct air capture": "CO₂", "Electrolysis": "H₂", "H₂ compression": "H₂",
                "Reverse water-gas shift": "CO", "Syngas mixing": "Syngas"}
    for r in excs.itertuples(index=False):
        if (r.type == "technosphere" and r.name in label and r.activity in label
                and r.unit == "kilogram" and s[r.activity]):
            src = label[r.name]
            links.append((src, label[r.activity], s[r.activity] * r.amount, material[src]))
    links.append(("Fischer-Tropsch", "PtL fuel", 1.0, "Fuel"))
    nodes = {n for l in links for n in l[:2]}
    for n in sorted(nodes):
        inflow = sum(l[2] for l in links if l[1] == n)
        outflow = sum(l[2] for l in links if l[0] == n)
        if inflow and outflow and inflow - outflow > 1e-9:
            links.append((n, "Water (by-product)", inflow - outflow, "Water"))
    return links


def chart_sankey(acts, excs):
    links = mass_flows(acts, excs)
    names = list(dict.fromkeys(n for l in links for n in l[:2]))
    depth = {n: 0 for n in names}
    for _ in names:
        for s, t, *_ in links:
            depth[t] = max(depth[t], depth[s] + 1)
    maxd = max(depth.values())
    for n in names:
        if not any(l[0] == n for l in links):
            depth[n] = maxd
    value = {n: max(sum(l[2] for l in links if l[1] == n), sum(l[2] for l in links if l[0] == n)) for n in names}
    order = {"CO₂ in air": 0, "Electrolysis": 1, "Direct air capture": 0, "H₂ compression": 1,
             "PtL fuel": 0, "Water (by-product)": 1}
    cols = {}
    for n in names:
        cols.setdefault(depth[n], []).append(n)
    H, pad = 1.0, 0.07
    k = min((H - pad * (len(ns) - 1)) / sum(value[n] for n in ns) for ns in cols.values())
    pos = {}
    for d, ns in cols.items():
        ns.sort(key=lambda n: order.get(n, 0))
        total = sum(value[n] * k for n in ns) + pad * (len(ns) - 1)
        y = (H - total) / 2
        for n in ns:
            pos[n] = [d, y, value[n] * k]
            y += value[n] * k + pad

    fig = figure(13, 6.6, "How 1 kg of PtL fuel is made",
                 "Ribbon width = kg per kg of fuel. Most of the mass that goes in leaves again as water.")
    ax = fig.add_axes([0.02, 0.07, 0.86, 0.78])
    ax.set_xlim(-0.05, maxd + 0.1)
    ax.set_ylim(H + 0.02, -0.02)
    ax.axis("off")
    color = {"CO₂": BLUE, "CO": BLUE, "Syngas": BLUE, "Fuel": BLUE, "H₂": ORANGE, "Water": MUTED}
    nw = 0.06
    out_y = {n: pos[n][1] for n in names}
    in_y = {n: pos[n][1] for n in names}
    for s, t, kg, m in sorted(links, key=lambda l: (pos[l[1]][1], pos[l[0]][1])):
        w = kg * k
        x0, x1 = pos[s][0] + nw, pos[t][0]
        y0, y1 = out_y[s], in_y[t]
        out_y[s] += w
        in_y[t] += w
        xm = (x0 + x1) / 2
        verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 + w), (xm, y1 + w), (xm, y0 + w), (x0, y0 + w), (x0, y0)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color[m], alpha=0.45, lw=0))
    for n, (d, y, h) in pos.items():
        ax.add_patch(plt.Rectangle((d, y), nw, max(h, 0.004), color=TEXT))
        ax.text(d + nw + 0.04, y + h / 2, f"{n}\n{value[n]:.2f} kg", va="center", fontsize=10, color=TEXT,
                bbox=dict(facecolor=SURFACE, edgecolor="none", alpha=0.75, pad=1))
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.6) for c in (BLUE, ORANGE, MUTED)]
    fig.legend(handles, ["Carbon path (CO₂ → CO → syngas → fuel)", "Hydrogen", "Water by-product"],
               loc="upper right", frameon=False, fontsize=9.5, ncol=3, bbox_to_anchor=(0.99, 0.965))
    save(fig, "01_mass_flow_sankey.png")


def chart_electricity(acts, excs):
    data = {fu: electricity_by_process(inventory(acts, excs, {a: 1.0})[1]) for fu, a in FU.items()}
    fig = figure(12, 4.8, "Electrolysis uses almost all the electricity",
                 "kWh of wind electricity per kg of product, by process step (shared scale)")
    xmax = max(s.max() for s in data.values()) * 1.25
    for i, fu in enumerate(["ptl", "lh2"]):
        s = data[fu].sort_values()
        ax = fig.add_axes([0.12 + i * 0.48, 0.14, 0.36, 0.62])
        style(ax)
        colors = [BLUE if a.startswith("Hydrogen production") else MUTED for a in s.index]
        bars = ax.barh([SHORT[a] for a in s.index], s.values, color=colors, height=0.6)
        ax.set_xlim(0, xmax)
        hbar_labels(ax, bars, s.values, lambda v: f"{v:.1f}")
        ax.set_title(f"{FU_NAME[fu]} · {s.sum():.1f} kWh in total", loc="left", fontsize=11.5, color=TEXT, fontweight="bold")
        ax.set_xlabel("kWh per kg", color=TEXT_2)
    save(fig, "02_electricity_by_step.png")


def chart_energy(acts, excs):
    fig = figure(10, 3.8, "About half of the electricity ends up in the product",
                 "Energy content of 1 kg of product (lower heating value) vs electricity used")
    ax = fig.add_axes([0.17, 0.16, 0.78, 0.6])
    style(ax, None)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    for i, fu in enumerate(["ptl", "lh2"]):
        kwh = electricity_by_process(inventory(acts, excs, {FU[fu]: 1.0})[1]).sum()
        kept = LHV[fu] / kwh
        ax.barh(i, kept, color=BLUE, height=0.55)
        ax.barh(i, 1 - kept, left=kept, color=MUTED, alpha=0.6, height=0.55)
        ax.text(0.015, i, f"{kept:.0%} in the product ({LHV[fu]:.1f} kWh)", va="center", color="white", fontsize=10.5, fontweight="bold")
        ax.text(0.985, i, f"{1 - kept:.0%} lost as heat ({kwh - LHV[fu]:.1f} kWh)", va="center", ha="right", color=TEXT, fontsize=10)
    ax.set_yticks([0, 1], [f"PtL fuel\n{electricity_by_process(inventory(acts, excs, {FU['ptl']: 1})[1]).sum():.1f} kWh in",
                           f"Liquid hydrogen\n{electricity_by_process(inventory(acts, excs, {FU['lh2']: 1})[1]).sum():.1f} kWh in"])
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    fig.text(0.17, 0.065, "Assumed heating values: H₂ 33.3 kWh/kg (120 MJ/kg), kerosene-like fuel 11.9 kWh/kg (43 MJ/kg).",
             fontsize=8.5, color=TEXT_2)
    save(fig, "03_energy_kept.png")


def chart_hydrogen_carbon(acts, excs):
    links = mass_flows(acts, excs)
    h2 = {t: kg for s, t, kg, m in links if s == "H₂ compression"}
    totals, _ = inventory(acts, excs, {FU["ptl"]: 1.0})
    captured = totals.loc[totals["name"] == "Carbon dioxide, in air", "scaled amount"].sum()
    released = 44 / 14

    fig = figure(12, 4.4, "Hydrogen use and the carbon loop, per kg of PtL fuel")
    ax = fig.add_axes([0.04, 0.2, 0.42, 0.5])
    style(ax, None)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([]), ax.set_yticks([])
    total = sum(h2.values())
    left = 0
    for (t, kg), c, name in zip(sorted(h2.items(), key=lambda x: -x[1]), (ORANGE, MUTED),
                                ("Straight into syngas", "To turn CO₂ into CO")):
        ax.barh(0, kg, left=left, color=c, height=0.5)
        ax.text(left + kg / 2, 0, f"{kg:.3f} kg\n{kg / total:.0%}", ha="center", va="center", fontsize=10,
                color="white" if c == ORANGE else TEXT, fontweight="bold")
        ax.text(left + kg / 2, 0.42, name, ha="center", fontsize=10, color=TEXT_2)
        left += kg
    ax.set_xlim(0, total)
    ax.set_ylim(0.6, -0.5)
    ax.set_title(f"{total:.3f} kg of hydrogen needed", loc="left", fontsize=11.5, color=TEXT, fontweight="bold")

    ax2 = fig.add_axes([0.62, 0.2, 0.33, 0.5])
    style(ax2)
    bars = ax2.barh(["Captured from the air", "Released when burned"], [captured, released], color=[BLUE, MUTED], height=0.55)
    ax2.set_xlim(0, 3.9)
    ax2.invert_yaxis()
    hbar_labels(ax2, bars, [captured, released], lambda v: f"{v:.2f} kg")
    ax2.set_title("The carbon loop (kg CO₂)", loc="left", fontsize=11.5, color=TEXT, fontweight="bold")
    fig.text(0.62, 0.085, f"Difference {abs(captured - released):.2f} kg ({abs(captured - released) / released:.1%}). "
             "Burning assumes –CH₂– fuel (44/14 kg CO₂ per kg).", fontsize=8.5, color=TEXT_2)
    save(fig, "04_hydrogen_and_carbon.png")


def chart_materials(acts, excs):
    fig = figure(13, 5.8, "Material inputs from the wider economy",
                 "Top 10 materials in grams per kg of product (deionised water left out: 4.75 kg and 11.3 kg)")
    for i, fu in enumerate(["ptl", "lh2"]):
        t, _ = inventory(acts, excs, {FU[fu]: 1.0})
        t = t[(t["type"] == "technosphere") & (t["unit"] == "kilogram") & (t["name"] != "market for water, deionised")]
        t = t.sort_values("scaled amount", ascending=False).head(10).iloc[::-1]
        names = [n.replace("market for ", "").replace("market group for ", "").replace("treatment of ", "treatment: ") for n in t["name"]]
        ax = fig.add_axes([0.2 + i * 0.5, 0.1, 0.27, 0.7])
        style(ax)
        grams = t["scaled amount"].values * 1000
        bars = ax.barh(names, grams, color=BLUE, height=0.6)
        ax.set_xlim(0, grams.max() * 1.3)
        hbar_labels(ax, bars, grams, lambda v: f"{v:.2f} g" if v >= 0.01 else f"{v:.3f} g")
        ax.tick_params(axis="y", labelsize=9)
        ax.set_title(f"Per kg of {FU_NAME[fu].lower() if fu == 'lh2' else 'PtL fuel'}", loc="left", fontsize=11.5, color=TEXT, fontweight="bold")
    save(fig, "05_materials.png")


def chart_equipment(acts, excs):
    rows = []
    for r in excs.itertuples(index=False):
        if r.type == "technosphere" and r.name in EQUIPMENT and r.activity not in EQUIPMENT:
            name, product = EQUIPMENT[r.name]
            rows.append((name, product, 1 / r.amount / 1000))
    rows.sort(key=lambda x: x[2])
    fig = figure(11, 4.8, "Equipment lasts a long time",
                 "Lifetime output of one unit, in tonnes of product (log scale: each gridline is ×10)")
    ax = fig.add_axes([0.2, 0.14, 0.62, 0.64])
    style(ax)
    ax.set_xscale("log")
    bars = ax.barh([r[0] for r in rows], [r[2] for r in rows], color=BLUE, height=0.6)
    ax.set_xlim(100, 1e9)
    for b, (_, product, t) in zip(bars, rows):
        label = f"{t:,.0f} t {product}" if t < 1e6 else f"{t / 1e6:.0f} million t {product}"
        ax.text(t * 1.25, b.get_y() + b.get_height() / 2, label, va="center", fontsize=9.5, color=TEXT)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: {1e2: "100 t", 1e3: "1k t", 1e4: "10k t", 1e5: "100k t", 1e6: "1M t", 1e7: "10M t", 1e8: "100M t", 1e9: "1B t"}.get(v, "")))
    save(fig, "06_equipment_lifetime.png")


def chart_anatomy(acts, excs):
    fg = set(acts["name"])
    labels = {**{a: n for a, (n, _) in EQUIPMENT.items()}, "RWGS catalyst production": "RWGS catalyst",
              "Hydrogen production, alkaline electrolysis": "Alkaline electrolysis", "Direct air capture": "Direct air capture",
              "CO production via RWGS": "Reverse water-gas shift", "GTL production": "Fischer-Tropsch synthesis",
              "Hydrogen compression to 25 bar": "H₂ compression", "Hydrogen liquefaction": "H₂ liquefaction",
              "Syngas production": "Syngas mixing"}
    rows = []
    for a in acts["name"]:
        e = excs[(excs["activity"] == a) & (excs["type"] != "production")]
        tech = e[e["type"] == "technosphere"]
        rows.append((labels[a], int(tech["name"].isin(fg).sum()), int((~tech["name"].isin(fg)).sum()),
                     int((e["type"] == "biosphere").sum())))
    rows.sort(key=lambda r: sum(r[1:]))
    fig = figure(11, 6.2, "Inside the dataset: exchanges per activity",
                 f"{len(acts)} activities, {len(excs)} exchanges. Each activity's own output line is not counted.")
    ax = fig.add_axes([0.24, 0.1, 0.7, 0.7])
    style(ax)
    y = np.arange(len(rows))
    left = np.zeros(len(rows))
    for j, (name, c) in enumerate([("From this dataset", BLUE), ("From ecoinvent", ORANGE), ("With the environment", AQUA)]):
        vals = np.array([r[j + 1] for r in rows])
        ax.barh(y, vals, left=left, color=c, height=0.62, label=name, edgecolor=SURFACE, linewidth=1.5)
        left += vals
    for yi, total in zip(y, left):
        ax.text(total + 0.15, yi, str(int(total)), va="center", fontsize=10, color=TEXT)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.legend(frameon=False, fontsize=9.5, ncol=3, loc="lower right", bbox_to_anchor=(1, 1.0))
    save(fig, "07_dataset_anatomy.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    _, acts, excs = read_brightway_csv(dataset_paths(ROOT / "data/original/power-to-liquid")["csv"])
    for chart in (chart_sankey, chart_electricity, chart_energy, chart_hydrogen_carbon,
                  chart_materials, chart_equipment, chart_anatomy):
        chart(acts, excs)


if __name__ == "__main__":
    main()
