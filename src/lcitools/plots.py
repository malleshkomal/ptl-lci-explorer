"""Charts for the README (static PNG)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"

SHORT = {
    "Hydrogen production, alkaline electrolysis": "Alkaline electrolysis",
    "Hydrogen compression to 25 bar": "H₂ compression (25 bar)",
    "Hydrogen liquefaction": "H₂ liquefaction",
    "Direct air capture": "Direct air capture",
}


def electricity_chart(panels, path):
    """Horizontal bars of kWh per functional unit, one panel per product.

    panels: list of (title, Series indexed by activity name).
    """
    xmax = max(s.sum() for _, s in panels) * 1.18
    nrows = max(len(s) for _, s in panels)
    fig, axes = plt.subplots(1, len(panels), figsize=(11, 0.55 * nrows + 1.9),
                             sharex=True, facecolor=SURFACE)
    for ax, (title, s) in zip(axes, panels):
        s = s.sort_values()
        labels = [SHORT.get(n, n) for n in s.index]
        ax.barh(labels, s.values, color=SERIES, height=0.6)
        for y, v in enumerate(s.values):
            ax.text(v + xmax * 0.012, y, f"{v:.1f}", va="center",
                    fontsize=10, color=TEXT)
        ax.set_title(f"{title}\n{s.sum():.1f} kWh in total", loc="left",
                     fontsize=12, color=TEXT, fontweight="bold")
        ax.set_facecolor(SURFACE)
        ax.set_xlim(0, xmax)
        ax.set_ylim(-0.6, nrows - 0.4)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(colors=TEXT_2, length=0, labelsize=10)
        ax.set_xlabel("kWh wind electricity per kg product", color=TEXT_2)
    fig.suptitle("Electrolysis dominates electricity demand in both supply chains",
                 x=0.01, ha="left", fontsize=14, color=TEXT, fontweight="bold")
    fig.text(0.01, 0.005, "Source: foreground LCI of Nair et al. (2025), scaled with lcitools. "
             "Inventory quantities, not impact scores.", fontsize=8, color=TEXT_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
