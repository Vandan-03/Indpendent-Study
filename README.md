# Crescent–Vital Acquisition: Independent Technical Valuation

An asset-level technical valuation of Crescent Energy's ~$3.1B acquisition of Vital Energy
(announced Aug 2025, closed Dec 2025), built entirely from public data.

**Headline finding:** Independent PV-10 of **~$3.1B** lands within **~1%** of the ~$3.1B Crescent
paid, and the model reproduces street FY1 EBITDA within **0.1%** indicating the assets were
fairly priced. Value creation in the deal is financial (synergies, refinancing, divestitures),
not a distressed discount on the underlying rock.

---

## What this project does

Rebuilds a full upstream A&D valuation workflow from scratch:

1. Pulled well-level production from the Texas Railroad Commission (public).
2. Clean the data and splits multi-well leases into decline segments using python scripts.
3. Fit Arps decline curves to each segment and builds basin-level type curves.
4. Forecast 15 years of production (existing base + new drilling).
5. Runs a reserve based DCF to a PV-10, benchmarked against the actual deal
6. Run sensitivity analysis across oil price and decline assumptions.

Everything uses free public sources, no commercial reserve database was used for this project.

## Key results

| Metric | Value |
|---|---|
| Independent PV-10 (SEC pricing, unhedged) | ~$3.1B |
| Crescent transaction value | ~$3.1B |
| Variance to price paid | ~1% |
| FY1 EBITDA vs. street consensus | within 0.1% |
| Breakeven oil price (PV-10 = price paid) | ~$75/bbl WTI |
| Median decline-curve fit quality (R²) | 0.96 |

## Data sources

- **Texas Railroad Commission** — Production Data Query (well/lease-level oil & gas volumes)
- **SEC EDGAR** — Vital Energy FY2024 Form 10-K (reserves, costs, pricing, capital)
- **Crescent Energy investor materials** — deal terms, synergy and divestiture figures

## How to run

```bash
pip install pandas numpy scipy matplotlib openpyxl
# run scripts in order from the Scripts/ folder
python "1_clean_and_segment.py"
python "2_decline_curve_analysis.py"
# ... through 6 and 8
```

## Key assumptions & limitations

- **Public lease-level data**, not commercial well-level allocation. Multi-well leases handled via segmentation.
- **Wells-per-pad = 4** is inferred, not measured — sensitized in the analysis.
- **Unhedged valuation**, consistent with SEC PV-10 convention.

## Author

Vandan Bhalala

M.Eng. Petroleum Engineering, Colorado School of Mines.

Built with Python and Excel as an independent A&D technical study.

*This is just an independent analysis using public data. Not investment advice. Not affiliated with
Crescent Energy, Vital Energy, or any financial institution.*
