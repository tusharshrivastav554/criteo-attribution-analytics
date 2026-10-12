"""pages/6_Budget_Simulation.py -- Spend reallocation simulation."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Budget Simulation", page_icon="💡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.sec-header{font-size:1.2rem;font-weight:700;color:#E2E8F0;
  border-left:4px solid #7C3AED;padding-left:.75rem;margin:1.6rem 0 .8rem;}
.warn-box{background:#1C1917;border:1px solid #92400E;border-radius:10px;padding:1rem 1.2rem;margin:.8rem 0;}
.result-box{background:#052E16;border:1px solid #16A34A;border-radius:10px;padding:1rem 1.2rem;margin:.8rem 0;}
#MainMenu,footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"

@st.cache_data
def load_sim():
    p = RESULTS / "budget_simulation.csv"
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_camp():
    p = RESULTS / "campaign_performance.csv"
    return pd.read_csv(p) if p.exists() else None

df_sim  = load_sim()
df_camp = load_camp()

st.title("💡 Budget Reallocation Simulation")
st.caption("Estimate the effect of shifting spend from low-efficiency to high-efficiency campaigns.")

# Always show assumption warning at top
st.markdown(
    '<div class="warn-box">'
    "<b>⚠️ This is a simulation, not a forecast.</b><br>"
    "It assumes each campaign's conversion-per-dollar efficiency is constant under budget changes. "
    "Real-world effects (auction dynamics, frequency saturation, reach limits) are not modelled. "
    "<b>Validate any reallocation with an A/B test (budget hold-out or geo experiment) before acting.</b>"
    "</div>", unsafe_allow_html=True,
)

if df_sim is None:
    st.info("Run `python budget_simulation.py` to generate simulation data, then refresh.")
    if df_camp is not None:
        st.markdown("### Preview: Campaign Efficiency Distribution")
        df_c = df_camp[df_camp["attributed_conversions"] > 0].copy()
        df_c["conv_per_unit_cost"] = df_c["attributed_conversions"] / df_c["total_cost"]
        fig = px.histogram(df_c, x="conv_per_unit_cost", nbins=30,
                           labels={"conv_per_unit_cost":"Conversions per Unit Spend (transformed)"},
                           template="plotly_dark", color_discrete_sequence=["#7C3AED"])
        fig.update_layout(plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14", font_color="#E2E8F0")
        st.plotly_chart(fig, use_container_width=True)
    st.stop()

df_sim["campaign"] = df_sim["campaign"].astype(str)
df_sim["spend_delta"]  = df_sim["new_cost"]      - df_sim["total_cost"]
df_sim["conv_delta"]   = df_sim["new_attr_conv"]  - df_sim["attributed_conversions"]

total_spend     = df_sim["total_cost"].sum()
total_conv_old  = df_sim["attributed_conversions"].sum()
total_conv_new  = df_sim["new_attr_conv"].sum()
cpac_old = total_spend / total_conv_old if total_conv_old else float("nan")
cpac_new = total_spend / total_conv_new if total_conv_new else float("nan")
improvement_pct = (cpac_old - cpac_new) / cpac_old * 100

# ── KPI summary ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Attributed Conv. (before)", f"{total_conv_old:,.0f}")
c2.metric("Attributed Conv. (simulated)", f"{total_conv_new:,.1f}",
          delta=f"+{total_conv_new - total_conv_old:,.1f}")
c3.metric("CpAC Before (transformed)", f"{cpac_old:.6f}")
c4.metric("CpAC Simulated (transformed)", f"{cpac_new:.6f}",
          delta=f"{-improvement_pct:.1f}% lower", delta_color="inverse")

st.markdown(
    f'<div class="result-box">'
    f"<b>Simulated result:</b> Shifting 20% of worst-quartile spend to the best-quartile campaigns "
    f"is projected to improve cost per attributed conversion by <b>{improvement_pct:.1f}%</b> "
    f"while holding total spend constant."
    f"</div>", unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["📊 Before vs After by Quartile", "📋 Campaign Detail"])

# ── Tab 1: Before/after by quartile ───────────────────────────────────────
with tab1:
    st.markdown('<div class="sec-header">Spend and Conversions Before vs After Reallocation</div>', unsafe_allow_html=True)

    q_agg = df_sim.groupby("efficiency_quartile", observed=True).agg(
        spend_before=("total_cost","sum"),
        spend_after=("new_cost","sum"),
        conv_before=("attributed_conversions","sum"),
        conv_after=("new_attr_conv","sum"),
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name="Before", x=q_agg["efficiency_quartile"],
                              y=q_agg["spend_before"], marker_color="#4F46E5"))
        fig1.add_trace(go.Bar(name="After",  x=q_agg["efficiency_quartile"],
                              y=q_agg["spend_after"],  marker_color="#06B6D4"))
        fig1.update_layout(barmode="group", template="plotly_dark",
                           plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                           font_color="#E2E8F0", height=360,
                           xaxis_title="Efficiency Quartile", yaxis_title="Total Spend (transformed)",
                           title="Spend reallocation by quartile")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Before", x=q_agg["efficiency_quartile"],
                              y=q_agg["conv_before"], marker_color="#4F46E5"))
        fig2.add_trace(go.Bar(name="After",  x=q_agg["efficiency_quartile"],
                              y=q_agg["conv_after"],  marker_color="#10B981"))
        fig2.update_layout(barmode="group", template="plotly_dark",
                           plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                           font_color="#E2E8F0", height=360,
                           xaxis_title="Efficiency Quartile", yaxis_title="Attributed Conversions",
                           title="Projected conversion change by quartile")
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Campaign-level detail ───────────────────────────────────────────
with tab2:
    quartile_filter = st.multiselect(
        "Filter by quartile", options=["Q1_worst","Q2","Q3","Q4_best"],
        default=["Q1_worst","Q4_best"]
    )
    df_show = df_sim[df_sim["efficiency_quartile"].isin(quartile_filter)] if quartile_filter else df_sim

    st.dataframe(
        df_show[["campaign","efficiency_quartile","conv_per_unit_cost",
                 "total_cost","new_cost","attributed_conversions","new_attr_conv",
                 "spend_delta","conv_delta"]].sort_values("conv_per_unit_cost", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "conv_per_unit_cost":     st.column_config.NumberColumn("Conv/$ Efficiency", format="%.2f"),
            "total_cost":             st.column_config.NumberColumn("Spend (before)",    format="%.5f"),
            "new_cost":               st.column_config.NumberColumn("Spend (after)",     format="%.5f"),
            "attributed_conversions": st.column_config.NumberColumn("Conv (before)",     format="%.0f"),
            "new_attr_conv":          st.column_config.NumberColumn("Conv (simulated)",  format="%.1f"),
            "spend_delta":            st.column_config.NumberColumn("Spend Δ",           format="%.5f"),
            "conv_delta":             st.column_config.NumberColumn("Conv Δ",            format="%.1f"),
        }
    )
