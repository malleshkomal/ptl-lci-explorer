"""Draw the animated PtL flow diagram as an SVG for README previews.

GitHub READMEs cannot run JavaScript, but they do play SVG (SMIL) animation,
so this writes a self-contained SVG whose dots move along each flow. The
interactive version with the LH2 switch and walk-through is docs/flow.html.

Flow amounts come from results/dashboard_data/ (written by run.py). The two
water outputs are not in the dataset: they are inputs minus product.

Usage: python make_flow_preview.py
"""

import json
from math import sqrt
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "results" / "dashboard_data"
OUT = ROOT / "results" / "charts" / "08_flow_animated.svg"

ELEC = "electricity production, wind, 1-3MW turbine, onshore"
BG, PANEL, INK, MUTED, GRID = "#EEF2F1", "#FFFFFF", "#16242B", "#5A6B70", "#DDE5E4"
COLOR = {"elec": "#C98A00", "water": "#3E9CC2", "co2": "#7B6A9E", "h2": "#2F74C8",
         "co": "#1B9483", "syn": "#0E6F68", "fuel": "#D04A12"}
FONT = "'IBM Plex Sans Condensed','Arial Narrow',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# id: (label, x, y, w, h, kind)
NODES = {
    "water": ("Deionised water", 75, 110, 120, 48, "src"),
    "wind": ("Wind electricity", 75, 260, 120, 48, "src"),
    "air": ("CO₂ in air", 75, 455, 120, 48, "src"),
    "ael": ("Alkaline electrolysis", 300, 110, 144, 62, "proc"),
    "dac": ("Direct air capture", 300, 440, 144, 62, "proc"),
    "comp": ("H₂ compression · 25 bar", 520, 260, 144, 62, "proc"),
    "rwgs": ("Reverse water-gas shift", 700, 440, 144, 62, "proc"),
    "syn": ("Syngas mixing", 920, 440, 144, 62, "proc"),
    "ft": ("Fischer-Tropsch", 1130, 440, 144, 62, "proc"),
    "ptl": ("1 kg PtL fuel", 1320, 440, 110, 52, "prod"),
    "wout": ("Water out", 920, 530, 150, 36, "sink"),
}
LABEL_TO_NODE = {
    "Alkaline electrolysis": "ael", "Direct air capture": "dac", "H2 compression": "comp",
    "Reverse water-gas shift": "rwgs", "Syngas mixing": "syn", "Fischer-Tropsch synthesis": "ft",
}
EQUIPMENT = {  # scaling.json label -> node
    "Electrolyser (equipment)": "ael", "DAC unit (equipment)": "dac",
    "H2 compressor (equipment)": "comp", "RWGS reactor (equipment)": "rwgs",
    "Fischer-Tropsch plant (equipment)": "ft",
}
# (from, to, flow type, path, label x, label y, anchor)
EDGES = [
    ("water", "ael", "water", "M135,110 L228,110", 181, 102, "middle"),
    ("wind", "ael", "elec", "M135,248 L185,248 L185,125 L228,125", 192, 165, "start"),
    ("wind", "comp", "elec", "M135,260 L448,260", 330, 252, "middle"),
    ("wind", "dac", "elec", "M135,272 L185,272 L185,425 L228,425", 192, 350, "start"),
    ("air", "dac", "co2", "M135,455 L228,455", 181, 447, "middle"),
    ("ael", "comp", "h2", "M372,110 L500,110 L500,229", 436, 102, "middle"),
    ("comp", "rwgs", "h2", "M560,291 L560,425 L628,425", 567, 360, "start"),
    ("dac", "rwgs", "co2", "M372,448 L628,448", 500, 440, "middle"),
    ("comp", "syn", "h2", "M592,272 L920,272 L920,409", 927, 340, "start"),
    ("rwgs", "syn", "co", "M772,440 L848,440", 810, 432, "middle"),
    ("syn", "ft", "syn", "M992,440 L1058,440", 1025, 432, "middle"),
    ("ft", "ptl", "fuel", "M1202,440 L1265,440", 1233, 432, "middle"),
    ("rwgs", "wout", "water", "M740,471 L740,530 L845,530", 792, 522, "middle"),
    ("ft", "wout", "water", "M1170,471 L1170,530 L995,530", 1082, 522, "middle"),
]


def load_amounts():
    mass = json.load(open(DATA / "mass_flows.json"))
    contrib = json.load(open(DATA / "contributions.json"))
    node = {**LABEL_TO_NODE, "CO2 in air": "air", "PtL fuel": "ptl"}
    amt = {(node[m["source"]], node[m["target"]]): m["kg"] for m in mass}
    for c in contrib:
        if c["fu"] != "ptl" or c["label"] not in LABEL_TO_NODE:
            continue
        if c["flow"] == ELEC:
            amt[("wind", LABEL_TO_NODE[c["label"]])] = c["amount"]
        elif c["flow"] == "market for water, deionised":
            amt[("water", LABEL_TO_NODE[c["label"]])] = c["amount"]
    # Water released, by mass balance (inputs minus product)
    amt[("rwgs", "wout")] = amt[("dac", "rwgs")] + amt[("comp", "rwgs")] - amt[("rwgs", "syn")]
    amt[("ft", "wout")] = amt[("syn", "ft")] - amt[("ft", "ptl")]
    return amt


def lifetime_output(amount):
    kg = 1 / amount
    if kg >= 1e9:
        return f"1 per {kg / 1e9:,.0f} Mt"
    if kg >= 1e6:
        return f"1 per {kg / 1e6:,.{0 if kg >= 1e8 else 1}f} kt"
    return f"1 per {kg / 1e3:,.0f} t"


def path_length(d):
    pts = [tuple(map(float, p[1:].split(","))) for p in d.split()]
    return sum(sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) for (x1, y1), (x2, y2) in zip(pts, pts[1:]))


def fmt(v, unit):
    s = f"{v:.1f}" if v >= 10 else f"{v:.2f}"
    return f"{s} {unit}"


def main():
    amt = load_amounts()
    scaling = json.load(open(DATA / "scaling.json"))
    eq = {EQUIPMENT[s["label"]]: s["amount"] for s in scaling
          if s["fu"] == "ptl" and s["label"] in EQUIPMENT}
    elec_total = sum(v for (f, _), v in amt.items() if f == "wind")

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 20 1400 545" width="1400" height="545" '
           f'role="img" aria-label="Animated flow diagram: wind power, water and CO2 from air become 1 kg of PtL jet fuel">',
           f'<rect x="0" y="20" width="1400" height="545" rx="10" fill="{BG}"/>']
    out += [f'<line x1="{x}" y1="20" x2="{x}" y2="565" stroke="{GRID}"/>' for x in range(50, 1400, 50)]
    out += [f'<line x1="0" y1="{y}" x2="1400" y2="{y}" stroke="{GRID}"/>' for y in range(50, 565, 50)]
    out.append(f'<text x="24" y="52" font-family="{FONT}" font-size="22" font-weight="600" fill="{INK}">'
               f'How wind becomes jet fuel</text>')
    out.append(f'<text x="1376" y="52" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}">'
               f'flows per 1 kg of PtL fuel · {elec_total:.1f} kWh · {amt[("air", "dac")]:.2f} kg CO₂ from air</text>')

    lines, dots, labels = [], [], []
    for f, t, ty, d, lx, ly, anchor in EDGES:
        v = amt[(f, t)]
        w = 1.5 + 1.25 * sqrt(v) if ty == "elec" else 1.6 + 3.1 * sqrt(v)
        dash = ' stroke-dasharray="5 4"' if t == "wout" else ""
        lines.append(f'<path d="{d}" fill="none" stroke="{PANEL}" stroke-width="{w + 5:.1f}" stroke-linejoin="round"/>')
        lines.append(f'<path d="{d}" fill="none" stroke="{COLOR[ty]}" stroke-width="{w:.1f}" stroke-linejoin="round"{dash}/>')
        length = path_length(d)
        speed = 95 if ty == "elec" else 48
        dur = length / speed
        n = max(2, int(length // (26 if ty == "elec" else 34)))
        r = max(1.6, min(4.2, w * 0.36))
        for i in range(n):
            dots.append(f'<circle r="{r:.1f}" fill="{PANEL}" stroke="{COLOR[ty]}" stroke-width="1.5">'
                        f'<animateMotion dur="{dur:.2f}s" begin="-{dur * i / n:.2f}s" repeatCount="indefinite" path="{d}"/></circle>')
        unit = "kWh" if ty == "elec" else "kg"
        labels.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-family="{MONO}" font-size="11.5" '
                      f'fill="{INK}" stroke="{PANEL}" stroke-width="4" paint-order="stroke">{fmt(v, unit)}</text>')
    out += lines + dots + labels

    for nid, (name, x, y, w, h, kind) in NODES.items():
        fill, stroke, color, extra = PANEL, INK, INK, ""
        if kind == "src":
            stroke, extra = MUTED, ' stroke-dasharray="4 3"'
        elif kind == "sink":
            stroke, extra = COLOR["water"], ' stroke-dasharray="4 3"'
        elif kind == "prod":
            fill = stroke = COLOR["fuel"]
            color = "#FFFFFF"
        out.append(f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="6" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="1.3"{extra}/>')
        ty = y - 3 if kind == "proc" else y + 4.5
        out.append(f'<text x="{x}" y="{ty}" text-anchor="middle" font-family="{FONT}" font-size="12" '
                   f'font-weight="600" fill="{color}">{name}</text>')
        if nid in eq:
            out.append(f'<text x="{x}" y="{y + 15}" text-anchor="middle" font-family="{MONO}" font-size="10.5" '
                       f'fill="{MUTED}">{lifetime_output(eq[nid])}</text>')
    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
