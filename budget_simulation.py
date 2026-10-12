"""
budget_simulation.py -- Future Plan Item 5
==========================================
Simulate rebalancing ad spend from inefficient to efficient campaigns.

ASSUMPTIONS (constant-efficiency model -- clearly stated):
  1. Each campaign's attributed-conversions-per-unit-cost stays fixed
     if its budget increases or decreases.
  2. Total spend is held constant -- we reallocate, not increase, budget.
  3. We shift SHIFT_PCT of bottom-quartile spend to the top quartile.

These assumptions are simplifications.  Real reallocation requires an
A/B test (frequency-cap experiment or budget-hold-out test) to validate.

Run:    python budget_simulation.py
Output: results/budget_simulation.csv  +  console summary
"""

import pathlib
import sys

import numpy as np
import pandas as pd

RESULTS   = pathlib.Path("results")
OUT_FILE  = RESULTS / "budget_simulation.csv"

# ── Configurable parameters ---------------------------------------------------
SHIFT_PCT = 0.20   # fraction of worst-quartile spend to reallocate
MIN_IMPR  = 1000   # minimum impressions filter (matches 03_spend_efficiency.sql)
# -----------------------------------------------------------------------------


def main() -> None:
    src = RESULTS / "campaign_performance.csv"
    if not src.exists():
        sys.exit("ERROR: results/campaign_performance.csv not found. Run run_all.py first.")

    df = pd.read_csv(src)

    # Keep only campaigns that have attributed conversions (needed for efficiency ratio)
    df = df[df["attributed_conversions"] > 0].copy()

    total_spend   = df["total_cost"].sum()
    total_convs   = df["attributed_conversions"].sum()
    baseline_cpac = total_spend / total_convs

    # Efficiency metric: attributed conversions earned per unit of transformed spend
    df["conv_per_unit_cost"] = df["attributed_conversions"] / df["total_cost"]

    # Quartile labels: Q1 = worst, Q4 = best
    df["efficiency_quartile"] = pd.qcut(
        df["conv_per_unit_cost"], q=4,
        labels=["Q1_worst", "Q2", "Q3", "Q4_best"]
    )

    bottom_mask = df["efficiency_quartile"] == "Q1_worst"
    top_mask    = df["efficiency_quartile"] == "Q4_best"

    spend_to_shift = df.loc[bottom_mask, "total_cost"].sum() * SHIFT_PCT

    # Assign new costs
    df["new_cost"] = df["total_cost"].copy()
    df.loc[bottom_mask, "new_cost"] = df.loc[bottom_mask, "total_cost"] * (1 - SHIFT_PCT)

    top_weight = df.loc[top_mask, "total_cost"] / df.loc[top_mask, "total_cost"].sum()
    df.loc[top_mask, "new_cost"] = df.loc[top_mask, "total_cost"] + spend_to_shift * top_weight

    # Projected conversions = new_cost * efficiency  (ASSUMPTION 1)
    df["new_attr_conv"] = df["new_cost"] * df["conv_per_unit_cost"]

    new_total_conv       = df["new_attr_conv"].sum()
    new_cpac             = total_spend / new_total_conv
    cpac_improvement_pct = (baseline_cpac - new_cpac) / baseline_cpac * 100
    conv_lift_pct        = (new_total_conv - total_convs) / total_convs * 100

    # ── Console summary -------------------------------------------------------
    print("=" * 62)
    print("BUDGET REALLOCATION SIMULATION (constant-efficiency model)")
    print("=" * 62)
    print(f"\nPARAMETERS")
    print(f"  Spend shifted from Q1 (worst) to Q4 (best) : {SHIFT_PCT*100:.0f}%")
    print(f"  Total (transformed) spend held constant     : {total_spend:.6f}")
    print(f"  Campaigns included                          : {len(df)}")
    print()
    print("BASELINE")
    print(f"  Total attributed conversions : {total_convs:,.0f}")
    print(f"  Cost per attributed conv.    : {baseline_cpac:.6f} (transformed)")
    print()
    print("SIMULATED (after reallocation)")
    print(f"  Total attributed conversions : {new_total_conv:,.1f}")
    print(f"  Cost per attributed conv.    : {new_cpac:.6f} (transformed)")
    print(f"  CpAC improvement             : {cpac_improvement_pct:.1f}%")
    print(f"  Conversion volume lift       : {conv_lift_pct:.1f}%")
    print()
    print("ASSUMPTIONS (read before citing any number):")
    print("  1. Each campaign efficiency (conv/$) is constant under budget change.")
    print("  2. No auction dynamics, frequency saturation, or reach effects.")
    print("  3. This is a MODEL, not a forecast. Validate with an A/B test.")
    print()

    # ── Save -----------------------------------------------------------------
    out_cols = [
        "campaign", "efficiency_quartile",
        "total_cost", "new_cost",
        "attributed_conversions", "new_attr_conv",
        "conv_per_unit_cost",
    ]
    df[out_cols].sort_values("conv_per_unit_cost", ascending=False).to_csv(
        OUT_FILE, index=False
    )
    print(f"Saved: {OUT_FILE}")


if __name__ == "__main__":
    main()
