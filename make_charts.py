"""
make_charts.py â€” Generate all 5 analysis charts from results CSVs.

Produces:
  charts/01_cost_per_conv.png      â€” Best/worst 10 campaigns by cost per attributed conversion
  charts/02_spend_vs_conv.png      â€” Spend share vs conversion share scatter
  charts/03_funnel.png             â€” Aggregate funnel: impressions â†’ clicks â†’ conversions â†’ attributed
  charts/04_frequency.png          â€” Conversion rate by frequency bucket (with pair counts)
  charts/05_click_vs_view.png      â€” Post-click vs post-view conversions by campaign (top 15)

Usage:
    python make_charts.py
"""

import io
import pathlib
import sys
import warnings

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

warnings.filterwarnings("ignore")

CHARTS = pathlib.Path("charts")
CHARTS.mkdir(exist_ok=True)

DPI = 150
STYLE = {
    "axes.facecolor": "#1e1e2e",
    "figure.facecolor": "#13131f",
    "axes.edgecolor": "#444466",
    "axes.labelcolor": "#cdd6f4",
    "xtick.color": "#cdd6f4",
    "ytick.color": "#cdd6f4",
    "text.color": "#cdd6f4",
    "grid.color": "#2a2a3e",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "axes.titlepad": 12,
}
plt.rcParams.update(STYLE)

BLUE = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
MAUVE = "#cba6f7"
PEACH = "#fab387"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Chart 1 â€” Cost per attributed conversion: best 10 and worst 10 campaigns
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def chart_01_cost_per_conv() -> None:
    df = pd.read_csv("results/campaign_performance.csv")
    if df.empty:
        print("⚠️ Warning: results/campaign_performance.csv is empty. Skipping Chart 1.")
        return
    df["cost_per_attr_conv"] = pd.to_numeric(df["cost_per_attr_conv"], errors="coerce")
    df = df.dropna(subset=["cost_per_attr_conv"]).sort_values("cost_per_attr_conv")
    if df.empty:
        print("⚠️ Warning: No valid cost_per_attr_conv rows found. Skipping Chart 1.")
        return

    top10 = df.head(10)
    worst10 = df.tail(10).sort_values("cost_per_attr_conv", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Cost per Attributed Conversion — Most vs Least Efficient Campaigns\n"
        "(transformed cost units; relative comparisons only)",
        fontsize=12, fontweight="bold", color="#cdd6f4",
    )

    # Best 10
    ax = axes[0]
    ax.barh(top10["campaign"].astype(str), top10["cost_per_attr_conv"], color=GREEN)
    ax.set_xlabel("Cost per attributed conversion (transformed units)")
    ax.set_title("10 Most Efficient Campaigns", fontsize=10, color=GREEN)
    ax.invert_yaxis()
    ax.grid(axis="x")

    # Worst 10
    ax = axes[1]
    ax.barh(worst10["campaign"].astype(str), worst10["cost_per_attr_conv"], color=RED)
    ax.set_xlabel("Cost per attributed conversion (transformed units)")
    ax.set_title("10 Least Efficient Campaigns", fontsize=10, color=RED)
    ax.invert_yaxis()
    ax.grid(axis="x")

    fig.tight_layout()
    fig.savefig(CHARTS / "01_cost_per_conv.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("✓ Chart 1 saved: charts/01_cost_per_conv.png")


# ─────────────────────────────────────────────────────────────────────────────
# Chart 2 — Spend share vs conversion share (scatter)
# ─────────────────────────────────────────────────────────────────────────────
def chart_02_spend_vs_conv() -> None:
    df = pd.read_csv("results/campaign_performance.csv")
    if df.empty:
        print("⚠️ Warning: results/campaign_performance.csv is empty. Skipping Chart 2.")
        return
    df["spend_share"] = pd.to_numeric(df["spend_share"], errors="coerce")
    df["conv_share"] = pd.to_numeric(df["conv_share"], errors="coerce")
    df = df.dropna(subset=["spend_share", "conv_share"])
    if df.empty:
        print("⚠️ Warning: No valid spend_share/conv_share rows found. Skipping Chart 2.")
        return

    df["spend_pct"] = df["spend_share"] * 100
    df["conv_pct"] = df["conv_share"] * 100
    df["waste"] = df["spend_pct"] - df["conv_pct"]  # positive = overspending vs results

    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(
        df["spend_pct"],
        df["conv_pct"],
        c=df["waste"],
        cmap="RdYlGn_r",
        alpha=0.75,
        s=60,
        edgecolors="#444466",
        linewidths=0.5,
    )
    # Diagonal reference line (perfect equality)
    lim = max(df["spend_pct"].max(), df["conv_pct"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "--", color="#888899", linewidth=1, label="Equal share")

    cbar = fig.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Spend share − Conv share (%pt)", color="#cdd6f4")
    cbar.ax.yaxis.set_tick_params(color="#cdd6f4")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#cdd6f4")

    ax.set_xlabel("Spend share (%)")
    ax.set_ylabel("Attributed conversion share (%)")
    ax.set_title(
        "Spend Share vs Attributed Conversion Share by Campaign\n"
        "Points above the diagonal: over-delivering; below: under-delivering",
        fontsize=10,
    )
    ax.legend(fontsize=9)
    ax.grid(True)

    fig.tight_layout()
    fig.savefig(CHARTS / "02_spend_vs_conv.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("✓ Chart 2 saved: charts/02_spend_vs_conv.png")


# ─────────────────────────────────────────────────────────────────────────────
# Chart 3 — Aggregate funnel: impressions → clicks → conversions → attributed
# ─────────────────────────────────────────────────────────────────────────────
def chart_03_funnel() -> None:
    df = pd.read_csv("results/funnel_by_campaign.csv")
    if df.empty:
        print("⚠️ Warning: results/funnel_by_campaign.csv is empty. Skipping Chart 3.")
        return

    for col in ["impressions", "clicks", "conversions", "attributed_conversions"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    totals = {
        "Impressions": df["impressions"].sum(),
        "Clicks": df["clicks"].sum(),
        "Conversions": df["conversions"].sum(),
        "Attributed\nConversions": df["attributed_conversions"].sum(),
    }
    labels = list(totals.keys())
    values = list(totals.values())
    colors = [BLUE, MAUVE, YELLOW, GREEN]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="#444466", width=0.55)

    # Annotate bars with value and drop-off %
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.02,
            f"{val:,.0f}",
            ha="center", va="bottom", fontsize=9, color="#cdd6f4",
        )
        if i > 0:
            prev = values[i - 1]
            pct = val / prev * 100 if prev else 0
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 0.5,
                f"{pct:.1f}%\nof prev",
                ha="center", va="center", fontsize=8, color="#13131f", fontweight="bold",
            )

    ax.set_yscale("log")
    ax.set_ylabel("Count (log scale)")
    ax.set_title(
        "Aggregate Ad Funnel — Impressions → Clicks → Conversions → Attributed\n"
        "(Campaigns with ≥ 1,000 impressions)",
        fontsize=10,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="y")

    fig.tight_layout()
    fig.savefig(CHARTS / "03_funnel.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("✓ Chart 3 saved: charts/03_funnel.png")


# ─────────────────────────────────────────────────────────────────────────────
# Chart 4 — Conversion rate by frequency bucket (with pair counts labeled)
# ─────────────────────────────────────────────────────────────────────────────
def chart_04_frequency() -> None:
    df = pd.read_csv("results/frequency_buckets.csv")
    if df.empty:
        print("⚠️ Warning: results/frequency_buckets.csv is empty. Skipping Chart 4.")
        return

    df["bucket_order"] = pd.to_numeric(df["bucket_order"], errors="coerce")
    df["conv_rate"] = pd.to_numeric(df["conv_rate"], errors="coerce").fillna(0)
    df["user_campaign_pairs"] = pd.to_numeric(df["user_campaign_pairs"], errors="coerce").fillna(0)
    df = df.sort_values("bucket_order")

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        df["freq_bucket"], df["conv_rate"] * 100,
        color=BLUE, edgecolor="#444466", width=0.55
    )

    # Annotate each bar with the pair count
    for bar, pairs in zip(bars, df["user_campaign_pairs"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"n={int(pairs):,}",
            ha="center", va="bottom", fontsize=8, color="#cdd6f4",
        )

    ax.set_xlabel("Impressions per user per campaign (frequency bucket)")
    ax.set_ylabel("Conversion rate (%)")
    ax.set_title(
        "Conversion Rate by Ad Frequency Bucket\n"
        "Correlation only — heavy-exposure users may differ in intent",
        fontsize=10,
    )
    ax.grid(axis="y")

    fig.tight_layout()
    fig.savefig(CHARTS / "04_frequency.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("✓ Chart 4 saved: charts/04_frequency.png")


# ─────────────────────────────────────────────────────────────────────────────
# Chart 5 — Post-click vs post-view conversion share (top 15 campaigns)
# ─────────────────────────────────────────────────────────────────────────────
def chart_05_click_vs_view() -> None:
    df = pd.read_csv("results/funnel_by_campaign.csv")
    if df.empty:
        print("⚠️ Warning: results/funnel_by_campaign.csv is empty. Skipping Chart 5.")
        return

    df["conversions"] = pd.to_numeric(df["conversions"], errors="coerce").fillna(0)
    df["share_conversions_with_click"] = pd.to_numeric(
        df["share_conversions_with_click"], errors="coerce"
    )
    df = df.dropna(subset=["share_conversions_with_click"])

    if df.empty:
        print("⚠️ Warning: No valid share_conversions_with_click data. Skipping Chart 5.")
        return

    df = df.nlargest(15, "conversions").copy()
    df["click_pct"] = df["share_conversions_with_click"] * 100
    df["view_pct"] = 100 - df["click_pct"]
    df = df.sort_values("click_pct")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["campaign"].astype(str), df["click_pct"], label="Post-click", color=GREEN)
    ax.barh(
        df["campaign"].astype(str), df["view_pct"],
        left=df["click_pct"], label="Post-view (no click)", color=PEACH
    )
    ax.axvline(50, color="#888899", linewidth=1, linestyle="--")
    ax.set_xlabel("Share of conversions (%)")
    ax.set_title(
        "Post-Click vs Post-View Conversions — Top 15 Campaigns by Conversions\n"
        "Campaigns near 0% post-click rely almost entirely on view-through attribution",
        fontsize=10,
    )
    ax.set_xlim(0, 100)
    ax.legend(loc="lower right")
    ax.grid(axis="x")

    fig.tight_layout()
    fig.savefig(CHARTS / "05_click_vs_view.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("✓ Chart 5 saved: charts/05_click_vs_view.png")


if __name__ == "__main__":
    print("Generating charts from results/ CSVs...\n")
    chart_01_cost_per_conv()
    chart_02_spend_vs_conv()
    chart_03_funnel()
    chart_04_frequency()
    chart_05_click_vs_view()
    print("\n✓ Chart generation completed.")

