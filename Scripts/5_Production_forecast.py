import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# Script 5: forecast company production for 15 years, existing base plus new drilling
# reads 1) Cleaned Production.csv, writes 3) Production Forecast.csv

# ----- how old is Vital's producing base right now -----
df = pd.read_csv("../Data/1) Cleaned Production.csv", parse_dates=["Date"])
df = df[df["Date"] < "2026-01-01"]

peak_idx = df.groupby("seg_id")["Oil (BBL)"].idxmax()
peaks = df.loc[peak_idx, ["seg_id", "Date"]].rename(columns={"Date": "peak_date"})

# each segment's current rate, i use the last 3 months so recent wells count more
last3 = (df.sort_values("Date").groupby("seg_id").tail(3)
           .groupby("seg_id")["Oil (BBL)"].mean().rename("recent_rate"))

age = peaks.merge(last3, on="seg_id")
asof = pd.Timestamp("2025-12-15")   # deal close date
age["age_months"] = (asof - age["peak_date"]).dt.days / 30.4

# weight each segment's age by its current rate, so the answer reflects where the
# barrels actually come from today, not just a plain average of wells
w_age = np.average(age["age_months"], weights=age["recent_rate"])
print(f"Production-weighted average age of base: {w_age:.1f} months")
print(f"Simple average age: {age['age_months'].mean():.1f} months")

# ----- modified Arps, hyperbolic early then a flat terminal decline -----
# a plain hyperbolic never really dies, which isn't real. so once the decline
# rate slows to 8%/yr i switch to a constant exponential decline.
def modified_arps(t, qi, Di, b, Dterm_annual=0.08):
    Dterm_m = 1 - (1 - Dterm_annual) ** (1/12)          # 8%/yr as a monthly rate
    t_sw = max((Di / Dterm_m - 1) / (b * Di), 0.0)       # the month it switches over
    t = np.asarray(t, dtype=float)
    q_hyp = qi / (1 + b * Di * t) ** (1 / b)
    q_sw = qi / (1 + b * Di * t_sw) ** (1 / b)           # rate at the switch point
    q_exp = q_sw * np.exp(-Dterm_m * (t - t_sw))
    return np.where(t <= t_sw, q_hyp, q_exp), t_sw

# check when each basin hits terminal decline
_, t_sw_mid = modified_arps(np.arange(1), 1.0, 0.334, 1.2)
_, t_sw_del = modified_arps(np.arange(1), 0.981, 0.228, 0.963)
print(f"Midland  switch month: {t_sw_mid:.0f}  (~{t_sw_mid/12:.1f} years)")
print(f"Delaware switch month: {t_sw_del:.0f}  (~{t_sw_del/12:.1f} years)")

# ----- the 15 year company forecast -----
H = 180                                    # 15 years in months
t_future = np.arange(H)

base_total = 138_000                       # BOE/d at close, from the deal metrics
midland_share = 0.63                       # measured production split
basins = {
    "Midland":  {"share": midland_share,      "Di": 0.334, "b": 1.20},
    "Delaware": {"share": 1 - midland_share,  "Di": 0.228, "b": 0.963},
}
base_age = 32.8                            # from the block above

# Machine 1: the existing base. i don't start it at t=0, i start it at age 32.8,
# because these wells are already ~3 years old. rescaling makes the forecast begin
# at today's actual rate and only borrow the curve's slope from here on.
base = np.zeros(H)
for name, p in basins.items():
    q0 = base_total * p["share"]
    shape, _ = modified_arps(base_age + t_future, 1.0, p["Di"], p["b"])
    shape_at_age, _ = modified_arps(np.array([base_age]), 1.0, p["Di"], p["b"])
    base += q0 * shape / shape_at_age[0]

# Machine 2: new pads stacking on top. each monthly batch of pads starts its own
# curve at t=0 and declines from there. drilling runs for 10 years then stops.
drill_months = 120

pad_program = {
    "Midland":  {"pads_per_month": 0.96, "ip": 4191, "Di": 0.334, "b": 1.20},
    "Delaware": {"pads_per_month": 0.57, "ip": 2874, "Di": 0.228, "b": 0.96},
}

wedge_by_basin = {name: np.zeros(H) for name in pad_program}
for name, p in pad_program.items():
    for m in range(drill_months):
        shape, _ = modified_arps(t_future[: H - m], 1.0, p["Di"], p["b"])
        wedge_by_basin[name][m:] += p["pads_per_month"] * p["ip"] * shape

wedges = wedge_by_basin["Midland"] + wedge_by_basin["Delaware"]

total = base + wedges
fc = pd.DataFrame({"Month": t_future,
                   "PDP Base (BOE/d)": base,
                   "Midland new pads (BOE/d)": wedge_by_basin["Midland"],
                   "Delaware new pads (BOE/d)": wedge_by_basin["Delaware"],
                   "New pads total (BOE/d)": wedges,
                   "Total (BOE/d)": total})
fc.to_csv("../Data/3) Production Forecast.csv", index=False)

print(f"Today: {total[0]:,.0f} BOE/d | Yr1: {total[12]:,.0f} | Yr5: {total[60]:,.0f} | Yr10: {total[120]:,.0f}")

# the layer cake chart, base on the bottom and new pads stacked on top
years = t_future / 12
fig, ax = plt.subplots(figsize=(10, 5.5))

ax.fill_between(years, 0, base, label="PDP base (existing)", alpha=0.8)
ax.fill_between(years, base, base + wedge_by_basin["Midland"],
                label="Midland new pads", alpha=0.8)
ax.fill_between(years, base + wedge_by_basin["Midland"], total,
                label="Delaware new pads", alpha=0.8)

ax.set_xlabel("Forecast Period (years)", fontsize=12, fontname="Arial")
ax.set_ylabel("Production (BOE/d)", fontsize=12, fontname="Arial")
ax.set_title("15 Year Production Forecast (Vital Energy)", fontsize=14, fontweight="bold", fontname="Arial")
ax.legend(fontsize=11, loc="upper right")
ax.tick_params(labelsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../Data/Images/4. Forecast chart.png", dpi=150)
plt.show()