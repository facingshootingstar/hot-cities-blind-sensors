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

## REAL_DATA steps (when network / API available)
1. Download OpenAQ measurements (temp/PM) for a city → `data/openaq_sample.csv`.
2. Fetch MODIS LST or ERA5-Land 2m temp for the same bbox → GeoTIFF / NetCDF under `data/`.
3. Regrid LST to analysis grid; mark station coverage; re-run metrics.
4. Document CRS, date range, and station IDs in `results/data_manifest.json`.

## Independence
Shares **no** code or data with `ghost-carbon` or `forest-lies-on-paper`.
