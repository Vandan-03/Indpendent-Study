import pandas as pd

# Script 4: calibrate the two things the forecast needs from real data,
# the basin production split and the new-pad IP, plus the drilling program
# reads 1) Cleaned Production.csv and 2) Arps Fits.csv

df = pd.read_csv("../Data/1) Cleaned Production.csv", parse_dates=["Date"])
fits = pd.read_csv("../Data/2) Arps Fits.csv")

# ----- basin production split -----
# i want the real split of where production is coming from right now, not just
# how many leases i picked. so i take the last 6 months and sum oil by basin.
recent_production = df[df["Date"] >= "2025-07-01"]
basin_split = recent_production.groupby("Basin")["Oil (BBL)"].sum()
print("Basin split (share of recent oil):")
print(basin_split / basin_split.sum())

# ----- new-pad IP calibration -----
# each segment's peak month, so i can keep only the recent wells
peak_idx = df.groupby("seg_id")["Oil (BBL)"].idxmax()
peaks = df.loc[peak_idx, ["seg_id", "Date"]].rename(columns={"Date": "peak_date"})

# put the peak dates onto the fits table
fits = fits.merge(peaks, on="seg_id", how="left")

# i only want recent, good-fit wells to represent a "new" pad, because that's
# what future drilling will actually look like. 2023 onward, and R2 above 0.8.
recent = fits[(fits["peak_date"] >= "2023-01-01") & (fits["r2"] > 0.8)].copy()

# qi is fitted in BBL per month, so divide by 30.4 to get BBL per day.
# then divide by 0.46 (oil is 46% of the stream) to gross up oil to total BOE.
recent["ip_bbl_d"] = recent["qi"] / 30.4
recent["ip_boe_d"] = recent["ip_bbl_d"] / 0.46

# ----- drilling program from Vital's own capital budget -----
# i don't want to guess how many wells they drill. i back it out of the money.

# what one well costs, straight from the 10-K
dc_capex_2024  = 873.637e6      # $ on oil & gas properties (10-K capital investments)
net_wells_2024 = 73.4          # net development wells completed (10-K drilling activity)
cost_per_well  = dc_capex_2024 / net_wells_2024        # about $11.9MM

# a lease in my data is usually a 4 well pad, so a pad costs 4 wells
WELLS_PER_PAD = 4              # assumption, not measured. flagged in the register.
pad_cost      = WELLS_PER_PAD * cost_per_well           # about $47.6MM

# how many pads that budget pays for
annual_budget  = 875e6         # midpoint of 10-K 2025 guidance ($825 to 925MM)
pads_per_month = annual_budget / (pad_cost * 12)        # about 1.53

# split the pads the same way production splits, 63 Midland / 37 Delaware
midland_pads   = pads_per_month * 0.63
delaware_pads  = pads_per_month * 0.37

print(f"\nCost per well:    ${cost_per_well/1e6:,.1f} MM")
print(f"Cost per pad:     ${pad_cost/1e6:,.1f} MM")
print(f"Pads per month:   {pads_per_month:.2f}  ({midland_pads:.2f} Midland / {delaware_pads:.2f} Delaware)")

# quick gut check, this should land near the 73.4 wells Vital actually drilled
print(f"Implied wells/yr: {pads_per_month * WELLS_PER_PAD * 12:.0f}  vs 73.4 actual in 2024")

# ----- report the IP numbers -----
print("\nSegments in calibration set:", len(recent))
print(f"Average IP: {recent['ip_bbl_d'].mean():,.0f} BBL/d oil")
print(f"Median  IP: {recent['ip_bbl_d'].median():,.0f} BBL/d oil")
print(recent.groupby("Basin")["ip_bbl_d"].agg(["count", "mean", "median"]).round(0))

print(f"\nAverage IP: {recent['ip_boe_d'].mean():,.0f} BOE/d total")
print(f"Median  IP: {recent['ip_boe_d'].median():,.0f} BOE/d total")
print(recent.groupby("Basin")["ip_boe_d"].agg(["count", "mean", "median"]).round(0))