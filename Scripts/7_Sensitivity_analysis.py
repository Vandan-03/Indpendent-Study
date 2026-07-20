import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Script 7: run the whole model across oil prices and decline rates for a sensitivity grid

def modified_arps(t, qi, Di, b, Dterm_annual=0.08):
    Dterm_m = 1 - (1 - Dterm_annual) ** (1/12)
    t_sw = max((Di / Dterm_m - 1) / (b * Di), 0.0)
    t = np.asarray(t, dtype=float)
    q_hyp = qi / (1 + b * Di * t) ** (1 / b)
    q_sw = qi / (1 + b * Di * t_sw) ** (1 / b)
    q_exp = q_sw * np.exp(-Dterm_m * (t - t_sw))
    return np.where(t <= t_sw, q_hyp, q_exp), t_sw


# the whole model wrapped in a function, so i can call it with any oil price or
# decline multiplier and get PV-10 back. this is what lets me sweep the grid.
def run_model(oil_px=76.76, decline_mult=1.0, wells_per_pad=4,
              loe_mult=1.0, disc=0.10, include_ga=True):

    FP, DAYS, DRILL = 180, 30.4, 120   # FP = forecast months, DRILL = months of drilling
    t_future = np.arange(FP)

    mid_share, base_age, base_total = 0.633, 32.8, 138_000

    # decline_mult scales Di in both machines, so a steeper/shallower run hits everything
    basins = {
        "Midland":  {"share": mid_share,     "Di": 0.334 * decline_mult, "b": 1.20},
        "Delaware": {"share": 1 - mid_share,  "Di": 0.228 * decline_mult, "b": 0.963},
    }

    # existing base, aged to 32.8 months and rescaled to today's rate
    base = np.zeros(FP)
    for p in basins.values():
        q0 = base_total * p["share"]
        shape, _ = modified_arps(base_age + t_future, 1.0, p["Di"], p["b"])
        at_age, _ = modified_arps(np.array([base_age]), 1.0, p["Di"], p["b"])
        base += q0 * shape / at_age[0]

    # drilling program backed out of the capital budget
    cost_per_well = 873.637 / 73.4          # $MM
    pad_cost = wells_per_pad * cost_per_well * 1e6
    pads_per_month = 875e6 / (pad_cost * 12)

    pads = {"Midland":  {"n": pads_per_month * 0.633, "ip": 4191,
                         "Di": 0.334 * decline_mult, "b": 1.20},
            "Delaware": {"n": pads_per_month * 0.367, "ip": 2874,
                         "Di": 0.228 * decline_mult, "b": 0.963}}

    wedges = np.zeros(FP)
    for p in pads.values():
        for m in range(DRILL):
            shape, _ = modified_arps(t_future[: FP - m], 1.0, p["Di"], p["b"])
            wedges[m:] += p["n"] * p["ip"] * shape

    total = base + wedges
    boe = total * DAYS

    # revenue minus opex minus capex, then discount to PV-10
    ga = 1.75 if include_ga else 0.0
    opex = boe * ((9.15 * loe_mult) + 2.41 + 0.92 + 0.36 + ga)
    rev = boe * (0.46 * oil_px + 0.27 * 13.66 + 0.27 * 6 * 0.85)
    capex = np.where(t_future < DRILL, pads_per_month * pad_cost, 0.0)
    fcf = rev - opex - capex

    r_m = (1 + disc) ** (1/12) - 1
    pv = (fcf / (1 + r_m) ** (t_future + 0.5)).sum()
    return pv / 1e9

oil_cases = [55, 65, 76.76, 85, 95]
decl_cases = {"Shallow (-25%)": 0.75, "Base": 1.00, "Steep (+25%)": 1.25}

for label, ga_flag in [("(inc. G&A)", True), ("(SEC, ex. G&A)", False)]:
    grid = pd.DataFrame(
        {name: [round(run_model(oil_px=o, decline_mult=d, include_ga=ga_flag), 2)
                for o in oil_cases]
         for name, d in decl_cases.items()},
        index=[f"${o}" for o in oil_cases]
    )
    grid.index.name = "Oil price"
    print(f"\nPV-10 ($Bn), {label}\n")
    print(grid)

    # same heatmap block as before, with the label in the title and filename
    fig, ax = plt.subplots(figsize=(7, 5))
    data = grid.values.astype(float)
    im = ax.imshow(data, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(grid.columns))); ax.set_xticklabels(grid.columns, fontsize=11, fontname="Arial")
    ax.set_yticks(range(len(grid.index)));  ax.set_yticklabels(grid.index, fontsize=11, fontname="Arial")
    ax.set_xlabel("Decline Scenario", fontsize=12, fontname="Arial")
    ax.set_ylabel("Oil Price ($/bbl)", fontsize=12, fontname="Arial")
    ax.set_title(f"PV-10 Sensitivity ($Bn), {label}", fontsize=13, fontweight="bold", fontname="Arial")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"${data[i,j]:.2f}", ha="center", va="center", fontsize=11, fontweight="bold")
    plt.colorbar(im, label="PV-10 ($Bn)")
    plt.tight_layout()
    plt.savefig(f"../Data/Images/5. Sensitivity heatmap ({'Includes G&A' if ga_flag else 'SEC'}).png", dpi=150)
    plt.show()