# Crescent–Vital Acquisition: Independent Technical Valuation Study

An asset-level technical valuation of Crescent Energy's ~$3.1Bn acquisition of Vital Energy
(announced Aug 2025, closed Dec 2025), built entirely from public data.

Standalone asset value of **~$3.15Bn** (inc. G\&A) aligns within ~1% of the $3.1Bn Crescent paid, 
while at SEC PV-10 of $3.75Bn (ex. G\&A) highlights ~$600M in standalone overhead synergy upside. Model baseline 
inputs reconcile 
cleanly to street consensus FY1 EBITDA, confirming operational accuracy. Value creation in the deal is driven by 
financial and corporate scale (G&A synergy capture, refinancing, and portfolio optimization) rather than a distressed 
discount on the underlying rock.

---

## What this project does

Rebuilds a full upstream A&D valuation workflow from scratch:

1. Pulled well level production from the Texas Railroad Commission (public).
2. Clean the data and splits multi-well leases into decline segments using python scripts.
3. Fit Arps decline curves to each segment and builds basin-level type curves.
4. Forecast 15 years of production (existing base + new drilling).
5. Runs a reserve based DCF to a PV-10, benchmarked against the actual deal
6. Run sensitivity analysis across oil price and decline assumptions.

Everything uses free public sources, no commercial reserve database was used for this project.

## Key results

| Metric | Value       |
|---|-------------|
| Independent PV-10 (SEC pricing, unhedged) | ~$3.15Bn     |
| Crescent transaction value | ~$3.1Bn      |
| Variance to price paid | ~1%         |
| FY1 EBITDA vs. street consensus | within 0.1% |
| Median decline-curve fit quality (R²) | 0.96        |

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
# ... for all scripts
```

## Key assumptions & limitations

- **Public lease-level data**, not commercial well-level allocation. Multi-well leases handled via segmentation.
- **Wells-per-pad = 4** is inferred, not measured — sensitized in the analysis.
- **Unhedged valuation**, consistent with SEC PV-10 convention.

## Author

Vandan Bhalala

M.Eng. Petroleum Engineering, Colorado School of Mines.

Built with Python and Excel as an independent A&D technical study.

## Disclaimer
*This is just an independent analysis using public data. Not investment advice. Not affiliated with
Crescent Energy, Vital Energy, or any financial institution.*
