"""pages/3_Funnel_and_Spend.py -- Funnel stages and click vs post-view conversion split."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Funnel & Spend", page_icon="🔻", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.sec-header{font-size:1.2rem;font-weight:700;color:#E2E8F0;
  border-left:4px solid #7C3AED;padding-left:.75rem;margin:1.6rem 0 .8rem;}
#MainMenu,footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"

@st.cache_data
def load_funnel():
    p = RESULTS / "funnel_by_campaign.csv"
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_camp():
    p = RESULTS / "campaign_performance.csv"
    return pd.read_csv(p) if p.exists() else None

df_f = load_funnel()
df_c = load_camp()

st.title("🔻 Funnel & Spend Analysis")
st.caption("Impression → Click → Conversion → Attributed funnel, and post-click vs post-view conversion split.")

if df_f is None:
    st.error("Missing `results/funnel_by_campaign.csv` — run `python run_all.py` first.")
    st.stop()

df_f["campaign"] = df_f["campaign"].astype(str)

tab1, tab2, tab3 = st.tabs(["📉 Aggregate Funnel", "📊 Per-Campaign Funnel", "👁️ Post-Click vs Post-View"])

# ── Tab 1: Aggregate funnel waterfall ─────────────────────────────────────
with tab1:
    st.markdown('<div class="sec-header">Overall Funnel (all campaigns aggregated)</div>', unsafe_allow_html=True)

    agg = {
        "Impressions":          int(df_f["impressions"].sum()),
        "Clicks":               int(df_f["clicks"].sum()),
        "Conversions":          int(df_f["conversions"].sum()),
        "Attributed Conv.":     int(df_f["attributed_conversions"].sum()),
    }
    stages = list(agg.keys())
    values = list(agg.values())

    # Funnel bar chart
    colors = ["#7C3AED","#4F46E5","#06B6D4","#10B981"]
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent initial",
        marker_color=colors,
        connector=dict(line=dict(color="#1E293B", width=2)),
    ))
    fig.update_layout(
        template="plotly_dark", plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", height=380, margin=dict(l=140),
        title="Funnel: Impressions → Attributed Conversions",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Drop-off metrics
    c1, c2, c3 = st.columns(3)
    ctr  = values[1] / values[0] * 100 if values[0] else 0
    cvr  = values[2] / values[1] * 100 if values[1] else 0
    attr = values[3] / values[2] * 100 if values[2] else 0
    c1.metric("Click-Through Rate",              f"{ctr:.2f}%")
    c2.metric("Click-to-Conversion Rate",        f"{cvr:.2f}%")
    c3.metric("Attribution Rate",                f"{attr:.2f}%")

# ── Tab 2: Per-campaign funnel bars ───────────────────────────────────────
with tab2:
    st.markdown('<div class="sec-header">Top Campaigns by Impressions</div>', unsafe_allow_html=True)
    n = st.slider("Top N campaigns", 5, 25, 12, key="funnel_n")
    df_top = df_f.nlargest(n, "impressions").copy()

    fig2 = go.Figure()
    stage_defs = [
        ("impressions",          "Impressions",      "#7C3AED"),
        ("clicks",               "Clicks",           "#4F46E5"),
        ("conversions",          "Conversions",      "#06B6D4"),
        ("attributed_conversions","Attributed Conv.", "#10B981"),
    ]
    for col, label, color in stage_defs:
        fig2.add_trace(go.Bar(name=label, x=df_top["campaign"], y=df_top[col], marker_color=color))
    fig2.update_layout(
        barmode="group", template="plotly_dark",
        plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", height=450,
        xaxis_title="Campaign", yaxis_title="Count",
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3: Post-click vs post-view split ─────────────────────────────────
with tab3:
    st.markdown('<div class="sec-header">Share of Conversions Preceded by a Click</div>', unsafe_allow_html=True)
    st.caption(
        "A conversion is 'post-click' if any impression in that conversion path had a click. "
        "Otherwise it is 'post-view'. Neither is inherently better — post-view shows brand impact."
    )

    if "share_conversions_with_click" not in df_f.columns:
        st.info("Column `share_conversions_with_click` not in funnel CSV. Check 04_funnel.sql.")
    else:
        df_pv = df_f.dropna(subset=["share_conversions_with_click"]).copy()
        df_pv = df_pv.nlargest(20, "conversions")
        df_pv["post_view_share"] = 1 - df_pv["share_conversions_with_click"]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Post-Click", x=df_pv["campaign"],
                              y=df_pv["share_conversions_with_click"], marker_color="#06B6D4"))
        fig3.add_trace(go.Bar(name="Post-View",  x=df_pv["campaign"],
                              y=df_pv["post_view_share"], marker_color="#7C3AED"))
        fig3.update_layout(
            barmode="stack", template="plotly_dark",
            plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
            font_color="#E2E8F0", height=420,
            xaxis_title="Campaign", yaxis_title="Share of Conversions",
            yaxis=dict(tickformat=".0%"),
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig3, use_container_width=True)

        overall_click_share = (
            df_f["conversions_with_click"].sum() / df_f["conversions"].sum()
            if "conversions_with_click" in df_f.columns else None
        )
        if overall_click_share is not None:
            st.metric("Overall post-click share", f"{overall_click_share:.1%}")
