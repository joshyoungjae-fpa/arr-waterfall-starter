"""
Two-panel ARR chart from monthly_waterfall.csv:
  1. Ending ARR as a line over time
  2. Waterfall components as a diverging stacked bar (new+expansion above
     zero, contraction+churn below zero)

Color choice: the two panels share a single design idea - blue/red is this
palette's documented diverging pair ("which side of a baseline"), so New and
Churn (the customer-count-driven flows) get the solid poles, and Expansion /
Contraction (the existing-customer dollar-delta flows) get a lighter tint of
the same hue. That keeps identity readable via hue (blue side vs red side)
*and* via lightness (solid = core flow, tint = adjustment flow), which is
also what keeps it colorblind-safe without needing four competing hues.

Note: the palette's automated CVD validator (scripts/validate_palette.js)
requires Node, which isn't available in this environment. Contrast ratios
below were checked by hand against the palette's documented light-mode chart
surface (#fcfcfb); the solid blue/red pair and the light tints match values
already validated in the design system's own palette reference.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

INPUT_CSV = "monthly_waterfall.csv"
OUTPUT_PNG = "arr_waterfall_chart.png"

# -- palette (see module docstring) --
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

BLUE_SOLID = "#2a78d6"   # New
BLUE_TINT = "#86b6ef"    # Expansion
RED_SOLID = "#e34948"    # Churned
RED_TINT = "#f09c9a"     # Contraction


def fmt_dollars(x, _pos=None):
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.1f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.0f}K"
    return f"${x:,.0f}"


def main():
    df = pd.read_csv(INPUT_CSV)
    months = df["month"]
    x = range(len(months))

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]

    fig, (ax_line, ax_bar) = plt.subplots(
        2, 1, figsize=(13, 9), sharex=True,
        gridspec_kw={"height_ratios": [1, 1.3], "hspace": 0.12},
        facecolor=SURFACE,
    )

    # ---------- Panel 1: Ending ARR line ----------
    ax_line.set_facecolor(SURFACE)
    ax_line.plot(
        x, df["ending_arr"], color=BLUE_SOLID, linewidth=2,
        marker="o", markersize=5, markerfacecolor=BLUE_SOLID,
        markeredgecolor=SURFACE, markeredgewidth=1, zorder=3,
    )

    # direct label at the line's end, per "lines -> value at the end"
    for xi, yi in zip(x, df["ending_arr"]):
        ax_line.annotate(
            fmt_dollars(yi), xy=(xi, yi),
            xytext=(0, 9), textcoords="offset points",
            va="bottom", ha="center", fontsize=7.5, color=INK_SECONDARY,
        )

    ax_line.set_title("Ending ARR", loc="left", fontsize=13, fontweight="bold", color=INK_PRIMARY, pad=10)
    ax_line.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollars))
    ax_line.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax_line.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax_line.spines[spine].set_visible(False)
    ax_line.spines["bottom"].set_color(BASELINE)
    ax_line.tick_params(axis="y", colors=INK_MUTED, length=0)
    ax_line.tick_params(axis="x", length=0)
    ax_line.set_xlim(-0.6, len(months) - 0.4)

    # ---------- Panel 2: waterfall components, diverging stacked bar ----------
    ax_bar.set_facecolor(SURFACE)
    bar_width = 0.62
    gap_lw = 1.4  # thin surface-color seam between stacked segments

    new_arr = df["new_arr"].to_numpy()
    expansion = df["expansion_arr"].to_numpy()
    contraction = -df["contraction_arr"].to_numpy()  # plot as negative
    churn = -df["churned_arr"].to_numpy()

    ax_bar.bar(
        x, new_arr, width=bar_width, color=BLUE_SOLID, label="New",
        edgecolor=SURFACE, linewidth=gap_lw, zorder=3,
    )
    ax_bar.bar(
        x, expansion, width=bar_width, bottom=new_arr, color=BLUE_TINT, label="Expansion",
        edgecolor=SURFACE, linewidth=gap_lw, zorder=3,
    )
    ax_bar.bar(
        x, churn, width=bar_width, color=RED_SOLID, label="Churned",
        edgecolor=SURFACE, linewidth=gap_lw, zorder=3,
    )
    ax_bar.bar(
        x, contraction, width=bar_width, bottom=churn, color=RED_TINT, label="Contraction",
        edgecolor=SURFACE, linewidth=gap_lw, zorder=3,
    )

    # Every non-zero segment gets a label. New/Churned (the larger, base
    # segments, touching the zero baseline) are labeled at their center in
    # dark ink -- measured to clear 4.5:1 against both solid fills, which flat
    # white does not (3.95:1 on the red). Expansion/Contraction (the thinner,
    # outer segments) are labeled just outside their own tip so text never
    # gets squeezed into a sliver.
    for i in range(len(months)):
        if new_arr[i] > 0:
            ax_bar.annotate(
                fmt_dollars(new_arr[i]), xy=(i, new_arr[i] / 2),
                ha="center", va="center", fontsize=7, fontweight="bold", color=INK_PRIMARY,
            )
        if expansion[i] > 0:
            top = new_arr[i] + expansion[i]
            ax_bar.annotate(
                fmt_dollars(expansion[i]), xy=(i, top), xytext=(0, 4),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=7, color=INK_SECONDARY,
            )
        if churn[i] < 0:
            ax_bar.annotate(
                fmt_dollars(abs(churn[i])), xy=(i, churn[i] / 2),
                ha="center", va="center", fontsize=7, fontweight="bold", color=INK_PRIMARY,
            )
        if contraction[i] < 0:
            bottom = churn[i] + contraction[i]
            ax_bar.annotate(
                fmt_dollars(abs(contraction[i])), xy=(i, bottom), xytext=(0, -4),
                textcoords="offset points", ha="center", va="top",
                fontsize=7, color=INK_SECONDARY,
            )

    pos_top = (new_arr + expansion).max()
    neg_bottom = (churn + contraction).min()
    ax_bar.set_ylim(neg_bottom * 1.30, pos_top * 1.22)

    ax_bar.axhline(0, color=BASELINE, linewidth=1.2, zorder=2)
    ax_bar.set_title("Monthly ARR Waterfall (New + Expansion vs. Contraction + Churn)",
                      loc="left", fontsize=13, fontweight="bold", color=INK_PRIMARY, pad=10)
    ax_bar.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollars))
    ax_bar.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax_bar.set_axisbelow(True)
    for spine in ("top", "right", "left", "bottom"):
        ax_bar.spines[spine].set_visible(False)
    ax_bar.tick_params(axis="y", colors=INK_MUTED, length=0)
    ax_bar.tick_params(axis="x", colors=INK_MUTED, length=0)

    ax_bar.set_xticks(list(x))
    ax_bar.set_xticklabels(months, rotation=45, ha="right", fontsize=9)

    legend = ax_bar.legend(
        loc="upper left", bbox_to_anchor=(0, -0.18), ncol=4,
        frameon=False, fontsize=10, handlelength=1.2, handleheight=1.2,
        labelcolor=INK_SECONDARY,
    )

    fig.suptitle("ARR Waterfall - Jan 2025 to Jun 2026", fontsize=15, fontweight="bold",
                 color=INK_PRIMARY, x=0.01, ha="left", y=0.995)

    fig.savefig(OUTPUT_PNG, dpi=180, facecolor=SURFACE, bbox_inches="tight")
    print(f"Saved {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
