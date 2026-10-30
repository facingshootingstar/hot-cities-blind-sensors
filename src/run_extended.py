#!/usr/bin/env python3
"""Hot Cities v4 extensions: placement scenarios (positive control), Monte Carlo
p-values, null calibration, one-at-a-time sensitivity, normalised ward score.

Self-contained (also pasted verbatim into the Kaggle notebook). The "core"
scenario at the baseline config reproduces results/multi_seed.csv exactly:
same RNG call order as src/run_experiment.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:  # running inside a notebook
    ROOT = Path(".")
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

GRID = 64
BASE = dict(k=12, r=6.0, pct=90)
N_PERM = 200
SEEDS = list(range(42, 52))          # narrative seeds, as in the paper
CAL_SEEDS = list(range(42, 142))     # 100 seeds for calibration / power
SCENARIOS = ["core", "uniform", "periphery"]
CORE_C = (0.45, 0.50)                # urban-core centre (x, y) as fraction of n
PERIPH_MIN_DIST = 0.30               # periphery stations: > 0.30n from core centre

_n = GRID
_YY, _XX = np.mgrid[0:_n, 0:_n]


def make_city_lst(rng, n=GRID):
    yy, xx = np.mgrid[0:n, 0:n]
    core = 32 + 8 * np.exp(-((xx - n * 0.45) ** 2 + (yy - n * 0.5) ** 2) / (2 * 12**2))
    industrial = 5 * np.exp(-((xx - n * 0.75) ** 2 + (yy - n * 0.25) ** 2) / (2 * 6**2))
    park_cool = -4 * np.exp(-((xx - n * 0.3) ** 2 + (yy - n * 0.7) ** 2) / (2 * 8**2))
    noise = rng.normal(0, 0.4, size=(n, n))
    return gaussian_filter(core + industrial + park_cool + noise, sigma=1.0)


def place_core(rng, n, k):
    coords = []
    for _ in range(k):
        x = int(rng.normal(n * 0.4, n * 0.12))
        y = int(rng.normal(n * 0.55, n * 0.12))
        coords.append((int(np.clip(y, 0, n - 1)), int(np.clip(x, 0, n - 1))))
    return np.array(coords, dtype=int)


def place_uniform(rng, n, k):
    return np.column_stack([rng.integers(0, n, size=k), rng.integers(0, n, size=k)])


def place_periphery(rng, n, k):
    coords = []
    while len(coords) < k:
        y, x = int(rng.integers(0, n)), int(rng.integers(0, n))
        if np.hypot(x - n * CORE_C[0], y - n * CORE_C[1]) > PERIPH_MIN_DIST * n:
            coords.append((y, x))
    return np.array(coords, dtype=int)


PLACERS = dict(core=place_core, uniform=place_uniform, periphery=place_periphery)


def coverage_mask(stations, r):
    s = np.asarray(stations)
    d2 = (_YY[None] - s[:, 0, None, None]) ** 2 + (_XX[None] - s[:, 1, None, None]) ** 2
    return (d2 <= r**2).any(axis=0)


WARDS = np.zeros((_n, _n), dtype=int)
_bs = _n // 4
for _i in range(4):
    for _j in range(4):
        WARDS[_i * _bs:(_i + 1) * _bs, _j * _bs:(_j + 1) * _bs] = _i * 4 + _j


def audit(seed, scenario="core", k=12, r=6.0, pct=90, n_perm=N_PERM):
    rng = np.random.default_rng(seed)
    lst = make_city_lst(rng)
    stations = PLACERS[scenario](rng, GRID, k)
    blind = ~coverage_mask(stations, r)
    heat = lst >= np.percentile(lst, pct)
    nh = max(heat.sum(), 1)
    b_h = float((heat & blind).sum() / nh)
    null = np.empty(n_perm)
    for i in range(n_perm):
        ys = rng.integers(0, GRID, size=k)
        xs = rng.integers(0, GRID, size=k)
        null[i] = (heat & ~coverage_mask(np.column_stack([ys, xs]), r)).sum() / nh
    # wards: raw score (paper) and min-max normalised LST score
    lw = np.array([lst[WARDS == w].mean() for w in range(16)])
    fb = np.array([blind[WARDS == w].mean() for w in range(16)])
    raw = lw * fb
    norm = (lw - lw.min()) / (lw.max() - lw.min()) * fb
    return dict(
        seed=seed, scenario=scenario, k=k, r=r, pct=pct,
        B_h=b_h, null_mean=float(null.mean()),
        null_q025=float(np.quantile(null, 0.025)), null_q975=float(np.quantile(null, 0.975)),
        E=b_h - float(null.mean()),
        p_upper=float((1 + (null >= b_h).sum()) / (n_perm + 1)),  # heat MORE blind than chance
        p_lower=float((1 + (null <= b_h).sum()) / (n_perm + 1)),  # heat LESS blind than chance
        top_ward_raw=int(raw.argmax()), top_ward_norm=int(norm.argmax()),
        _ward=dict(lw=lw, fb=fb, raw=raw, norm=norm),
    )


def strip(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main():
    # 1) scenarios x narrative seeds
    sc = [audit(s, sn) for sn in SCENARIOS for s in SEEDS]
    sc_df = pd.DataFrame([strip(d) for d in sc])
    sc_df.to_csv(RESULTS / "ext_scenarios.csv", index=False)

    # 2) calibration / power over 100 seeds
    cal = pd.DataFrame([strip(audit(s, sn)) for sn in SCENARIOS for s in CAL_SEEDS])
    cal.to_csv(RESULTS / "ext_calibration_raw.csv", index=False)
    cal_sum = cal.groupby("scenario").agg(
        E_mean=("E", "mean"), E_sd=("E", "std"),
        frac_E_pos=("E", lambda e: float((e > 0).mean())),
        rate_p_upper_05=("p_upper", lambda p: float((p < 0.05).mean())),
        rate_p_lower_05=("p_lower", lambda p: float((p < 0.05).mean())),
    ).reindex(SCENARIOS)
    cal_sum.to_csv(RESULTS / "ext_calibration.csv")

    # 3) one-at-a-time sensitivity (core + periphery, narrative seeds)
    grid = [("baseline", None)] + [("k", v) for v in (6, 24)] + [("r", v) for v in (3.0, 9.0)] \
        + [("pct", v) for v in (80, 95)]
    rows = []
    for factor, val in grid:
        cfg = dict(BASE) if val is None else {**BASE, factor: val}
        for sn in ("core", "periphery"):
            es = np.array([audit(s, sn, **cfg)["E"] for s in SEEDS])
            rows.append(dict(factor=factor, value=cfg[factor] if val is not None else "-",
                             scenario=sn, E_mean=es.mean(), E_sd=es.std(ddof=1),
                             frac_E_neg=float((es < 0).mean()), frac_E_pos=float((es > 0).mean())))
    sens = pd.DataFrame(rows)
    sens.to_csv(RESULTS / "ext_sensitivity.csv", index=False)

    # 4) normalised ward score, seed 42 core
    w42 = next(d for d in sc if d["seed"] == 42 and d["scenario"] == "core")["_ward"]
    wdf = pd.DataFrame(dict(ward=range(16), mean_lst=w42["lw"], frac_blind=w42["fb"],
                            S_raw=w42["raw"], S_norm=w42["norm"])).sort_values("S_norm", ascending=False)
    wdf.to_csv(RESULTS / "ext_wards_seed42.csv", index=False)

    core = sc_df[sc_df.scenario == "core"]
    summary = dict(
        mode="SYNTHETIC_city_grid_v4_extensions",
        n_perm=N_PERM, seeds=SEEDS, calibration_seeds=f"{CAL_SEEDS[0]}-{CAL_SEEDS[-1]}",
        periphery_min_dist_frac=PERIPH_MIN_DIST,
        scenarios_10seeds={sn: dict(
            E_mean=float(g.E.mean()), E_sd=float(g.E.std(ddof=1)),
            B_h_mean=float(g.B_h.mean()), frac_E_pos=float((g.E > 0).mean()),
            n_p_upper_05=int((g.p_upper < 0.05).sum()), n_p_lower_05=int((g.p_lower < 0.05).sum()))
            for sn, g in sc_df.groupby("scenario")},
        calibration_100seeds=cal_sum.reset_index().to_dict(orient="records"),
        core_top_ward_raw_counts={int(k): int(v) for k, v in core.top_ward_raw.value_counts().items()},
        core_top_ward_norm_counts={int(k): int(v) for k, v in core.top_ward_norm.value_counts().items()},
    )
    (RESULTS / "ext_summary.json").write_text(json.dumps(summary, indent=2))

    # figure: E by scenario over 100 seeds
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    rng = np.random.default_rng(0)
    for i, sn in enumerate(SCENARIOS):
        e = cal.loc[cal.scenario == sn, "E"].to_numpy()
        ax.scatter(e, i + rng.uniform(-0.15, 0.15, e.size), s=10, alpha=0.6)
        ax.plot([e.mean()] * 2, [i - 0.3, i + 0.3], color="black", lw=1.5)
    ax.axvline(0, color="gray", ls="--", lw=1)
    ax.set_yticks(range(len(SCENARIOS)), ["core-biased", "uniform (null)", "periphery-biased"])
    ax.set_xlabel("Excess E = $B_h$ − null mean (100 seeds)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(RESULTS / f"ext_scenarios.{ext}", dpi=300)
    plt.close(fig)

    pd.set_option("display.width", 200)
    print(sc_df.drop(columns=["k", "r", "pct"]).round(4).to_string(index=False))
    print(cal_sum.round(4).to_string())
    print(sens.round(4).to_string(index=False))
    print(wdf.round(3).to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
