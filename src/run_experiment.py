#!/usr/bin/env python3
"""Hot Cities: heat extremes vs ground-sensor missingness (synthetic demo)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)
GRID = 64
N_STATIONS = 12
RADIUS = 6.0  # cells
HEAT_PCT = 90


def make_city_lst(n: int = GRID) -> np.ndarray:
    """Synthetic urban LST: warm core + parks + industrial spike."""
    yy, xx = np.mgrid[0:n, 0:n]
    core = 32 + 8 * np.exp(-((xx - n * 0.45) ** 2 + (yy - n * 0.5) ** 2) / (2 * 12**2))
    industrial = 5 * np.exp(-((xx - n * 0.75) ** 2 + (yy - n * 0.25) ** 2) / (2 * 6**2))
    park_cool = -4 * np.exp(-((xx - n * 0.3) ** 2 + (yy - n * 0.7) ** 2) / (2 * 8**2))
    noise = RNG.normal(0, 0.4, size=(n, n))
    lst = gaussian_filter(core + industrial + park_cool + noise, sigma=1.0)
    return lst


def place_stations(n: int, n_stations: int) -> np.ndarray:
    """Bias stations toward cooler / central 'downtown' — equity skew."""
    coords = []
    for _ in range(n_stations):
        # prefer left-center (not industrial SE)
        x = int(RNG.normal(n * 0.4, n * 0.12))
        y = int(RNG.normal(n * 0.55, n * 0.12))
        x = int(np.clip(x, 0, n - 1))
        y = int(np.clip(y, 0, n - 1))
        coords.append((y, x))
    return np.array(coords, dtype=int)


def coverage_mask(shape, stations, radius: float) -> np.ndarray:
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    covered = np.zeros(shape, dtype=bool)
    for y, x in stations:
        covered |= (yy - y) ** 2 + (xx - x) ** 2 <= radius**2
    return covered


def ward_labels(n: int, k: int = 4) -> np.ndarray:
    """k×k block wards."""
    labels = np.zeros((n, n), dtype=int)
    bs = n // k
    wid = 0
    for i in range(k):
        for j in range(k):
            labels[i * bs : (i + 1) * bs, j * bs : (j + 1) * bs] = wid
            wid += 1
    return labels


def null_overlap(lst, heat_mask, radius, n_stations, n_perm=200) -> float:
    h, w = lst.shape
    fracs = []
    for _ in range(n_perm):
        ys = RNG.integers(0, h, size=n_stations)
        xs = RNG.integers(0, w, size=n_stations)
        cov = coverage_mask(lst.shape, np.column_stack([ys, xs]), radius)
        blind_heat = heat_mask & ~cov
        fracs.append(blind_heat.sum() / max(heat_mask.sum(), 1))
    return float(np.mean(fracs))


def main():
    lst = make_city_lst()
    stations = place_stations(GRID, N_STATIONS)
    covered = coverage_mask(lst.shape, stations, RADIUS)
    thr = np.percentile(lst, HEAT_PCT)
    heat = lst >= thr
    blind = ~covered
    blind_heat = heat & blind

    frac_heat_blind = float(blind_heat.sum() / max(heat.sum(), 1))
    frac_city_blind = float(blind.mean())
    null_mean = null_overlap(lst, heat, RADIUS, N_STATIONS)

    wards = ward_labels(GRID, 4)
    rows = []
    for w in range(int(wards.max()) + 1):
        m = wards == w
        rows.append(
            {
                "ward": w,
                "mean_lst": float(lst[m].mean()),
                "frac_blind": float(blind[m].mean()),
                "frac_heat": float(heat[m].mean()),
                "frac_blind_and_heat": float((blind_heat & m).sum() / m.sum()),
                "hot_blind_score": float(lst[m].mean() * blind[m].mean()),
            }
        )
    df = pd.DataFrame(rows).sort_values("hot_blind_score", ascending=False)
    df.to_csv(RESULTS / "heat_missingness.csv", index=False)

    summary = {
        "mode": "SYNTHETIC_city_grid",
        "grid": GRID,
        "n_stations": N_STATIONS,
        "radius_cells": RADIUS,
        "heat_percentile": HEAT_PCT,
        "lst_threshold_c": float(thr),
        "frac_heat_cells_uncovered": frac_heat_blind,
        "frac_city_uncovered": frac_city_blind,
        "null_mean_frac_heat_uncovered": null_mean,
        "excess_vs_null": frac_heat_blind - null_mean,
        "note": "Replace with OpenAQ + MODIS/ERA5 per README REAL_DATA",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(df.head().to_string(index=False))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    im0 = axes[0].imshow(lst, cmap="inferno")
    axes[0].scatter(stations[:, 1], stations[:, 0], c="cyan", s=40, marker="^", label="stations")
    axes[0].set_title("Synthetic LST + stations")
    axes[0].legend(loc="upper right", fontsize=7)
    plt.colorbar(im0, ax=axes[0], fraction=0.046)
    axes[1].imshow(heat, cmap="Reds")
    axes[1].set_title(f"Heat ≥ p{HEAT_PCT}")
    axes[2].imshow(blind_heat, cmap="Purples")
    axes[2].set_title("Blind ∩ heat (equity gap)")
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(RESULTS / "city_map.png", dpi=120)
    plt.close()
    print(f"Wrote {RESULTS / 'heat_missingness.csv'}, city_map.png, summary.json")


if __name__ == "__main__":
    main()
