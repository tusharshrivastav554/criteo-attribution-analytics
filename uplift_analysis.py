"""
uplift_analysis.py -- Future Plan Item 2
=========================================
Download and analyse the Criteo Uplift Modelling dataset (v2.1).
This is a SEPARATE dataset from the attribution dataset.

Dataset: criteo/criteo-uplift-v2.1 on Hugging Face
Columns: f0-f11 (features), treatment (0/1), conversion (0/1),
         visit (0/1), exposure (0/1)

Run:    python uplift_analysis.py
Output: results/uplift_overall.csv
        results/uplift_segments.csv
"""

import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats

RESULTS     = pathlib.Path("results")
DATA        = pathlib.Path("data")
UPLIFT_FILE = DATA / "criteo-uplift-v2.1.csv.gz"


def maybe_download() -> None:
    if UPLIFT_FILE.exists():
        print(f"Found {UPLIFT_FILE} -- skipping download.")
        return
    print("Downloading Criteo Uplift v2.1 dataset from Hugging Face...")
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download(
            repo_id="criteo/criteo-uplift-v2.1",
            filename="criteo-uplift-v2.1.csv.gz",
            repo_type="dataset",
            local_dir=str(DATA),
        )
        print(f"Saved to {UPLIFT_FILE}")
    except Exception as exc:
        sys.exit(
            f"\nDownload failed: {exc}\n"
            "Manual option: download from\n"
            "  https://huggingface.co/datasets/criteo/criteo-uplift-v2.1\n"
            f"and place the file at {UPLIFT_FILE}"
        )


def compute_uplift(df: pd.DataFrame, outcome: str) -> dict:
    """Average Treatment Effect with 95% CI and two-sided z-test p-value."""
    treated = df[df["treatment"] == 1][outcome].dropna()
    control = df[df["treatment"] == 0][outcome].dropna()

    n_t, n_c       = len(treated), len(control)
    mean_t, mean_c = treated.mean(), control.mean()
    uplift         = mean_t - mean_c

    se    = np.sqrt(treated.var() / n_t + control.var() / n_c)
    z     = uplift / se if se > 0 else np.nan
    p     = float(2 * (1 - stats.norm.cdf(abs(z)))) if not np.isnan(z) else np.nan
    ci_lo = uplift - 1.96 * se
    ci_hi = uplift + 1.96 * se

    return dict(
        outcome=outcome,
        n_treated=n_t, n_control=n_c,
        rate_treated=round(mean_t, 6),
        rate_control=round(mean_c, 6),
        uplift=round(uplift, 6),
        ci_lo=round(ci_lo, 6), ci_hi=round(ci_hi, 6),
        z_stat=round(float(z), 3) if not np.isnan(z) else None,
        p_value=round(p, 6) if not np.isnan(p) else None,
    )


def segment_analysis(df: pd.DataFrame, outcome: str = "conversion") -> pd.DataFrame:
    """Heterogeneous treatment effects by quartile of feature f0."""
    df = df.copy()
    df["f0_quartile"] = pd.qcut(df["f0"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    rows = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        sub = df[df["f0_quartile"] == q]
        r = compute_uplift(sub, outcome)
        r["segment"] = f"f0_{q}"
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    maybe_download()

    print("\nLoading dataset (may take ~30 s for 13M rows)...")
    df = pd.read_csv(UPLIFT_FILE, compression="gzip")
    print(f"  Loaded: {len(df):,} rows, columns: {list(df.columns)}")

    outcomes = [c for c in ["conversion", "visit"] if c in df.columns]

    print("\n-- Overall Average Treatment Effect --")
    overall_rows = []
    for outcome in outcomes:
        r = compute_uplift(df, outcome)
        overall_rows.append(r)
        sig = "SIGNIFICANT" if (r["p_value"] is not None and r["p_value"] < 0.05) else "not significant"
        print(
            f"  {outcome:12s}: uplift={r['uplift']:+.6f}  "
            f"95% CI [{r['ci_lo']:+.6f}, {r['ci_hi']:+.6f}]  "
            f"p={r['p_value']:.4f}  [{sig}]"
        )
        print(f"               treated rate={r['rate_treated']:.4f}  "
              f"control rate={r['rate_control']:.4f}  "
              f"n_t={r['n_treated']:,}  n_c={r['n_control']:,}")

    pd.DataFrame(overall_rows).to_csv(RESULTS / "uplift_overall.csv", index=False)
    print(f"\nSaved: results/uplift_overall.csv")

    if "conversion" in outcomes:
        print("\n-- Segment Effects (conversion, by f0 quartile) --")
        seg = segment_analysis(df, "conversion")
        print(seg[["segment", "n_treated", "n_control", "uplift", "ci_lo", "ci_hi", "p_value"]].to_string(index=False))
        seg.to_csv(RESULTS / "uplift_segments.csv", index=False)
        print(f"\nSaved: results/uplift_segments.csv")

    if "exposure" in df.columns:
        print("\n-- Exposure Bias Check --")
        exp_rate = df.groupby("treatment")["exposure"].mean()
        print(f"  Exposure rate: treatment=1 -> {exp_rate.get(1, float('nan')):.4f}, "
              f"treatment=0 -> {exp_rate.get(0, float('nan')):.4f}")
        print("  Note: if exposure differs across arms, the ATE above is an intent-to-treat")
        print("  estimate and understates the effect on users actually exposed.")


if __name__ == "__main__":
    main()
