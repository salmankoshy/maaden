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
