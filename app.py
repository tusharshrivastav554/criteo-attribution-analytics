"""
app.py -- Criteo Attribution Analytics Dashboard (Home / Landing Page)
Streamlit multi-page app.  Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Criteo Attribution Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero-title {
    font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 50%, #06B6D4 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.25rem; line-height: 1.2;
}
.hero-sub {
    font-size: 1rem; color: #94A3B8; margin-bottom: 1.5rem; letter-spacing: 0.02em;
}
.kpi-card {
    background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
    border: 1px solid #312E81; border-radius: 14px;
    padding: 1.4rem 1.2rem; text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(124,58,237,0.25); }
.kpi-value  { font-size: 2rem; font-weight: 800; color: #A78BFA; }
.kpi-label  { font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem; }
.sec-header {
    font-size: 1.2rem; font-weight: 700; color: #E2E8F0;
    border-left: 4px solid #7C3AED; padding-left: 0.75rem; margin: 1.8rem 0 0.8rem;
}
.nav-card {
    background: #1E1B4B; border: 1px solid #312E81; border-radius: 12px;
    padding: 1rem 1.1rem; margin-bottom: 0.7rem;
    transition: border-color 0.2s, transform 0.15s;
}
.nav-card:hover { border-color: #7C3AED; transform: translateX(3px); }
.nav-icon  { font-size: 1.6rem; }
.nav-name  { font-weight: 700; color: #C4B5FD; margin: 0.2rem 0 0.1rem; font-size: 0.95rem; }
.nav-desc  { font-size: 0.78rem; color: #94A3B8; line-height: 1.4; }
#MainMenu  { visibility: hidden; }
footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent
RESULTS = ROOT / "results"

@st.cache_data
def load_csv(name: str) -> pd.DataFrame | None:
    p = RESULTS / name
    return pd.read_csv(p) if p.exists() else None

df_camp   = load_csv("campaign_performance.csv")
df_funnel = load_csv("funnel_by_campaign.csv")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">📊 Criteo Attribution Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">'
    'Ad Campaign Efficiency &nbsp;·&nbsp; Attribution Models &nbsp;·&nbsp; '
    'Funnel &nbsp;·&nbsp; Frequency &nbsp;·&nbsp; Conversion Lag &nbsp;·&nbsp; Budget Simulation'
    '</div>',
    unsafe_allow_html=True,
)
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
if df_camp is not None:
    total_impr  = int(df_camp["impressions"].sum())
    n_campaigns = len(df_camp)
    total_conv  = int(df_camp["attributed_conversions"].sum())
    total_spend = df_camp["total_cost"].sum()
    avg_cpac    = total_spend / total_conv if total_conv > 0 else float("nan")

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        (c1, f"{total_impr:,}",    "Impressions (5 % sample)"),
        (c2, f"{n_campaigns}",     "Campaigns (≥1 000 impr.)"),
        (c3, f"{total_conv:,}",    "Attributed Conversions"),
        (c4, f"{avg_cpac:.5f}",    "Avg Cost / Attr. Conv."),
    ]
    for col, val, lbl in kpis:
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
            f'<div class="kpi-label">{lbl}</div></div>',
            unsafe_allow_html=True,
        )
    st.caption("⚠️ Cost values are **transformed** (not real currency) — use for relative comparison only.")
else:
    st.warning("No data yet. Run `python run_all.py` then refresh.")

st.markdown("")

# ── Teaser chart ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Spend Share vs. Conversion Share</div>', unsafe_allow_html=True)

if df_camp is not None:
    df_plot = df_camp.copy()
    df_plot["campaign"]    = df_plot["campaign"].astype(str)
    df_plot["gap"]         = df_plot["spend_share"] - df_plot["conv_share"]

    fig = px.scatter(
        df_plot,
        x="spend_share", y="conv_share",
        size="impressions", size_max=40,
        color="gap",
        color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
        color_continuous_midpoint=0,
        hover_name="campaign",
        hover_data={
            "impressions": True,
            "ctr": ":.3f",
            "attributed_conversions": True,
            "gap": ":.4f",
        },
        labels={"spend_share": "Spend Share", "conv_share": "Conversion Share", "gap": "Spend − Conv Gap"},
        template="plotly_dark",
        height=430,
    )
    lim = max(df_plot["spend_share"].max(), df_plot["conv_share"].max()) * 1.05
    fig.add_shape(type="line", x0=0, y0=0, x1=lim, y1=lim,
                  line=dict(color="#64748B", width=1.2, dash="dot"))
    fig.add_annotation(x=lim * 0.65, y=lim * 0.78,
                       text="Points above = efficient", showarrow=False,
                       font=dict(color="#94A3B8", size=11))
    fig.update_layout(
        plot_bgcolor="#0A0A14", paper_bgcolor="#0A0A14",
        font_color="#E2E8F0", margin=dict(t=20, b=40),
        coloraxis_colorbar=dict(title="Gap", tickformat=".3f"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size ∝ impressions. Red = spend share exceeds conversion share (waste). Hover for details.")
else:
    st.info("Chart will appear after `python run_all.py` is run.")

st.divider()

# ── Navigation cards ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Explore the Dashboard</div>', unsafe_allow_html=True)

pages = [
    ("📈", "1 Campaign Summary",    "Efficiency rankings, top/bottom campaigns, spend vs conversion share."),
    ("🔀", "2 Attribution Models",  "How last-touch, first-touch, linear, and time-decay shift campaign credit."),
    ("🔻", "3 Funnel & Spend",      "Impression → Click → Conversion funnel; post-click vs post-view split."),
    ("🔁", "4 Frequency Analysis",  "Conversion rate by ad frequency bucket; check for diminishing returns."),
    ("⏱️", "5 Conversion Lag",      "Time from impression / click to conversion; informs attribution window."),
    ("💡", "6 Budget Simulation",   "Simulate spend reallocation under explicit constant-efficiency assumptions."),
]

cols = st.columns(3)
for i, (icon, name, desc) in enumerate(pages):
    with cols[i % 3]:
        st.markdown(
            f'<div class="nav-card">'
            f'<div class="nav-icon">{icon}</div>'
            f'<div class="nav-name">{name}</div>'
            f'<div class="nav-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("&nbsp;")
st.caption(
    "**Data:** Criteo Attribution Modeling Dataset — 5 % user sample, ~30 days of live traffic &nbsp;|&nbsp; "
    "**Engine:** DuckDB &nbsp;|&nbsp; "
    "**License:** check Criteo dataset page and credit Criteo in any public use."
)
