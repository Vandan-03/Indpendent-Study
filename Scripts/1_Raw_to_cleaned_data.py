import pandas as pd

# Script 1: clean the raw RRC lease data and split leases into segments
# reads the 100-lease monthly file, writes 1) Cleaned Production.csv

df = pd.read_excel("../Data/Monthly_raw_data.xlsx", sheet_name="Monthly data")

# RRC writes missing months as "NO RPT" text. if i convert to numbers first,
# those become NaN and i can drop them in one go. deleting "NO RPT" by name
# would miss variants like a stray space or N/A.
df["Oil (BBL)"] = pd.to_numeric(df["Oil (BBL)"], errors="coerce")
df["Gas (MCF)"] = pd.to_numeric(df["Gas (MCF)"], errors="coerce")
df = df.dropna(subset=["Oil (BBL)"])

# the zeros before a lease starts producing aren't decline, the well just
# didn't exist yet. keeping them would make the curve rise then fall later.
df = df.sort_values(["Lease Name", "Date"])
first_production = df[df["Oil (BBL)"] > 0].groupby("Lease Name")["Date"].min()
df = df[df["Date"] >= df["Lease Name"].map(first_production)]

# when a lease suddenly produces more than it ever has (1.5x its running peak),
# that's new wells drilled on the same lease. i split it there so each batch
# of wells gets its own decline curve. the month 6 check avoids early noise.
df = df.sort_values(["Lease Name", "Date"]).reset_index(drop=True)

df["prior_peak"] = df.groupby("Lease Name")["Oil (BBL)"].transform(
    lambda series: series.cummax().shift(1)
)
df["month_index"] = df.groupby("Lease Name").cumcount()

df["is_new_well_spike"] = (
    (df["Oil (BBL)"] > 1.5 * df["prior_peak"]) &
    (df["month_index"] >= 6)
)

# a running count of the spikes gives me the segment number
df["Segment"] = df.groupby("Lease Name")["is_new_well_spike"].cumsum()
df = df.drop(columns=["prior_peak", "is_new_well_spike"])

leases_split = df.groupby("Lease Name")["Segment"].max()
print("Leases with splits:", (leases_split > 0).sum())
print(leases_split[leases_split > 0])

# anything under 8 months is too short to fit a 3 parameter Arps curve on
df["seg_id"] = df["Lease Name"] + "_" + df["Segment"].astype(str)
segment_month_counts = df.groupby("seg_id")["Date"].count()
valid_segments = segment_month_counts[segment_month_counts >= 8].index
df = df[df["seg_id"].isin(valid_segments)]

print("Segments kept:", df["seg_id"].nunique())
print("Rows after segment filter:", len(df))
print(df.info())
print(df.head(5))

df.to_csv("../Data/1) Cleaned Production.csv", index=False)
print("Saved", len(df), "rows to Cleaned Production.csv")