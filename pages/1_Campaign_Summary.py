"""pages/1_Campaign_Summary.py -- Efficiency rankings and spend analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Campaign Summary", page_icon="📈", layout="wide")

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
def load() -> pd.DataFrame | None:
    p = RESULTS / "campaign_performance.csv"
    return pd.read_csv(p) if p.exists() else None

df = load()
st.title("📈 Campaign Summary")
st.caption("Efficiency rankings, spend share, and conversion delivery across campaigns (≥1 000 impressions).")

if df is None:
    st.error("Missing `results/campaign_performance.csv` — run `python run_all.py` first.")
    st.stop()

df = df.copy()
df["campaign"]  = df["campaign"].astype(str)
df["gap"]       = df["spend_share"] - df["conv_share"]
df["efficiency"]= df["conv_share"] / df["spend_share"].replace(0, float("nan"))

tab1, tab2, tab3 = st.tabs(["🏆 Efficiency Rankings", "📊 Spend vs Conversions", "📋 Full Table"])

# ── Tab 1: Top / bottom campaigns by CpAC ─────────────────────────────────
with tab1:
    n = st.slider("Campaigns to show at each end", min_value=5, max_value=20, value=10, key="n_camps")
    df_ranked = df.dropna(subset=["cost_per_attr_conv"]).sort_values("cost_per_attr_conv")
    top_n  = df_ranked.head(n)
    bot_n  = df_ranked.tail(n)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="sec-header">✅ Most Efficient</div>', unsafe_allow_html=True)
        fig1 = px.bar(top_n, x="cost_per_attr_conv", y="campaign", orientation="h",
                      color="cost_per_attr_conv", color_continuous_scale=["#059669","#34D399"],
                      labels={"cost_per_attr_conv":"CpAC (transformed)","campaign":"Campaign"},
                      template="plotly_dark", height=380)
        fig1.update_layout(plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                           font_color="#E2E8F0", coloraxis_showscale=False,
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown('<div class="sec-header">⚠️ Least Efficient</div>', unsafe_allow_html=True)
        fig2 = px.bar(bot_n, x="cost_per_attr_conv", y="campaign", orientation="h",
                      color="cost_per_attr_conv", color_continuous_scale=["#F59E0B","#EF4444"],
                      labels={"cost_per_attr_conv":"CpAC (transformed)","campaign":"Campaign"},
                      template="plotly_dark", height=380)
        fig2.update_layout(plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                           font_color="#E2E8F0", coloraxis_showscale=False,
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig2, use_container_width=True)

    st.caption("CpAC = Cost per Attributed Conversion (transformed units — relative use only).")

# ── Tab 2: Spend share vs conversion share scatter ────────────────────────
with tab2:
    st.markdown("Campaigns **above the dashed diagonal** deliver more conversions relative to their spend.")
    fig3 = px.scatter(
        df, x="spend_share", y="conv_share", size="impressions", size_max=45,
        color="gap", color_continuous_scale=["#10B981","#FBBF24","#EF4444"],
        color_continuous_midpoint=0, hover_name="campaign",
        hover_data={"impressions":True,"ctr":":.3f","attributed_conversions":True,"gap":":.4f"},
        labels={"spend_share":"Spend Share","conv_share":"Conversion Share","gap":"Spend − Conv Gap"},
        template="plotly_dark", height=500)
    lim = max(df["spend_share"].max(), df["conv_share"].max()) * 1.08
    fig3.add_shape(type="line", x0=0, y0=0, x1=lim, y1=lim,
                   line=dict(color="#64748B", width=1.2, dash="dot"))
    fig3.update_layout(plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14", font_color="#E2E8F0")
    st.plotly_chart(fig3, use_container_width=True)

    # Summary stats
    waste_camps = (df["gap"] > 0).sum()
    top_waste   = df.nlargest(1,"gap").iloc[0]
    st.info(
        f"**{waste_camps}** of {len(df)} campaigns spend more than their conversion share. "
        f"Biggest gap: campaign **{top_waste['campaign']}** "
        f"(spend {top_waste['spend_share']:.3f} → conv {top_waste['conv_share']:.3f})."
    )

# ── Tab 3: Full data table ────────────────────────────────────────────────
with tab3:
    show_cols = ["campaign","impressions","clicks","ctr","attributed_conversions",
                 "total_cost","cost_per_attr_conv","spend_share","conv_share","efficiency_rank"]
    st.dataframe(
        df[show_cols].sort_values("efficiency_rank"),
        use_container_width=True, hide_index=True,
        column_config={
            "ctr":                st.column_config.NumberColumn("CTR",           format="%.3f"),
            "total_cost":         st.column_config.NumberColumn("Cost (trans.)", format="%.5f"),
            "cost_per_attr_conv": st.column_config.NumberColumn("CpAC (trans.)", format="%.5f"),
            "spend_share":        st.column_config.NumberColumn("Spend Share",   format="%.4f"),
            "conv_share":         st.column_config.NumberColumn("Conv Share",    format="%.4f"),
        }
    )
