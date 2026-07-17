import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Script 2: fit an Arps decline curve to every segment and grade each fit
# reads 1) Cleaned Production.csv, writes 2) Arps Fits.csv

df = pd.read_csv("../Data/1) Cleaned Production.csv", parse_dates=["Date"])
df = df[df["Date"] < "2026-01-01"]   # last RRC month is usually incomplete, so i drop it

# line each segment up on its own clock. Arps only describes the fall after peak,
# so i find each segment's peak month and keep everything from there on.
# t then counts months since that peak: 0, 1, 2...
peak_idx = df.groupby("seg_id")["Oil (BBL)"].idxmax()
peak_dates = df.loc[peak_idx].set_index("seg_id")["Date"]

df["peak_date"] = df["seg_id"].map(peak_dates)
df = df[df["Date"] >= df["peak_date"]]

df["t"] = df.groupby("seg_id").cumcount()

print("Segments:", df["seg_id"].nunique())
print("Rows for fitting:", len(df))

# the Arps hyperbolic equation. qi is the peak rate, Di the starting decline, b the curvature
def arps_decline(t, qi, Di, b):
    return qi / (1 + b * Di * t) ** (1 / b)

results = []
for seg, g in df.groupby("seg_id"):
    # ignore months below 5% of peak, those are shut ins, not real decline,
    # and they'd drag the curve down
    g_fit = g[g["Oil (BBL)"] > 0.05 * g["Oil (BBL)"].max()]
    t = g_fit["t"].values.astype(float)
    q = g_fit["Oil (BBL)"].values.astype(float)
    if len(t) < 8:
        continue
    try:
        # p0 is my starting guess, bounds keep the fit physically sensible
        popt, _ = curve_fit(
            arps_decline, t, q,
            p0=[q[0], 0.10, 1.0],
            bounds=([1, 0.001, 0.01], [q[0] * 3, 1.0, 2.0]),
            maxfev=5000
        )
        qi, Di, b = popt
        q_pred = arps_decline(t, qi, Di, b)
        # R2 tells me how well the curve matches, 1.0 is perfect
        ss_res = np.sum((q - q_pred) ** 2)
        ss_tot = np.sum((q - np.mean(q)) ** 2)
        r2 = 1 - ss_res / ss_tot
        results.append({
            "seg_id": seg,
            "Basin": g["Basin"].iloc[0],
            "County": g["County"].iloc[0],
            "months": len(t),
            "qi": qi, "Di": Di, "b": b, "r2": r2
        })
    except RuntimeError:
        # some segments are too erratic for curve_fit to converge, i keep them as NaN
        results.append({"seg_id": seg, "Basin": g["Basin"].iloc[0],
                        "County": g["County"].iloc[0], "months": len(t),
                        "qi": np.nan, "Di": np.nan, "b": np.nan, "r2": np.nan})

fits = pd.DataFrame(results)
fits.to_csv("../Data/2) Arps Fits.csv", index=False)

print(fits["r2"].describe())
print("Fits with R2 > 0.8:", (fits["r2"] > 0.8).sum(), "of", len(fits))

# before i throw out the poor fits, i want to know how much oil they represent.
# if it's a big share i can't just ignore them.
bad = fits[fits["r2"] < 0.8]["seg_id"]

seg_oil = df.groupby("seg_id")["Oil (BBL)"].sum()
total_oil = seg_oil.sum()

bad_oil = seg_oil[seg_oil.index.isin(bad)].sort_values(ascending=False)

print(bad_oil)
print()
print("Bad-fit oil:", f"{bad_oil.sum():,.0f}", "BBL")
print("Share of sample:", f"{bad_oil.sum() / total_oil:.1%}")

# plot the 6 worst fits so i can see WHY they failed (shut ins, new wells, or just noise)
worst = fits[fits["r2"] < 0.8].sort_values("r2").head(6)["seg_id"]

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, seg in zip(axes.flat, worst):
    g = df[df["seg_id"] == seg]
    row = fits[fits["seg_id"] == seg].iloc[0]
    ax.plot(g["t"], g["Oil (BBL)"], "ko", markersize=3, label="Actual")
    tt = np.linspace(0, g["t"].max(), 200)
    ax.plot(tt, arps_decline(tt, row["qi"], row["Di"], row["b"]), "r-", label="Fit")
    ax.set_title(f"{seg}\nR2={row['r2']:.2f}", fontsize=9)
    ax.legend(fontsize=7)
plt.tight_layout()
plt.savefig("../Data/Images/1. Worst fits.png", dpi=150)
plt.show()

# a few recent, high-volume segments i want to eyeball separately before deciding
check = ["JOSEPHINE 37-36_1", "VERANCIA 50-26-27 UNIT 2 WA_1", "SATNIN 37-36_1"]

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, seg in zip(axes.flat, check):
    g = df[df["seg_id"] == seg]
    row = fits[fits["seg_id"] == seg].iloc[0]
    ax.plot(g["t"], g["Oil (BBL)"], "ko", markersize=3)
    tt = np.linspace(0, g["t"].max(), 200)
    ax.plot(tt, arps_decline(tt, row["qi"], row["Di"], row["b"]), "r-")
    ax.set_title(f"{seg}\nR2={row['r2']:.2f}", fontsize=9)
plt.tight_layout()
plt.savefig("../Data/Images/2. Recent bad fits.png", dpi=150)
plt.show()

# check where JOSEPHINE's low months sit as a fraction of peak, to see if the 5% cutoff caught them
g = df[df["seg_id"] == "JOSEPHINE 37-36_1"]
print((g["Oil (BBL)"] / g["Oil (BBL)"].max()).sort_values().head(8))