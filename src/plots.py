import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def hist_leverage(L_by_mode, thresholds, current, path, clip_max):
    fig, axes = plt.subplots(1, len(L_by_mode), figsize=(11, 4), sharey=True)
    for ax, (mode, L) in zip(np.atleast_1d(axes), L_by_mode.items()):
        ax.hist(np.clip(L, 0, clip_max), bins=60, color="#4C78A8")
        for t in thresholds:
            ax.axvline(t, color="#E45756", ls="--", label=f"{t}x threshold")
        ax.axvline(current[mode], color="black", label=f"current {current[mode]:.2f}x")
        ax.set_title(f"Month-12 ND/EBITDA ({mode})")
        ax.set_xlabel(f"ND / LTM EBITDA (clipped at {clip_max:g}x)")
        ax.legend(fontsize=8)
    np.atleast_1d(axes)[0].set_ylabel("paths")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
REF_LOW, REF_HIGH = "#8a8985", "#0b0b0b"


def _style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK_2)
    ax.tick_params(colors=INK_2, labelsize=9)


def credit_breakeven(capex, curves, thresholds, target, guidance, points, path):
    """L_2030 vs constant annual capex (SAR bn). curves: {label: L array}. points: [(series index, capex, L)].
    target: (low, high) of the company leverage target range, for the labels."""
    fig, ax = plt.subplots(figsize=(9.5, 5.5), facecolor=SURFACE)
    _style(ax)
    x = np.asarray(capex) / 1e3
    for i, (label, y) in enumerate(curves.items()):
        ax.plot(x, y, color=SERIES[i], lw=2, label=label, zorder=3)
        ax.annotate(label, (x[-1], y[-1]), xytext=(5, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    low, high = thresholds
    ax.axhline(low, color=REF_LOW, ls="--", lw=1.2, zorder=2)
    ax.axhline(high, color=REF_HIGH, ls="--", lw=1.2, zorder=2)
    right = x[-1] + 2.5
    rng = f"{target[0]:g}-{target[1]:g}x"
    ax.text(right, high, f"{high:.1f}x: Ma'aden policy ceiling (top of {rng} target)", va="bottom", ha="right", fontsize=9,
            color=INK)
    ax.annotate(f"{low:.1f}x: inside the {rng} target", (right, low), xytext=(0, -3), textcoords="offset points", va="top",
                ha="right", fontsize=9, color=INK_2)
    ax.axvline(guidance / 1e3, color=INK_2, ls=":", lw=1.4, zorder=2)
    top = max(y.max() for y in curves.values())
    ax.text(guidance / 1e3, top, f" 2026 guidance {guidance / 1e3:.1f}bn, held flat (assumption)", va="top", ha="left",
            fontsize=9, color=INK_2)
    for i, c, l in points:
        above = l == high
        ax.plot(c / 1e3, l, "o", ms=8, color=SERIES[i], mec=SURFACE, mew=2, zorder=4)
        ax.annotate(f"{c / 1e3:.1f}", (c / 1e3, l), xytext=(-6, 7) if above else (7, -12), textcoords="offset points",
                    ha="right" if above else "left", fontsize=8.5, color=INK)
    ax.set_xlim(x[0], x[-1] + 2.6)
    ax.set_xlabel("Constant annual capex, 2026-2030 (SAR bn)", color=INK_2)
    ax.set_ylabel("Net debt / EBITDA at end-2030 (x)", color=INK_2)
    ax.set_title("End-2030 leverage against capex; markers show breakeven capex (SAR bn)", loc="left", color=INK, fontsize=11)
    ax.legend(loc="upper left", frameon=False, fontsize=9, title="FY25 EBITDA, held flat", title_fontsize=9,
              bbox_to_anchor=(0.0, 1.0))
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
