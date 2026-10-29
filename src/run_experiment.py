#!/usr/bin/env python3
"""Hot Cities: heat extremes vs ground-sensor missingness (synthetic demo + multi-seed)."""
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

GRID = 64
N_STATIONS = 12
RADIUS = 6.0
HEAT_PCT = 90
N_PERM = 200
SEEDS = list(range(42, 52))  # 10 seeds for conference-style uncertainty


def make_city_lst(rng: np.random.Generator, n: int = GRID) -> np.ndarray:
    yy, xx = np.mgrid[0:n, 0:n]
    core = 32 + 8 * np.exp(-((xx - n * 0.45) ** 2 + (yy - n * 0.5) ** 2) / (2 * 12**2))
    industrial = 5 * np.exp(-((xx - n * 0.75) ** 2 + (yy - n * 0.25) ** 2) / (2 * 6**2))
    park_cool = -4 * np.exp(-((xx - n * 0.3) ** 2 + (yy - n * 0.7) ** 2) / (2 * 8**2))
    noise = rng.normal(0, 0.4, size=(n, n))
    return gaussian_filter(core + industrial + park_cool + noise, sigma=1.0)


def place_stations(rng: np.random.Generator, n: int, n_stations: int) -> np.ndarray:
    coords = []
    for _ in range(n_stations):
        x = int(rng.normal(n * 0.4, n * 0.12))
        y = int(rng.normal(n * 0.55, n * 0.12))
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
    labels = np.zeros((n, n), dtype=int)
    bs = n // k
    wid = 0
    for i in range(k):
        for j in range(k):
            labels[i * bs : (i + 1) * bs, j * bs : (j + 1) * bs] = wid
            wid += 1
    return labels


def null_overlap(rng, heat_mask, radius, n_stations, n_perm=N_PERM) -> float:
    h, w = heat_mask.shape
    fracs = []
    for _ in range(n_perm):
        ys = rng.integers(0, h, size=n_stations)
        xs = rng.integers(0, w, size=n_stations)
        cov = coverage_mask(heat_mask.shape, np.column_stack([ys, xs]), radius)
        fracs.append((heat_mask & ~cov).sum() / max(heat_mask.sum(), 1))
    return float(np.mean(fracs))


def run_one(seed: int):
    rng = np.random.default_rng(seed)
    lst = make_city_lst(rng)
    stations = place_stations(rng, GRID, N_STATIONS)
    covered = coverage_mask(lst.shape, stations, RADIUS)
    thr = np.percentile(lst, HEAT_PCT)
    heat = lst >= thr
    blind = ~covered
    blind_heat = heat & blind
    frac_heat_blind = float(blind_heat.sum() / max(heat.sum(), 1))
    null_mean = null_overlap(rng, heat, RADIUS, N_STATIONS)
    excess = frac_heat_blind - null_mean
    wards = ward_labels(GRID, 4)
    scores = []
    for w in range(int(wards.max()) + 1):
        m = wards == w
        scores.append(float(lst[m].mean() * blind[m].mean()))
    top_ward = int(np.argmax(scores))
    return {
        "seed": seed,
        "frac_heat_cells_uncovered": frac_heat_blind,
        "frac_city_uncovered": float(blind.mean()),
        "null_mean_frac_heat_uncovered": null_mean,
        "excess_vs_null": excess,
        "lst_threshold_c": float(thr),
        "top_ward": top_ward,
        "top_ward_score": scores[top_ward],
        "lst": lst,
        "stations": stations,
        "heat": heat,
        "blind_heat": blind_heat,
        "wards": wards,
        "blind": blind,
    }


def main():
    multi = [run_one(s) for s in SEEDS]
    # Primary narrative seed remains 42 for figure continuity
    primary = next(r for r in multi if r["seed"] == 42)

    seed_rows = [
        {
            "seed": r["seed"],
            "frac_heat_cells_uncovered": r["frac_heat_cells_uncovered"],
            "null_mean_frac_heat_uncovered": r["null_mean_frac_heat_uncovered"],
            "excess_vs_null": r["excess_vs_null"],
            "top_ward": r["top_ward"],
            "top_ward_score": r["top_ward_score"],
        }
        for r in multi
    ]
    sdf = pd.DataFrame(seed_rows)
    sdf.to_csv(RESULTS / "multi_seed.csv", index=False)

    lst, stations = primary["lst"], primary["stations"]
    heat, blind, blind_heat = primary["heat"], primary["blind"], primary["blind_heat"]
    wards = primary["wards"]
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
        "primary_seed": 42,
        "n_seeds": len(SEEDS),
        "n_perm": N_PERM,
        "lst_threshold_c": primary["lst_threshold_c"],
        "frac_heat_cells_uncovered": primary["frac_heat_cells_uncovered"],
        "frac_city_uncovered": primary["frac_city_uncovered"],
        "null_mean_frac_heat_uncovered": primary["null_mean_frac_heat_uncovered"],
        "excess_vs_null": primary["excess_vs_null"],
        "excess_mean_10seeds": float(sdf["excess_vs_null"].mean()),
        "excess_std_10seeds": float(sdf["excess_vs_null"].std(ddof=1)),
        "frac_heat_uncovered_mean_10seeds": float(sdf["frac_heat_cells_uncovered"].mean()),
        "frac_heat_uncovered_std_10seeds": float(sdf["frac_heat_cells_uncovered"].std(ddof=1)),
        "frac_seeds_excess_negative": float((sdf["excess_vs_null"] < 0).mean()),
        "note": "Replace with OpenAQ + MODIS/ERA5 per README REAL_DATA",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(df.head().to_string(index=False))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    im0 = axes[0].imshow(lst, cmap="inferno")
    axes[0].scatter(stations[:, 1], stations[:, 0], c="cyan", s=40, marker="^", label="stations")
    axes[0].set_title("Synthetic LST + stations (seed 42)")
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

    fig2, ax = plt.subplots(figsize=(5.5, 3.5))
    ax.hist(sdf["excess_vs_null"], bins=8, color="steelblue", edgecolor="white")
    ax.axvline(0, color="black", ls="--", lw=1)
    ax.axvline(summary["excess_mean_10seeds"], color="crimson", lw=1.5, label="mean")
    ax.set_xlabel("excess vs null (observed − null)")
    ax.set_ylabel("count (seeds)")
    ax.set_title("Multi-seed excess distribution (n=10)")
    ax.legend()
    fig2.tight_layout()
    fig2.savefig(RESULTS / "multi_seed_excess.png", dpi=120)
    plt.close()
    print(f"Wrote results under {RESULTS}")


if __name__ == "__main__":
    main()
