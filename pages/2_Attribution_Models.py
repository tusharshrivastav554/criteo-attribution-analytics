"""pages/2_Attribution_Models.py -- Compare 4 attribution models."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Attribution Models", page_icon="🔀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.sec-header{font-size:1.2rem;font-weight:700;color:#E2E8F0;
  border-left:4px solid #7C3AED;padding-left:.75rem;margin:1.6rem 0 .8rem;}
.insight-box{background:#1E1B4B;border:1px solid #4338CA;border-radius:10px;padding:1rem 1.2rem;margin:.6rem 0;}
#MainMenu,footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results"

@st.cache_data
def load_models():
    p = RESULTS / "attribution_model_comparison.csv"
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_shifts():
    p = RESULTS / "attribution_rank_shifts.csv"
    return pd.read_csv(p) if p.exists() else None

df_models = load_models()
df_shifts  = load_shifts()

st.title("🔀 Attribution Model Comparison")
st.caption(
    "How last-touch, first-touch, linear, and time-decay (7-day half-life) assign credit "
    "to campaigns — and which campaigns are most sensitive to the measurement choice."
)

if df_models is None:
    st.error("Missing `results/attribution_model_comparison.csv`. Run `python run_all.py` first.")
    st.stop()

df_models["campaign"] = df_models["campaign"].astype(str)
if df_shifts is not None:
    df_shifts["campaign"] = df_shifts["campaign"].astype(str)

tab1, tab2, tab3 = st.tabs(["📊 Credit by Model", "🔄 Rank Shifts", "📋 Full Table"])

# ── Tab 1: Grouped bar — credit under each model ──────────────────────────
with tab1:
    n = st.slider("Top N campaigns by last-touch credit", 5, 30, 15, key="attr_n")
    df_top = df_models.head(n).copy()

    credit_cols = ["credit_last_touch","credit_first_touch","credit_linear","credit_time_decay"]
    model_names = ["Last-Touch","First-Touch","Linear","Time-Decay (7d)"]
    palette     = ["#7C3AED","#06B6D4","#10B981","#F59E0B"]

    fig = go.Figure()
    for col, name, color in zip(credit_cols, model_names, palette):
        fig.add_trace(go.Bar(
            name=name, x=df_top["campaign"], y=df_top[col],
            marker_color=color, opacity=0.88,
        ))
    fig.update_layout(
        barmode="group", template="plotly_dark",
        plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", height=460,
        xaxis_title="Campaign", yaxis_title="Attribution Credit (fractional conversions)",
        legend=dict(orientation="h", y=1.08),
        title="Attribution credit by model — top campaigns by last-touch",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Each bar shows how many fractional conversions that campaign receives under each model. "
        "Large differences between bars signal measurement-rule sensitivity."
    )

# ── Tab 2: Rank shifts ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="sec-header">Campaigns Most Sensitive to Measurement Choice</div>', unsafe_allow_html=True)

    if df_shifts is None:
        st.info("Run `python run_all.py` to generate rank-shift data.")
    else:
        n2 = st.slider("Top N campaigns by max rank shift", 5, 30, 15, key="shift_n")
        df_sh = df_shifts.head(n2).copy()

        # Diverging bar: last-touch rank vs time-decay rank
        df_sh = df_sh.sort_values("max_rank_shift", ascending=False)
        df_sh["delta"] = df_sh["rank_last"] - df_sh["rank_timedecay"]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Last-Touch Rank",   x=df_sh["campaign"], y=df_sh["rank_last"],
            marker_color="#7C3AED", opacity=0.85,
        ))
        fig2.add_trace(go.Bar(
            name="Time-Decay Rank",   x=df_sh["campaign"], y=df_sh["rank_timedecay"],
            marker_color="#F59E0B", opacity=0.85,
        ))
        fig2.update_layout(
            barmode="group", template="plotly_dark",
            plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
            font_color="#E2E8F0", height=400,
            xaxis_title="Campaign", yaxis_title="Rank (1 = most credit)",
            yaxis_autorange="reversed",
            title="Rank comparison: Last-Touch vs Time-Decay (biggest movers first)",
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="sec-header">Max Rank Shift by Campaign</div>', unsafe_allow_html=True)
        fig3 = px.bar(
            df_shifts.head(20).sort_values("max_rank_shift", ascending=True),
            x="max_rank_shift", y="campaign", orientation="h",
            color="max_rank_shift", color_continuous_scale=["#4F46E5","#EF4444"],
            labels={"max_rank_shift":"Max Rank Shift Across Models","campaign":"Campaign"},
            template="plotly_dark", height=420,
        )
        fig3.update_layout(plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
                           font_color="#E2E8F0", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown(
            '<div class="insight-box">'
            "<b>Insight:</b> A large rank shift means this campaign's measured value depends heavily "
            "on which attribution rule you choose. These are the highest-priority campaigns "
            "to investigate with an experiment before cutting or scaling budget."
            "</div>", unsafe_allow_html=True
        )

# ── Tab 3: Full table ──────────────────────────────────────────────────────
with tab3:
    st.dataframe(
        df_models, use_container_width=True, hide_index=True,
        column_config={
            "credit_last_touch":  st.column_config.NumberColumn("Last-Touch",       format="%.2f"),
            "credit_first_touch": st.column_config.NumberColumn("First-Touch",      format="%.2f"),
            "credit_linear":      st.column_config.NumberColumn("Linear",           format="%.2f"),
            "credit_time_decay":  st.column_config.NumberColumn("Time-Decay (7d)",  format="%.2f"),
        }
    )
    st.caption(
        "Credits are fractional conversions. Rank 1 = campaign receiving the most credit under that model. "
        "The four credit columns for each campaign sum to its total touchpoint count."
    )
