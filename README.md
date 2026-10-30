# Hot Cities, Blind Sensors — Heat Where the Map Is Empty

**VI:** Bản đồ nhiệt vệ tinh trông “đủ”, nhưng trạm mặt đất thưa — đo chỗ nắng nóng trùng vùng thiếu sensor (equity).

## Claim
Urban heat / LST maps from satellites look spatially complete, but ground stations are sparse. Heat extremes often coincide with **sensor missingness** — an equity gap invisible if you only trust the satellite grid.

## Research questions
- **RQ1:** What fraction of high-LST (top decile) cells have no ground station within a radius *r*?
- **RQ2:** Does heat–missingness overlap exceed a random-station null?
- **RQ3:** Which districts (synthetic wards) are hottest *and* blind?

## Method
**Default demo:** honest **synthetic city grid** (LST field + sparse stations) implementing coverage-gap vs heat-percentile metrics.
**REAL_DATA (optional):** OpenAQ temperature extracts + MODIS LST / ERA5-Land for a city bbox — see below.

## How to run
```bash
cd hot-cities-blind-sensors
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/run_experiment.py
```
Outputs: `results/heat_missingness.csv`, `results/city_map.png`, `results/summary.json`.

Kaggle (executed): https://www.kaggle.com/code/drowningcraft/hot-cities-heat-where-the-map-is-empty — `notebooks/hot_cities.ipynb` also runs seeds 42–51 and reproduces `results/multi_seed.csv` and `results/heat_missingness.csv` exactly.

## v4 extensions (`src/run_extended.py`)
```bash
python src/run_extended.py
```
Positive control and robustness, without changing any locked number (the `core` scenario at k=12, r=6, p90 reproduces `results/multi_seed.csv` exactly):
- **Placement scenarios** on the same synthetic city per seed: `core` (paper design), `uniform` (null-like), `periphery` (stations > 0.30n from the core centre).
- **Monte Carlo p-values** from the 200 null draws (`p_upper`: heat more blind than chance; `p_lower`: less blind).
- **Calibration / power** over 100 seeds (42–141): `results/ext_calibration.csv`.
- **One-at-a-time sensitivity** k ∈ {6, 24}, r ∈ {3, 9}, percentile ∈ {80, 95}: `results/ext_sensitivity.csv`.
- **Normalised ward score** (min-max ward LST × blind fraction): `results/ext_wards_seed42.csv`.

The `ext_*` files in `results/` were produced by the executed Kaggle run (notebook v4).

## REAL_DATA steps (when network / API available)
1. Download OpenAQ measurements (temp/PM) for a city → `data/openaq_sample.csv`.
2. Fetch MODIS LST or ERA5-Land 2m temp for the same bbox → GeoTIFF / NetCDF under `data/`.
3. Regrid LST to analysis grid; mark station coverage; re-run metrics.
4. Document CRS, date range, and station IDs in `results/data_manifest.json`.

## Independence
Shares **no** code or data with `ghost-carbon` or `forest-lies-on-paper`.

## Paper type & scope
Conference short paper presenting a **reproducible audit protocol**. *This paper presents a reproducible audit protocol demonstrated on synthetic/proxy data; a REAL_DATA path is documented for follow-on measurement, not claimed as completed observation.*

**Limitations:** synthetic/PROXY demo numbers only; REAL_DATA slice below is documented, not run; audit-metric contribution, not “first ever”; no journal-tier claim.

## Camera-ready figures
`python src/make_figures.py` → 300 dpi PNG + PDF + SVG in `results/` (same seeds/CSVs; numbers unchanged).

## REAL_DATA slice recipe (exact, not yet run)
One city slice: OpenAQ v3 locations API (temperature or PM2.5 stations) for a city bbox (e.g., Hanoi 20.9–21.15°N, 105.7–105.95°E) → `data/stations.csv`; MODIS MOD11A1 daytime LST (1 km) summer composite for the same bbox → GeoTIFF; regrid to 1 km; buffer r = 1–2 km; rerun the same metrics + 200-perm null + ward score using administrative wards; record CRS, dates, station ids in `results/data_manifest.json`.
