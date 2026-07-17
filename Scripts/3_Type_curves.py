import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Script 3: build one type curve per basin by stacking the good-fit segments
# reads 1) Cleaned Production.csv and 2) Arps Fits.csv

def arps_decline(t, qi, Di, b):
    return qi / (1 + b * Di * t) ** (1 / b)

df = pd.read_csv("../Data/1) Cleaned Production.csv", parse_dates=["Date"])
df = df[df["Date"] < "2026-01-01"]
fits = pd.read_csv("../Data/2) Arps Fits.csv")
good = fits[fits["r2"] > 0.8]   # only trust the segments that fit well

# same peak-aligned clock as script 2, so every segment starts at its own peak
peak_idx = df.groupby("seg_id")["Oil (BBL)"].idxmax()
peak_dates = df.loc[peak_idx].set_index("seg_id")["Date"]
df["peak_date"] = df["seg_id"].map(peak_dates)
df = df[df["Date"] >= df["peak_date"]]
df["t"] = df.groupby("seg_id").cumcount()

# keep only the good-fit segments and pull each one's fitted qi onto the rows
df = df.merge(good[["seg_id", "qi", "Basin"]].rename(columns={"Basin": "fit_basin"}), on="seg_id", how="inner")

# normalize each segment by its own peak, so i'm comparing shapes not sizes.
# now every segment starts near 1.0 and i can average them together.
df["q_norm"] = df["Oil (BBL)"] / df["qi"]
print("Segments in type curve set:", df["seg_id"].nunique())
print(df.groupby("Basin")["seg_id"].nunique())

# fit one Arps curve to the averaged, normalized data, once per basin
type_curves = {}
for basin, g in df.groupby("Basin"):
    avg = g.groupby("t")["q_norm"].agg(["mean", "count"])
    avg = avg[avg["count"] >= 5]   # only trust a month if 5+ segments still report it
    t_avg = avg.index.values.astype(float)
    q_avg = avg["mean"].values
    popt, _ = curve_fit(arps_decline, t_avg, q_avg, p0=[1.0, 0.10, 1.0], bounds=([0.5, 0.001, 0.01], [1.5, 1.0, 2.0]), maxfev=5000)
    qi_tc, Di_tc, b_tc = popt
    type_curves[basin] = popt
    print(f"{basin}: qi={qi_tc:.3f}, Di={Di_tc:.4f}/month, b={b_tc:.3f}, "
          f"months={len(t_avg)}, segments={g['seg_id'].nunique()}")

# individual plot per basin: gray spaghetti of every segment, blue dots for the
# monthly average, red for the fitted type curve
max_observed_months = {}
for basin, g in df.groupby("Basin"):
    plt.figure(figsize=(8, 5))
    for seg, sg in g.groupby("seg_id"):     # each faint gray line is one segment
        plt.plot(sg["t"], sg["q_norm"], color="gray", alpha=0.15, lw=0.7)
    # the averaged data points
    avg = g.groupby("t")["q_norm"].agg(["mean", "count"])
    avg = avg[avg["count"] >= 5]
    plt.plot(avg.index, avg["mean"], "b.", markersize=6, label="Monthly Average Data")
    max_observed_months[basin] = avg.index.max()
    # the smooth fitted curve
    tt = np.linspace(0, avg.index.max(), 300)
    qi_tc, Di_tc, b_tc = type_curves[basin]
    plt.plot(tt, arps_decline(tt, qi_tc, Di_tc, b_tc), "r-", lw=2.5, label="Fitted Type Curve")
    plt.title(f"{basin} Basin Type Curve (Well Calibration)", fontsize=13, fontweight="bold", fontname="Arial", pad=12)
    plt.xlabel("Months Since Peak", fontsize=11, fontname="Arial")
    plt.ylabel("Production (Fraction of Peak)", fontsize=11, fontname="Arial")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    file_path = f"../Data/Images/3. Type curve {basin}.png"
    plt.savefig(file_path, dpi=150)
    print(f"Saved individual plot: {file_path}")
    plt.show()
    plt.close()

# the comparison chart, both basins on one axis, so the difference is obvious
midland_max = max_observed_months.get("Midland", 30)
delaware_max = max_observed_months.get("Delaware", 30)
plt.figure(figsize=(9, 5.5))
midland_params = type_curves["Midland"]
tt_midland = np.linspace(0, midland_max, 300)
plt.plot(
    tt_midland,
    arps_decline(tt_midland, *midland_params),
    color="#d9383a",  # red for Midland
    lw=3,
    label=f"Midland Basin (Di={midland_params[1]:.2f}, b={midland_params[2]:.2f})"
)
delaware_params = type_curves["Delaware"]
tt_delaware = np.linspace(0, delaware_max, 300)
plt.plot(
    tt_delaware,
    arps_decline(tt_delaware, *delaware_params),
    color="#1f77b4",  # blue for Delaware
    lw=3,
    label=f"Delaware Basin (Di={delaware_params[1]:.2f}, b={delaware_params[2]:.2f})"
)
plt.title("Permian Basin Type Curves Comparison", fontsize=14, fontweight="bold", fontname="Arial", pad=15)
plt.xlabel("Months Since Peak", fontsize=11, fontname="Arial")
plt.ylabel("Normalized Production (Fraction of Peak Rate)", fontname="Arial", fontsize=11)
plt.xlim(0, max(midland_max, delaware_max))
plt.ylim(0, 1.05)
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend(loc="upper right", frameon=True, fontsize=10, facecolor="white", edgecolor="black")
plt.tight_layout()
comparison_path = "../Data/Images/3. Type curves comparison.png"
plt.savefig(comparison_path, dpi=150)
print(f"Saved comparison plot: {comparison_path}")
plt.show()
plt.close()