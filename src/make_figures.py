#!/usr/bin/env python3
"""Camera-ready figures for Hot Cities (same seed 42 as the paper; numbers unchanged).

Re-derives the seed-42 rasters via run_experiment and redraws Figure 1 at 300 dpi
(PNG) plus PDF/SVG. Does not overwrite summary.json / CSVs. If results/multi_seed.csv
exists, also redraws multi_seed_excess.{png,pdf,svg} in the same style.
"""
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_experiment as rx  # noqa: E402

R = rx.RESULTS
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7", "grey": "#BBBBBB"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})


def save(fig, stem):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(R / f"{stem}.{ext}", dpi=300)
    plt.close(fig)


def seed42():
    if hasattr(rx, "run_one"):
        r = rx.run_one(42)
        return r["lst"], r["stations"], r["heat"], r["blind"], r["blind_heat"], r["wards"]
    rx.RNG = np.random.default_rng(42)
    lst = rx.make_city_lst(); st = rx.place_stations(rx.GRID, rx.N_STATIONS)
    cov = rx.coverage_mask(lst.shape, st, rx.RADIUS); heat = lst >= np.percentile(lst, rx.HEAT_PCT)
    return lst, st, heat, ~cov, heat & ~cov, rx.ward_labels(rx.GRID, 4)


def city_map():
    lst, st, heat, blind, bh, wards = seed42()
    n = lst.shape[0]; k = int(wards.max()) + 1; kk = int(round(k ** 0.5)); bs = n // kk
    fig, axes = plt.subplots(1, 3, figsize=(6.2, 2.55), constrained_layout=True)

    # (a) LST + stations + buffers
    im = axes[0].imshow(lst, cmap="cividis", origin="upper")
    for y, x in st:
        axes[0].add_patch(Circle((x, y), rx.RADIUS, fill=False, ec="white", lw=0.7, ls="--"))
    axes[0].scatter(st[:, 1], st[:, 0], marker="^", s=22, c=OI["verm"], edgecolors="white", linewidths=0.6, zorder=3)
    cb = fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.02); cb.set_label("LST (°C, synthetic)")
    axes[0].set_title("(a) LST + stations (r=%g)" % rx.RADIUS)

    # (b) heat cells split by coverage
    cls = np.zeros_like(lst, dtype=int); cls[heat & ~blind] = 1; cls[heat & blind] = 2
    cmap = ListedColormap(["#F2F2F2", OI["sky"], OI["verm"]])
    axes[1].imshow(cls, cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    axes[1].scatter(st[:, 1], st[:, 0], marker="^", s=14, c="black", zorder=3)
    axes[1].set_title(f"(b) Heat cells (≥ p{rx.HEAT_PCT})")

    # (c) hot ∩ blind with ward grid + ids
    axes[2].imshow(np.where(bh, 1, 0), cmap=ListedColormap(["#F2F2F2", OI["verm"]]), vmin=0, vmax=1, interpolation="nearest")
    for i in range(1, kk):
        for ax in (axes[2],):
            ax.axhline(i * bs - 0.5, color="#555555", lw=0.6); ax.axvline(i * bs - 0.5, color="#555555", lw=0.6)
    for w in range(k):
        i, j = divmod(w, kk)
        axes[2].text(j * bs + 2, i * bs + 2, str(w), fontsize=9, color="#333333", va="top", ha="left")
    axes[2].set_title("(c) Hot ∩ blind + ward ids")

    for ax in axes:
        ax.set_xticks([0, n // 2, n - 1]); ax.set_yticks([0, n // 2, n - 1])
        ax.set_xlabel("x (cells)"); ax.set_ylabel("y (cells)")
    for ax in axes[1:]:
        ax.set_ylabel("")
    handles = [Line2D([], [], marker="^", ls="", color=OI["verm"], mec="white", ms=6, label="Station"),
               Line2D([], [], ls="--", color="#777777", label="Coverage buffer"),
               Patch(fc=OI["sky"], label="Hot & covered"),
               Patch(fc=OI["verm"], label="Hot & blind (no station in buffer)")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.16),
               handlelength=1.5, columnspacing=1.2)
    save(fig, "city_map")


def multi_seed():
    p = R / "multi_seed.csv"
    if not p.exists():
        return False
    s = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(4.2, 2.7), constrained_layout=True)
    ax.hist(s["excess_vs_null"], bins=8, color=OI["blue"], edgecolor="white")
    ax.axvline(0, ymax=0.7, color="black", ls="--", lw=1, label="no excess (0)")
    ax.axvline(s["excess_vs_null"].mean(), color=OI["verm"], ymax=0.7, lw=1.6, label=f"mean = {s['excess_vs_null'].mean():+.2f}")
    ax.set_xlabel("Excess vs placement null\n(observed − null uncovered-heat share)")
    ax.set_ylabel("Seeds (count)")
    ax.set_ylim(0, s["excess_vs_null"].value_counts(bins=8).max() * 1.5)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.legend(frameon=False, loc="upper center", ncol=2, handlelength=1.6, columnspacing=1.0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    save(fig, "multi_seed_excess")
    return True


if __name__ == "__main__":
    city_map()
    print("wrote city_map.{png,pdf,svg}; multi_seed:", multi_seed())
