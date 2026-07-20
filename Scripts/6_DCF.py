import pandas as pd
import numpy as np

# Script 6: turn the production forecast into dollars and discount to PV-10
# reads 3) Production Forecast.csv, writes 4) DCF Output.csv and 5) Monthly boepd.csv

fc = pd.read_csv("../Data/3) Production Forecast.csv")

# ----- revenue: split each BOE into oil, NGL, gas and price each stream -----
DAYS = 30.4
mix = {"oil": 0.46, "ngl": 0.27, "gas": 0.27}          # production mix from Vital's 10-K
px  = {"oil": 76.76, "ngl": 13.66, "gas": 0.85}        # SEC realized prices from Vital's 10-K

fc["BOE / month"] = fc["Total (BOE/d)"] * DAYS

fc["Revenue Oil"] = fc["BOE / month"] * mix["oil"] * px["oil"]
fc["Revenue NGL"] = fc["BOE / month"] * mix["ngl"] * px["ngl"]
fc["Revenue Gas"] = fc["BOE / month"] * mix["gas"] * 6 * px["gas"]   # gas BOE back to Mcf, then price
fc["Revenue"] = fc[["Revenue Oil", "Revenue NGL", "Revenue Gas"]].sum(axis=1)

print(f"Month 0 Revenue: ${fc['Revenue'][0]/1e6:,.1f} MM")
print(f"Year 1 Revenue:  ${fc['Revenue'][:12].sum()/1e6:,.0f} MM")
print(f"Implied $/BOE:   ${fc['Revenue'][0]/fc['BOE / month'][0]:.2f}")

# ----- opex: two cost stacks, because EBITDA and SEC PV-10 define costs differently -----
# EBITDA includes G&A (it's an operating cost). SEC PV-10 excludes corporate G&A
# (it values the reserves, not the head office). so i keep both.
production_costs_per_boe = 9.15 + 2.41 + 0.92 + 0.36     # LOE + prod tax + transport + GPT = 12.84
ga_per_boe = 1.75                                         # cash G&A, ex LTIP and transaction costs
total_opex = production_costs_per_boe + ga_per_boe        # 14.59, the full stack

fc["OPEX"] = fc["BOE / month"] * total_opex
fc["EBITDA"] = fc["Revenue"] - fc["OPEX"]                 # EBITDA uses the FULL stack

print(f"Production costs: ${production_costs_per_boe:.2f}/BOE   G&A: ${ga_per_boe:.2f}/BOE")
print(f"Year 1 EBITDA: ${fc['EBITDA'][:12].sum()/1e6:,.0f} MM")   # should read ~$1,349MM again

# ----- capex: the cost of the drilling program, only while drilling runs -----
PAD_COST = 47.6e6          # ~4 wells x $11.9MM (10-K: $873.6MM / 73.4 net wells)
PADS_PER_MONTH = 1.53      # calibrated to the ~$875MM/yr capital budget
DRILL_MONTHS = 120

fc["CAPEX"] = 0.0
fc.loc[fc["Month"] < DRILL_MONTHS, "CAPEX"] = PADS_PER_MONTH * PAD_COST

# net operating cash flow, pre-tax, after capex. not textbook FCF (no taxes,
# no working capital), so i don't call it that.
fc["Net Operating Cash Flow"] = fc["EBITDA"] - fc["CAPEX"]

# the SEC PV-10 version excludes G&A, so a second cash line without it
fc["SEC Net Cash Flow"] = fc["Revenue"] - fc["BOE / month"] * production_costs_per_boe - fc["CAPEX"]

print(f"Annual CAPEX (yrs 1-10): ${fc['CAPEX'][:12].sum()/1e6:,.0f} MM")
print(f"Year 1 Net Operating Cash Flow: ${fc['Net Operating Cash Flow'][:12].sum()/1e6:,.0f} MM")
print(f"Year 11 Net Operating Cash Flow (no drilling): ${fc['Net Operating Cash Flow'][120:132].sum()/1e6:,.0f} MM")

# ----- discount every month's cash back to today at 10%/yr -----
r_annual = 0.10          # SEC standard rate
r_month = (1 + r_annual) ** (1/12) - 1          # the same 10%/yr as a monthly rate

fc["Discount Factor"] = 1 / (1 + r_month) ** (fc["Month"] + 0.5)
fc["PV (all-in)"] = fc["Net Operating Cash Flow"] * fc["Discount Factor"]
fc["PV (SEC)"]    = fc["SEC Net Cash Flow"] * fc["Discount Factor"]

pv_allin = fc["PV (all-in)"].sum()
pv_sec   = fc["PV (SEC)"].sum()
fc.to_csv("../Data/4) DCF Output.csv", index=False)

DEAL_PRICE = 3.1e9   # what Crescent actually paid, my benchmark

print(f"\nSEC PV-10 (ex G&A):            ${pv_sec/1e9:,.2f} BN")
print(f"All-in asset value (incl G&A): ${pv_allin/1e9:,.2f} BN")
print(f"Crescent paid:                 ${DEAL_PRICE/1e9:,.2f} BN")
print(f"All-in vs price paid:          ${(pv_allin - DEAL_PRICE)/1e9:,.2f} BN")