"""pages/5_Conversion_Lag.py -- Time from impression/click to conversion."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Conversion Lag", page_icon="⏱️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.sec-header{font-size:1.2rem;font-weight:700;color:#E2E8F0;
  border-left:4px solid #7C3AED;padding-left:.75rem;margin:1.6rem 0 .8rem;}
.insight-box{background:#1E1B4B;border:1px solid #4338CA;border-radius:10px;padding:.9rem 1.1rem;margin:.6rem 0;}
#MainMenu,footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"

@st.cache_data
def load_lag():
    p = RESULTS / "conversion_lag_buckets.csv"
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_click_lag():
    p = RESULTS / "click_to_conv_lag.csv"
    return pd.read_csv(p) if p.exists() else None

df_lag  = load_lag()
df_clk  = load_click_lag()

st.title("⏱️ Conversion Lag Analysis")
st.caption(
    "Distribution of time from impression (or last click) to conversion. "
    "This directly informs the right attribution window for your measurement setup."
)

if df_lag is None:
    st.error("Missing `results/conversion_lag_buckets.csv` — run `python run_all.py` first.")
    st.stop()

tab1, tab2 = st.tabs(["🕐 Impression-to-Conversion Lag", "🖱️ Click-to-Conversion Lag"])

# ── Tab 1: Impression-to-conversion ───────────────────────────────────────
with tab1:
    st.markdown('<div class="sec-header">How long after seeing an ad do users convert?</div>', unsafe_allow_html=True)

    total_conv = df_lag["conversions"].sum()
    df_lag["cum_share"] = df_lag["conversions"].cumsum() / total_conv * 100

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_lag["lag_bucket"], y=df_lag["conversions"],
        name="Conversions", marker_color="#7C3AED", opacity=0.85,
        text=df_lag["conversions"].apply(lambda v: f"{v:,}"),
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=df_lag["lag_bucket"], y=df_lag["cum_share"],
        name="Cumulative %", mode="lines+markers",
        line=dict(color="#06B6D4", width=2.5),
        marker=dict(size=8), yaxis="y2",
    ))
    fig.update_layout(
        template="plotly_dark", plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", height=430,
        xaxis_title="Time from Impression to Conversion",
        yaxis=dict(title="Distinct Conversions"),
        yaxis2=dict(title="Cumulative Share (%)", overlaying="y", side="right",
                    range=[0, 105], ticksuffix="%"),
        legend=dict(orientation="h", y=1.08),
        title="Impression-to-conversion lag distribution with cumulative coverage",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Percentile callouts
    c1, c2, c3 = st.columns(3)
    within_1d  = df_lag[df_lag["lag_bucket"].isin(["1. le1h","2. 1h-1d"])]["conversions"].sum()
    within_7d  = df_lag[~df_lag["lag_bucket"].isin(["5. 7d-14d","6. 14d-30d","7. gt30d"])]["conversions"].sum()
    beyond_7d  = total_conv - within_7d

    c1.metric("Conversions within 1 day",  f"{within_1d / total_conv:.1%}")
    c2.metric("Conversions within 7 days", f"{within_7d / total_conv:.1%}")
    c3.metric("Conversions beyond 7 days", f"{beyond_7d / total_conv:.1%}")

    st.dataframe(
        df_lag[["lag_bucket","conversions","touchpoints","avg_lag_hours","min_lag_hours","max_lag_hours"]].rename(columns={
            "lag_bucket":"Time Window","conversions":"Distinct Conversions",
            "touchpoints":"Touchpoints","avg_lag_hours":"Avg Lag (h)",
            "min_lag_hours":"Min Lag (h)","max_lag_hours":"Max Lag (h)",
        }),
        use_container_width=True, hide_index=True,
        column_config={
            "Avg Lag (h)": st.column_config.NumberColumn(format="%.1f"),
            "Min Lag (h)": st.column_config.NumberColumn(format="%.2f"),
            "Max Lag (h)": st.column_config.NumberColumn(format="%.1f"),
        }
    )

    st.markdown(
        '<div class="insight-box">'
        "<b>Attribution window implication:</b> If most conversions fall within N days, "
        "then a window shorter than N days will miss real conversions and undercount campaign value. "
        "Conversely, a window far longer than the peak lag risks counting unrelated conversions."
        "</div>", unsafe_allow_html=True,
    )

# ── Tab 2: Click-to-conversion lag ────────────────────────────────────────
with tab2:
    st.markdown('<div class="sec-header">How long after clicking do users convert?</div>', unsafe_allow_html=True)

    if df_clk is None:
        st.info("No click-lag data yet — run `python run_all.py` to generate `results/click_to_conv_lag.csv`.")
    else:
        total_clk = df_clk["conversions"].sum()
        df_clk["share"] = df_clk["conversions"] / total_clk

        fig2 = px.bar(
            df_clk, x="click_lag_bucket", y="conversions",
            color="share", color_continuous_scale=["#4F46E5","#06B6D4"],
            text=df_clk["conversions"].apply(lambda v: f"{v:,}"),
            labels={"click_lag_bucket":"Time Since Last Click","conversions":"Distinct Conversions"},
            template="plotly_dark", height=380,
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
            font_color="#E2E8F0", coloraxis_showscale=False,
            title="Click-to-conversion lag — only conversions with a prior click",
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Only includes conversions where `time_since_last_click` is non-null (i.e., a click was recorded). "
            "Post-view conversions are excluded from this tab."
        )
