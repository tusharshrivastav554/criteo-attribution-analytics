"""pages/4_Frequency_Analysis.py -- Conversion rate by ad frequency bucket."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Frequency Analysis", page_icon="🔁", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.sec-header{font-size:1.2rem;font-weight:700;color:#E2E8F0;
  border-left:4px solid #7C3AED;padding-left:.75rem;margin:1.6rem 0 .8rem;}
.caveat-box{background:#1C1917;border:1px solid #78350F;border-radius:10px;padding:.9rem 1.1rem;margin:.6rem 0;}
#MainMenu,footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"

@st.cache_data
def load_freq():
    p = RESULTS / "frequency_buckets.csv"
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_top5():
    p = RESULTS / "frequency_top5_campaigns.csv"
    return pd.read_csv(p) if p.exists() else None

df_freq = load_freq()
df_top5 = load_top5()

st.title("🔁 Frequency Analysis")
st.caption(
    "Does conversion rate change with how many times a user sees a campaign's ads? "
    "Measured at the user–campaign level (not impression by impression)."
)

if df_freq is None:
    st.error("Missing `results/frequency_buckets.csv` — run `python run_all.py` first.")
    st.stop()

df_freq["conv_rate_pct"] = df_freq["conv_rate"] * 100

tab1, tab2 = st.tabs(["📊 Overall Frequency Curve", "🏆 Per-Campaign Breakdown"])

# ── Tab 1: Overall frequency vs conversion rate ───────────────────────────
with tab1:
    st.markdown('<div class="sec-header">Conversion Rate by Frequency Bucket</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_freq["freq_bucket"], y=df_freq["conv_rate_pct"],
        name="Conv. Rate (%)", marker_color="#7C3AED", opacity=0.85,
        text=df_freq["user_campaign_pairs"].apply(lambda v: f"n={v:,}"),
        textposition="outside",
    ))
    # Overlay line for trend
    fig.add_trace(go.Scatter(
        x=df_freq["freq_bucket"], y=df_freq["conv_rate_pct"],
        mode="lines+markers", name="Trend",
        line=dict(color="#06B6D4", width=2.5),
        marker=dict(size=8, color="#06B6D4"),
    ))
    fig.update_layout(
        template="plotly_dark", plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", height=430,
        xaxis_title="Frequency Bucket (impressions per user per campaign)",
        yaxis_title="Conversion Rate (%)",
        legend=dict(orientation="h", y=1.08),
        title="Conversion rate rises with frequency — but is this causal?",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.dataframe(
        df_freq[["freq_bucket","user_campaign_pairs","conv_rate"]].rename(columns={
            "freq_bucket":"Frequency Bucket",
            "user_campaign_pairs":"User-Campaign Pairs",
            "conv_rate":"Conversion Rate",
        }),
        use_container_width=True, hide_index=True,
        column_config={"Conversion Rate": st.column_config.NumberColumn(format="%.4f")},
    )

    st.markdown(
        '<div class="caveat-box">'
        "<b>⚠️ Correlation, not causation.</b> Users who see many ads likely differ "
        "from users who see few — they may browse more or have higher purchase intent. "
        "This pattern does <i>not</i> prove that more impressions <i>cause</i> more conversions. "
        "A frequency-cap A/B test is needed to establish causality."
        "</div>", unsafe_allow_html=True,
    )

# ── Tab 2: Per-campaign frequency breakdown ───────────────────────────────
with tab2:
    st.markdown('<div class="sec-header">Top Campaigns — Frequency × Conversion Rate</div>', unsafe_allow_html=True)

    if df_top5 is None:
        st.info("No per-campaign frequency data found (`results/frequency_top5_campaigns.csv`).")
    else:
        df_top5["campaign"] = df_top5["campaign"].astype(str)
        df_top5["conv_rate_pct"] = df_top5["conv_rate"] * 100

        campaigns = sorted(df_top5["campaign"].unique())
        selected  = st.multiselect("Select campaigns", campaigns, default=campaigns[:5])

        if selected:
            df_sel = df_top5[df_top5["campaign"].isin(selected)]
            fig2 = px.line(
                df_sel, x="freq_bucket", y="conv_rate_pct",
                color="campaign", markers=True,
                labels={"freq_bucket":"Freq Bucket","conv_rate_pct":"Conv Rate (%)","campaign":"Campaign"},
                template="plotly_dark", height=430,
            )
            fig2.update_layout(
                plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                font_color="#E2E8F0",
                title="Does the frequency–conversion pattern hold within individual campaigns?",
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("Small bucket sizes give noisy rates. Report n (pair count) alongside each rate.")
        else:
            st.info("Select at least one campaign above.")
