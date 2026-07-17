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

# ----- opex: all the per-BOE operating costs from the 10-K -----
opex_per_boe = {
    "loe": 9.15,          # lease operating expense
    "prod_tax": 2.41,     # production & ad valorem taxes
    "oil_transport": 0.92,
    "gpt": 0.36,          # gas gathering, processing & transport
    "ga": 1.75,           # cash G&A, excludes LTIP and transaction costs
}
total_opex = sum(opex_per_boe.values())

fc["OPEX"] = fc["BOE / month"] * total_opex
fc["EBITDA"] = fc["Revenue"] - fc["OPEX"]

print(f"Total OPEX: ${total_opex:.2f}/BOE")
print(f"Margin:     ${fc['Revenue'][0]/fc['BOE / month'][0] - total_opex:.2f}/BOE")
print(f"Year 1 EBITDA: ${fc['EBITDA'][:12].sum()/1e6:,.0f} MM")

# ----- capex: the cost of the drilling program, only while drilling runs -----
PAD_COST = 47.6e6          # ~4 wells x $11.9MM (10-K: $873.6MM / 73.4 net wells)
PADS_PER_MONTH = 1.53      # calibrated to the ~$875MM/yr capital budget
DRILL_MONTHS = 120

fc["CAPEX"] = 0.0
fc.loc[fc["Month"] < DRILL_MONTHS, "CAPEX"] = PADS_PER_MONTH * PAD_COST

fc["Free Cash Flow"] = fc["EBITDA"] - fc["CAPEX"]

print(f"Annual CAPEX (yrs 1-10): ${fc['CAPEX'][:12].sum()/1e6:,.0f} MM")
print(f"Year 1 Free Cash Flow: ${fc['Free Cash Flow'][:12].sum()/1e6:,.0f} MM")
print(f"Year 11 Free Cash Flow (no drilling): ${fc['Free Cash Flow'][120:132].sum()/1e6:,.0f} MM")

# ----- discount every month's cash back to today at 10%/yr -----
r_annual = 0.10          # SEC standard rate
r_month = (1 + r_annual) ** (1/12) - 1          # the same 10%/yr as a monthly rate

# +0.5 is the mid-month convention, cash arrives through the month not on day 1
fc["Discount Factor"] = 1 / (1 + r_month) ** (fc["Month"] + 0.5)
fc["PV"] = fc["Free Cash Flow"] * fc["Discount Factor"]

PV10 = fc["PV"].sum()   # add up all the discounted months
fc.to_csv("../Data/4) DCF Output.csv", index=False)

print(f"\nPV-10 (unhedged, SEC pricing): ${PV10/1e9:,.2f} BN")
print(f"Crescent implied EV for Vital:  $2.90 BN")
print(f"Implied discount to asset value: ${(PV10 - 2.9e9)/1e9:,.2f} BN")

fc[["Month", "Total (BOE/d)"]].to_csv("../Data/5) Monthly boepd.csv", index=False)