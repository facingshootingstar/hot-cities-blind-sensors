## 2. Hot Cities, Blind Sensors

**Title:** Heat Where the Map Is Empty? Satellite LST Meets Sparse Ground Sensors

**Subtitle:** A complete heat map is not a monitored city — but blindness has to be measured, not assumed

**Abstract.**
Satellite land-surface temperature (LST) maps look spatially complete; ground stations do not. On this synthetic seed (64×64, 12 stations), **46%** of top-decile heat cells lack a station buffer, but excess vs permutation null is **-0.24** (heat lies nearer stations than chance); ward-level heat×blindness scores still flag priorities (e.g. ward 6)—so a complete LST map is not the same as monitored heat where coverage fails. Unlike SUHI-vs-CUHI comparisons or IoT gap-filling studies, we audit where the hottest LST cells fall relative to station coverage, against a placement null. REAL_DATA path: OpenAQ + MODIS/ERA5 (README).

**Keywords:** urban heat island, sensor equity, LST, OpenAQ, permutation null

**Contribution.** We contribute an *audit metric* pairing top-decile LST heat with station-buffer blindness, tested against a permutation null and summarized at ward level—without assuming heat lives in sensor deserts.

**Related work & positioning.**
Satellite LST is widely used to fill data gaps where ground stations are sparse, particularly in the Global South, and surface-UHI reviews document both its reach and its limits (Zhou et al., 2019). LST is not air-temperature hazard: Venter, Chakraborty & Lee (2021) find satellite SUHI about six times canopy-air CUHI across 342 European cities, and Zhan et al. (arXiv:2509.16568) argue that LST strongly mischaracterises urban heat hazard. Station placement is itself biased: citizen weather stations cluster in built-up urban areas while national stations favour rural sites (Sakthivel & Sengupta, 2025), and dense IoT networks reveal heat that reference stations miss (Aida et al., 2025, Seoul S-DoT). Gap: in our search we found no audit pairing top-decile heat with station buffers under a permutation null plus a ward heat×blind score, reported even when the null fails.

- **Not the same as Venter et al. (2021) / Zhan et al. (2025):** we do not re-estimate SUHI vs CUHI or argue LST vs air temperature; we treat LST only as a heat-ranking layer and audit monitoring coverage of its top decile.
- **Not the same as Aida et al. (2025):** they quantify heat missed by reference stations using a dense IoT network; we quantify the blindness share and its excess over a placement null as audit metrics, on a synthetic city first.
- **Not the same as placement-bias studies (Sakthivel & Sengupta, 2025):** they show where stations sit and how that biases UHI intensity; we test whether the hottest cells are less covered than random placement would give, and in this draw they are not.

**References.**
1. Venter, Z. S., Chakraborty, T., Lee, X. (2021). Crowdsourced air temperatures contrast satellite measures of the urban heat island and its mechanisms. Science Advances 7(22), eabb9569. https://www.science.org/doi/10.1126/sciadv.abb9569
2. Zhan, W., Bechtel, B., et al. (2025). Satellite-derived Land Surface Temperatures Strongly Mischaracterise Urban Heat Hazard. arXiv:2509.16568. https://arxiv.org/abs/2509.16568
3. Aida, A., Park, C., Jeon, J.-J., Choi, J. (2025). Quantifying undetected urban heat: Identifying monitoring gaps using public urban IoT sensor network. J. Climate Change Research 16(5-1), 739–763. https://doi.org/10.15531/KSCCR.2025.16.5.739
4. Sakthivel, P., Sengupta, R. (2025). Spatial bias in placement of citizen and conventional weather stations and their impact on urban climate research: A case study of the Urban Heat Island effect in Canada. Urban Climate 59, 102280. https://www.sciencedirect.com/science/article/pii/S2212095524004772
5. Zhou, D., Xiao, J., Bonafoni, S., et al. (2019). Satellite Remote Sensing of Surface Urban Heat Islands: Progress, Challenges, and Perspectives. Remote Sensing 11(1), 48. https://doi.org/10.3390/rs11010048

**Scope note:** SYNTHETIC city grid, single seed; excess vs null is negative (-0.239).
