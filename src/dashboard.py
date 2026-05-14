import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from datetime import datetime, timedelta
from src.neo_ws_client import NeoWsClient, HIGH_RISK_THRESHOLD
from src.data_processing import (
    get_or_fetch,
    stats,
    risk_time_series,
    closest_approach_ranking,
    highest_risk_ranking,
    DATA_DIR,
)
from src.translations import t, set_locale, get_locale, LANGUAGES

st.set_page_config(
    page_title="ASTEROIDADVISOR",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

client = NeoWsClient()

CUSTOM_CSS = """
<style>
/* === SOLARBALLS-INSPIRED SPACE THEME === */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

.stApp {
    background: linear-gradient(145deg, #070b1a 0%, #0d1b3e 25%, #150a2e 50%, #0a0e27 75%, #070b1a 100%);
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image:
        radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 25% 5%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.5px 1.5px at 5% 45%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 40% 10%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.5px 1.5px at 55% 30%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 70% 15%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 85% 35%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.5px 1.5px at 15% 60%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 35% 75%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 50% 55%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.5px 1.5px at 65% 80%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 80% 65%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 90% 50%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.5px 1.5px at 20% 90%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 45% 85%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 75% 95%, rgba(255,255,255,0.4), transparent);
    pointer-events: none;
    z-index: 0;
}

.stApp header { height: 0 !important; }
.main .block-container { padding-top: 1rem; padding-bottom: 1rem; position: relative; z-index: 1; min-height: 100vh; }
.stElementContainer { min-height: 100vh; overflow: hidden; }
section[data-testid="stMain"] { min-height: 100vh; overflow: hidden; }

/* === CARDS === */
div[data-testid="stMetric"],
div[data-testid="stDataFrame"],
div[data-testid="stTable"],
.stPlotlyChart,
div.stTabs {
    background: rgba(15,20,50,0.5) !important;
    border: 1px solid rgba(100,150,255,0.1) !important;
    border-radius: 14px !important;
    padding: 0.75rem !important;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03);
    transition: border-color 0.3s, box-shadow 0.3s;
}
div[data-testid="stMetric"]:hover,
.stPlotlyChart:hover {
    border-color: rgba(100,150,255,0.25) !important;
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), 0 0 24px rgba(100,150,255,0.06);
}

/* === METRICS === */
div[data-testid="stMetric"] {
    padding: 1rem 0.75rem !important;
}
div[data-testid="stMetricLabel"] {
    color: #7a8fbf !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px;
}
div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    color: #e8eeff !important;
    font-weight: 700 !important;
    text-shadow: 0 0 30px rgba(100,150,255,0.15);
}

/* === TYPOGRAPHY === */
h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; }
h3, h4, h5, h6 {
    color: #d0ddff !important;
    letter-spacing: 0.5px;
}
h3 {
    border-bottom: 1px solid rgba(100,150,255,0.12);
    padding-bottom: 10px;
    margin-top: 0.5rem !important;
}
h4 { margin-top: 1.8rem !important; margin-bottom: 0.8rem !important; }
h5 { margin-top: 1.4rem !important; margin-bottom: 0.6rem !important; }
.stMarkdown p, .stMarkdown li, .stMarkdown span {
    color: #b0c4de;
}
.stCaption, .stCaption p {
    color: #5a6f8f !important;
}

/* === BUTTONS === */
.stButton button {
    background: linear-gradient(135deg, rgba(30,60,120,0.6), rgba(50,20,80,0.6)) !important;
    border: 1px solid rgba(100,150,255,0.2) !important;
    color: #b8ccff !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.3s !important;
    backdrop-filter: blur(4px);
}
.stButton button:hover {
    background: linear-gradient(135deg, rgba(40,80,160,0.7), rgba(70,30,110,0.7)) !important;
    border-color: rgba(100,150,255,0.4) !important;
    box-shadow: 0 0 28px rgba(100,150,255,0.12);
    color: #d0ddff !important;
}

/* === INPUTS === */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input {
    background: rgba(10,15,40,0.7) !important;
    border: 1px solid rgba(100,150,255,0.12) !important;
    color: #c8d8ff !important;
    border-radius: 10px !important;
    caret-color: #6a8fff;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(100,150,255,0.4) !important;
    box-shadow: 0 0 16px rgba(100,150,255,0.08);
}

/* === SELECTBOX DROPDOWN === */
div[data-baseweb="select"] div[data-baseweb="popover"] {
    background: rgba(10,15,40,0.95) !important;
    border: 1px solid rgba(100,150,255,0.15) !important;
    backdrop-filter: blur(12px);
}

/* === TABS === */
div[data-testid="stTabs"] button {
    color: #7a8fbf !important;
    font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.3s;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #8ab4ff !important;
    border-bottom-color: #6a8fff !important;
}

/* === CHECKBOX / TOGGLE === */
div[data-testid="stCheckbox"] label span {
    color: #b0c4de;
}

/* === SLIDER === */
div[data-testid="stSlider"] div[data-testid="stTickBar"] {
    color: #5a6f8f;
}

/* === BADGES === */
.badge { display: inline-block; padding: 3px 12px; border-radius: 14px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
.badge-high { background: linear-gradient(135deg, #b71c1c, #ff5252); color: #fff; box-shadow: 0 0 16px rgba(255,82,82,0.3); }
.badge-medium { background: linear-gradient(135deg, #e65100, #ffb74d); color: #000; box-shadow: 0 0 12px rgba(255,183,77,0.2); }
.badge-low { background: linear-gradient(135deg, #f57f17, #fff176); color: #000; }
.badge-none { background: linear-gradient(135deg, #1b5e20, #4caf50); color: #fff; }

/* === PLOTLY CHARTS === */
.stPlotlyChart { margin-top: 0.5rem !important; }

/* === DATA FRAME === */
div[data-testid="stDataFrame"] div[data-testid="stDataFrame"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* === SPINNER === */
div[data-testid="stSpinner"] {
    color: #8ab4ff;
}

/* === DIVIDER === */
hr {
    border-color: rgba(100,150,255,0.08) !important;
    margin: 1.5rem 0 !important;
}

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background: rgba(7,11,26,0.95) !important;
    border-right: 1px solid rgba(100,150,255,0.08);
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 3px; }
::-webkit-scrollbar-thumb { background: rgba(100,150,255,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100,150,255,0.35); }

/* === RESPONSIVE === */
@media (max-width: 640px) {
    .main .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
}
</style>
"""


def render_risk_badge(label):
    cls = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low", "NONE": "badge-none"}
    return f'<span class="badge {cls.get(label, "badge-none")}">{label}</span>'


def build_risk_gauge(score, threshold=HIGH_RISK_THRESHOLD):
    color = "#4CAF50" if score < 0.2 else "#FFF176" if score < threshold else "#FFB74D" if score < 0.8 else "#FF5252"
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"valueformat": ".3f", "font": {"size": 24, "color": color}},
        gauge={
            "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "#555", "tickvals": [0, 0.2, threshold, 0.8, 1]},
            "bar": {"color": color, "thickness": 0.3},
            "steps": [
                {"range": [0, 0.2], "color": "#1B5E20"},
                {"range": [0.2, threshold], "color": "#F57F17"},
                {"range": [threshold, 0.8], "color": "#E65100"},
                {"range": [0.8, 1], "color": "#B71C1C"},
            ],
            "threshold": {
                "line": {"color": "#fff", "width": 3},
                "thickness": 0.6,
                "value": score,
            },
        },
    ))


def build_github_heatmap(ts, threshold=HIGH_RISK_THRESHOLD):
    if ts.empty or "date" not in ts.columns:
        return None

    df = ts.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return None
    df["dow"] = df["date"].dt.dayofweek
    first_week = df["date"].min().isocalendar()[1]
    df["week"] = df["date"].apply(lambda d: d.isocalendar()[1] - first_week)
    df["week"] = df["week"] - df["week"].min()

    if df.empty:
        return None

    weeks = int(df["week"].max()) + 1
    grid = [[None] * 7 for _ in range(weeks)]
    hover = [[""] * 7 for _ in range(weeks)]
    for _, r in df.iterrows():
        w, d = int(r["week"]), int(r["dow"])
        grid[w][d] = r["avg_risk"]
        hover[w][d] = (
            f"{r['date'].strftime('%Y-%m-%d')}<br>"
            f"{t('detail.avg_risk_hover_avg', v=r['avg_risk'])}<br>"
            f"{t('detail.avg_risk_hover_max', v=r['max_risk'])}<br>"
            f"{t('detail.avg_risk_hover_count', n=r['count'])}<br>"
            f"{t('detail.avg_risk_hover_high', n=int(r['high_risk_count']))}"
        )

    dow_labels = [t("dow.mon"), t("dow.tue"), t("dow.wed"), t("dow.thu"), t("dow.fri"), t("dow.sat"), t("dow.sun")]
    fig = go.Figure(data=go.Heatmap(
        z=grid,
        x=dow_labels,
        y=[t("risk.week", n=i+1) for i in range(weeks)],
        text=hover,
        hoverinfo="text",
        colorscale=[
            [0.0, "#1B5E20"],
            [0.2, "#4CAF50"],
            [0.4, "#FFF176"],
            [0.6, "#FFB74D"],
            [0.8, "#FF5252"],
            [1.0, "#B71C1C"],
        ],
        zmin=0,
        zmax=1,
        showscale=True,
        colorbar=dict(title=t("risk.heatmap_avg"), len=0.7),
    ))
    fig.update_layout(
        title=t("risk.heatmap_title"),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=10)),
        margin=dict(t=100, b=10, l=10, r=10),
        height=max(200, weeks * 28 + 60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, side="top")
    fig.update_yaxes(showgrid=False)
    return fig


def build_closest_table(ranking):
    if ranking.empty:
        return None
    display = ranking[
        ["rank", "name", "date", "miss_distance_km",
         "miss_ld", "diameter_avg_m", "velocity_kmh",
         "risk_score", "is_high_risk", "is_hazardous"]
    ].copy()
    display["risk_score"] = display["risk_score"].apply(lambda x: f"{x:.3f}")
    display["is_high_risk"] = display["is_high_risk"].apply(
        lambda x: t("table.high") if x else "✅"
    )
    display["is_hazardous"] = display["is_hazardous"].apply(
        lambda x: t("table.yes") if x else t("table.no")
    )
    display.columns = [
        t("table.col_rank"), t("table.col_name"), t("table.col_date"),
        t("table.col_miss_km"), t("table.col_miss_ld"),
        t("table.col_diam"), t("table.col_speed"),
        t("table.col_risk"), t("table.col_high_risk"), t("table.col_pho"),
    ]
    return display


def main():
    with st.sidebar:
        lang = st.selectbox(
            t("lang.select"),
            options=list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k],
            key="lang_selector",
        )
        set_locale(lang)
        st.markdown("---")

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    tab_feed, tab_browse, tab_cache, tab_about = st.tabs(
        [t("tab.feed"), t("tab.browse"), t("tab.cache"), t("tab.about")]
    )

    with tab_feed:
        render_feed()
    with tab_browse:
        render_browse()
    with tab_cache:
        render_cache()
    with tab_about:
        render_about()


def render_feed():
    st.markdown(t("feed.title"))

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_date = st.date_input(t("date.start"), datetime.now(), key="feed_start")
    with col2:
        end_date = st.date_input(t("date.end"), datetime.now() + timedelta(days=30), key="feed_end")
    with col3:
        force_refresh = st.checkbox(t("force_refresh"), value=False)

    if start_date > end_date:
        st.error(t("start_before_end"))
        return

    sd = start_date.strftime("%Y-%m-%d")
    ed = end_date.strftime("%Y-%m-%d")

    status_placeholder = st.empty()
    progress_placeholder = st.empty()

    with st.spinner(t("spinner.loading")):
        try:
            def progress_cb(cs, ce):
                progress_placeholder.info(t("fetching", start=cs, end=ce))

            df, info = get_or_fetch(sd, ed, force_refresh=force_refresh)
            progress_placeholder.empty()

            if df is None or df.empty:
                st.warning(t("no_asteroids_range"))
                return

            if info["source"] == "csv":
                status_placeholder.caption(t("source.csv"))
            elif info.get("from_cache"):
                status_placeholder.caption(
                    t("source.cache", cached=info["cached_chunks"], total=info["chunks"])
                )
            else:
                status_placeholder.caption(
                    t("source.api", n=info["chunks"])
                )
        except Exception as e:
            st.error(t("failed", error=e))
            return

    s = stats(df)
    render_summary(df, s)
    st.markdown("---")
    threshold = render_risk_section(df, key_suffix="feed")
    st.markdown("---")
    render_charts(df)
    st.markdown("---")
    render_data_table(df, key_suffix="feed", threshold=threshold)


def render_browse():
    st.markdown(t("browse.title"))

    col1, col2 = st.columns([1, 1])
    with col1:
        page = st.number_input(t("page"), min_value=0, value=0, step=1, key="browse_page")
    with col2:
        page_size = st.selectbox(t("per_page"), [10, 20, 50], index=1, key="browse_size")

    with st.spinner(t("spinner.loading")):
        try:
            from src.neo_ws_client import flatten_browse
            raw, from_cache = client.browse(page=page, size=page_size)
            records = flatten_browse(raw)
            if not records:
                st.warning(t("no_asteroids"))
                return
            df = pd.DataFrame(records)
        except Exception as e:
            st.error(t("failed", error=e))
            return

    total = raw.get("page", {}).get("total_elements", len(records))
    icon = "📦" if from_cache else "🌍"
    st.caption(t("page_info", icon=icon, page=page, count=len(records), total=total))

    s = stats(df)
    render_summary(df, s)
    st.markdown("---")
    threshold = render_risk_section(df, key_suffix="browse")
    st.markdown("---")
    render_charts(df)
    st.markdown("---")
    render_data_table(df, key_suffix="browse", threshold=threshold)


def render_cache():
    st.markdown(t("cache.title"))
    col1, col2, col3 = st.columns(3)
    with col1:
        raw_files = list(client.cache.cache_dir.glob("*.json"))
        st.metric(t("cache.raw_files"), len(raw_files))
    with col2:
        csv_files = list(DATA_DIR.glob("*.csv"))
        st.metric(t("cache.csv_files"), len(csv_files))
    with col3:
        total_rows = sum(len(pd.read_csv(f)) for f in csv_files) if csv_files else 0
        st.metric(t("cache.total_rows"), total_rows)

    st.markdown(t("cache.pipeline_title"))
    st.markdown(t("cache.pipeline"))

    if csv_files:
        st.markdown(t("cache.csv_section"))
        meta = []
        for p in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True):
            meta.append({
                "file": p.name,
                "size_kb": p.stat().st_size / 1024,
                "rows": len(pd.read_csv(p)),
            })
        st.dataframe(
            pd.DataFrame(meta),
            column_config={
                "file": t("cache.filename"),
                "size_kb": st.column_config.NumberColumn(t("cache.size_kb"), format="%.1f"),
                "rows": t("cache.rows"),
            },
            width='stretch',
            hide_index=True,
        )

    if raw_files or csv_files:
        if st.button(t("cache.clear_btn")):
            client.cache.clear_all()
            for p in DATA_DIR.glob("*.csv"):
                p.unlink()
            st.rerun()


def render_about():
    st.markdown(f"""### {t("about.title")}

{t("about.fetches")}

{t("about.risk_scoring")}

{t("about.default_threshold")}

{t("about.pipeline_title")}
{t("about.pipeline_lines")}

{t("about.sources_title")}
{t("about.sources_lines")}

{t("about.limitations_title")}
{t("about.limitations_lines")}
""")


def render_summary(df, s=None):
    if s is None:
        s = stats(df) if not df.empty else {}

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(t("stat.total_neo"), s.get("total", 0))
    m2.metric(t("stat.hazardous"), s.get("hazardous", 0), help=t("stat.hazardous_help"))
    m3.metric(t("stat.high_risk"), s.get("high_risk", 0), help=t("stat.high_risk_help", threshold=HIGH_RISK_THRESHOLD), delta_color="inverse")
    m4.metric(t("stat.avg_velocity"), f"{s.get('avg_velocity_kmh', 0):,.0f} km/h")
    m5.metric(t("stat.avg_risk"), f"{s.get('avg_risk', 0):.3f}")

    extras = []
    if s.get("closest_name"):
        extras.append(t("stat.closest", name=s["closest_name"], dist=s["closest_km"]))
    if s.get("largest_name"):
        extras.append(t("stat.largest", name=s["largest_name"], size=s["largest_m"]))
    if s.get("fastest_name"):
        extras.append(t("stat.fastest", name=s["fastest_name"], speed=s["fastest_kmh"]))
    if s.get("max_risk"):
        extras.append(t("stat.max_risk", score=s["max_risk"]))
    if extras:
        st.caption(" · ".join(extras))


def render_risk_section(df, key_suffix=""):
    st.markdown(t("risk.title"))

    key = f"global_threshold_{key_suffix}" if key_suffix else "global_threshold"
    threshold = st.slider(
        t("risk.threshold"),
        min_value=0.0, max_value=1.0, value=HIGH_RISK_THRESHOLD, step=0.05,
        key=key,
        help=t("risk.threshold_help"),
    )
    above = (df["risk_score"] >= threshold).sum()
    st.metric(
        t("risk.above", threshold=threshold),
        int(above),
        help=t("risk.percent", pct=above / len(df) * 100),
    )

    st.markdown("<br>", unsafe_allow_html=True)
    ts = risk_time_series(df)

    col_hm, col_ts = st.columns([1, 1])
    with col_hm:
        fig_hm = build_github_heatmap(ts, threshold=threshold)
        if fig_hm:
            st.plotly_chart(fig_hm, width='stretch')

    with col_ts:
        if not ts.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts["date"], y=ts["avg_risk"],
                mode="lines+markers", name=t("risk.avg"),
                line=dict(color="#FFB74D", width=2),
                marker=dict(size=6),
            ))
            fig.add_trace(go.Scatter(
                x=ts["date"], y=ts["max_risk"],
                mode="lines+markers", name=t("risk.max"),
                line=dict(color="#FF5252", width=2, dash="dot"),
                marker=dict(size=6),
            ))
            fig.add_hline(
                y=threshold,
                line_dash="dash", line_color="#fff",
                annotation_text=t("risk.threshold_line", t=threshold),
            )
            fig.update_layout(
                title=t("risk.time_title"),
                xaxis_title=t("risk.date"),
                yaxis_title=t("risk.score"),
                yaxis=dict(range=[0, 1]),
                margin=dict(t=80, b=10, l=10, r=10),
                height=280,
                legend=dict(orientation="h", y=1.12),
            )
            st.plotly_chart(fig, width='stretch')

    st.markdown(t("rankings.title"))
    rank_tabs = st.tabs([t("rankings.closest"), t("rankings.highest")])

    with rank_tabs[0]:
        ranking = closest_approach_ranking(df)
        if not ranking.empty:
            fig_rank = px.bar(
                ranking,
                x="rank", y="miss_distance_km",
                color="risk_score",
                hover_data=["name", "date", "miss_ld", "diameter_avg_m", "velocity_kmh"],
                title=t("rankings.closest_title"),
                labels={"rank": t("rankings.rank"), "miss_distance_km": t("rankings.miss_distance"), "risk_score": t("chart.risk_score")},
                color_continuous_scale="RdYlGn_r",
                range_color=[0, 1],
                text="name",
            )
            fig_rank.update_traces(textposition="outside", textfont_size=10)
            fig_rank.update_layout(
                margin=dict(t=80, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig_rank, width='stretch')

            tbl = build_closest_table(ranking)
            if tbl is not None:
                st.dataframe(tbl, width='stretch', hide_index=True)

    with rank_tabs[1]:
        risk_rank = highest_risk_ranking(df)
        if not risk_rank.empty:
            fig_risk_rank = px.bar(
                risk_rank,
                x="rank", y="risk_score",
                color="risk_score",
                hover_data=["name", "date", "diameter_avg_m", "velocity_kmh", "miss_distance_km"],
                title=t("rankings.highest_title"),
                labels={"rank": t("rankings.rank"), "risk_score": t("chart.risk_score")},
                color_continuous_scale="RdYlGn_r",
                range_color=[0, 1],
                text="name",
            )
            fig_risk_rank.update_traces(textposition="outside", textfont_size=10)
            fig_risk_rank.update_layout(
                margin=dict(t=80, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig_risk_rank, width='stretch')

            st.dataframe(
                risk_rank[["rank", "name", "date", "risk_score", "diameter_avg_m", "velocity_kmh", "miss_distance_km", "is_hazardous"]],
                column_config={
                    "rank": t("rankings.rank"),
                    "name": t("data.name"),
                    "date": t("data.date"),
                    "risk_score": st.column_config.NumberColumn(t("data.risk"), format=".3f"),
                    "diameter_avg_m": st.column_config.NumberColumn(t("data.avg_diam"), format=".1f"),
                    "velocity_kmh": st.column_config.NumberColumn(t("data.speed"), format=".0f"),
                    "miss_distance_km": st.column_config.NumberColumn(t("data.miss_dist"), format=".0f"),
                    "is_hazardous": st.column_config.CheckboxColumn(t("table.col_pho")),
                },
                width='stretch',
                hide_index=True,
            )

    return threshold


def render_charts(df):
    st.markdown(t("charthist.title"))

    c1, c2 = st.columns(2)
    with c1:
        hazardous_counts = df["is_hazardous"].value_counts()
        fig_pie = px.pie(
            values=hazardous_counts.values,
            names=[t("chart.safe"), t("chart.potentially_hazardous")],
            title=t("chart.hazardous_title"),
            color_discrete_sequence=["#4CAF50", "#FF5252"],
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=300)
        fig_pie.update_traces(textposition="outside", textinfo="label+percent")
        st.plotly_chart(fig_pie, width='stretch')

    with c2:
        risk_counts = df["risk_label"].value_counts().reindex(["NONE", "LOW", "MEDIUM", "HIGH"], fill_value=0)
        colors = {"NONE": "#4CAF50", "LOW": "#FFF176", "MEDIUM": "#FFB74D", "HIGH": "#FF5252"}
        fig_risk = px.bar(
            x=risk_counts.index,
            y=risk_counts.values,
            title=t("chart.risk_dist_title"),
            labels={"x": t("chart.risk_level"), "y": t("chart.count")},
            color=risk_counts.index,
            color_discrete_map=colors,
        )
        fig_risk.update_layout(showlegend=False, margin=dict(t=80, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_risk, width='stretch')

    c3, c4 = st.columns(2)
    with c3:
        fig_scatter = px.scatter(
            df,
            x="diameter_avg_m",
            y="velocity_kmh",
            color="risk_score",
            size="diameter_max_m",
            hover_data=["name", "miss_distance_km", "risk_score"],
            title=t("chart.size_vs_speed"),
            labels={
                "diameter_avg_m": t("chart.diameter"),
                "velocity_kmh": t("chart.velocity"),
                "risk_score": t("chart.risk_score"),
            },
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1],
        )
        fig_scatter.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_scatter, width='stretch')

    with c4:
        fig_dist = px.scatter(
            df,
            x="miss_distance_km",
            y="velocity_kmh",
            color="risk_score",
            size="diameter_max_m",
            hover_data=["name", "risk_score"],
            title=t("chart.dist_vs_speed"),
            labels={
                "miss_distance_km": t("data.miss_dist"),
                "velocity_kmh": t("chart.velocity"),
                "risk_score": t("chart.risk_score"),
            },
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1],
        )
        fig_dist.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_dist, width='stretch')

    c5, c6 = st.columns(2)
    with c5:
        fig_hist = px.histogram(
            df,
            x="diameter_avg_m",
            nbins=20,
            title=t("chart.size_dist_title"),
            labels={"diameter_avg_m": t("chart.diameter")},
            color_discrete_sequence=["#1E88E5"],
        )
        fig_hist.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_hist, width='stretch')

    with c6:
        fig_speed_hist = px.histogram(
            df,
            x="velocity_kmh",
            nbins=20,
            title=t("chart.speed_dist_title"),
            labels={"velocity_kmh": t("chart.velocity")},
            color_discrete_sequence=["#FF7043"],
        )
        fig_speed_hist.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_speed_hist, width='stretch')

    c7, c8 = st.columns(2)
    with c7:
        fig_lunar = px.bar(
            df.nsmallest(10, "miss_distance_km"),
            x="name",
            y="miss_distance_km",
            color="risk_score",
            title=t("chart.closest_title"),
            labels={"name": "", "miss_distance_km": t("data.miss_dist"), "risk_score": t("chart.risk_score")},
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1],
        )
        fig_lunar.update_layout(
            xaxis_tickangle=-45,
            margin=dict(t=80, b=80, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_lunar, width='stretch')

    with c8:
        top_diam = df.nlargest(10, "diameter_max_m")
        fig_diam = px.bar(
            top_diam,
            x="name",
            y="diameter_max_m",
            color="risk_score",
            title=t("chart.largest_title"),
            labels={"name": "", "diameter_max_m": t("chart.max_diameter"), "risk_score": t("chart.risk_score")},
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1],
        )
        fig_diam.update_layout(
            xaxis_tickangle=-45,
            margin=dict(t=80, b=80, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_diam, width='stretch')

    c9, c10 = st.columns(2)
    with c9:
        fig_risk_dist = px.histogram(
            df,
            x="risk_score",
            nbins=20,
            title=t("chart.risk_score_dist_title"),
            labels={"risk_score": t("chart.risk_score_range")},
            color_discrete_sequence=["#FF5252"],
        )
        fig_risk_dist.add_vline(
            x=HIGH_RISK_THRESHOLD,
            line_dash="dash", line_color="#fff",
            annotation_text=t("risk.threshold_line", t=HIGH_RISK_THRESHOLD),
        )
        fig_risk_dist.update_layout(margin=dict(t=80, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_risk_dist, width='stretch')

    with c10:
        top_speed = df.nlargest(10, "velocity_kmh")
        fig_speed = px.bar(
            top_speed,
            x="name",
            y="velocity_kmh",
            color="risk_score",
            title=t("chart.fastest_title"),
            labels={"name": "", "velocity_kmh": t("chart.velocity"), "risk_score": t("chart.risk_score")},
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1],
        )
        fig_speed.update_layout(
            xaxis_tickangle=-45,
            margin=dict(t=80, b=80, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_speed, width='stretch')


def render_data_table(df, key_suffix="", threshold=HIGH_RISK_THRESHOLD):
    st.markdown(t("data.title"))

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search = st.text_input(t("data.search"), placeholder=t("data.search_placeholder"), key=f"search_{key_suffix}" if key_suffix else "search")
    with col_f2:
        risk_filter = st.selectbox(t("data.risk_filter"), ["All", "HIGH_RISK", "HIGH", "MEDIUM", "LOW", "NONE"], index=0, key=f"risk_filter_{key_suffix}" if key_suffix else "risk_filter")
    with col_f3:
        risk_range = st.slider(
            t("data.risk_range"),
            min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.05,
            label_visibility="collapsed",
            key=f"risk_range_{key_suffix}" if key_suffix else "risk_range",
        )

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["name"].str.contains(search, case=False, na=False)]
    if risk_filter == "HIGH_RISK":
        filtered = filtered[filtered["is_high_risk"]]
    elif risk_filter != "All":
        filtered = filtered[filtered["risk_label"] == risk_filter]
    filtered = filtered[
        (filtered["risk_score"] >= risk_range[0]) &
        (filtered["risk_score"] <= risk_range[1])
    ]

    display_cols = [
        "name", "date", "diameter_avg_m", "velocity_kmh",
        "miss_distance_km", "risk_score", "is_high_risk",
        "orbiting_body", "risk_label",
    ]
    available = [c for c in display_cols if c in filtered.columns]
    display = filtered[available].copy()

    display["risk_label"] = display["risk_label"].apply(
        lambda x: f"{x} {'⚠️' if x == 'HIGH' else '⚡' if x == 'MEDIUM' else '✓' if x == 'NONE' else ''}"
    )

    col_config = {
        "name": st.column_config.TextColumn(t("data.name"), width="large"),
        "date": st.column_config.TextColumn(t("data.date"), width="small"),
        "diameter_avg_m": st.column_config.NumberColumn(t("data.avg_diam"), format="%.1f", width="small"),
        "velocity_kmh": st.column_config.NumberColumn(t("data.speed"), format="%.0f", width="small"),
        "miss_distance_km": st.column_config.NumberColumn(t("data.miss_dist"), format="%.0f", width="small"),
        "risk_score": st.column_config.NumberColumn(t("data.risk"), format=".3f", width="small"),
        "is_high_risk": st.column_config.CheckboxColumn(t("data.high_risk"), width="small"),
        "orbiting_body": st.column_config.TextColumn(t("data.orbit"), width="small"),
        "risk_label": st.column_config.TextColumn(t("data.label"), width="small"),
    }
    existing_cols = [c for c in col_config if c in display.columns]

    st.dataframe(
        display[existing_cols],
        column_config={k: col_config[k] for k in existing_cols},
        width='stretch',
        hide_index=True,
        height=400,
    )

    st.markdown(t("data.showing", shown=len(display), total=len(df)))

    csv = df.to_csv(index=False)
    st.download_button(
        t("data.download"),
        data=csv,
        file_name=f"asteroids_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"download_{key_suffix}" if key_suffix else "download",
    )

    st.markdown(t("data.details_title"))
    selected = st.selectbox(t("data.select_asteroid"), df["name"].unique(), key=f"detail_select_{key_suffix}" if key_suffix else "detail_select")
    if selected:
        row = df[df["name"] == selected].iloc[0]
        render_detail(row, threshold=threshold)


def render_detail(row, threshold=HIGH_RISK_THRESHOLD):
    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            fig = build_risk_gauge(row["risk_score"], threshold=threshold)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=200, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width='stretch')

        with cols[1]:
            risk_label = row.get("risk_label", "NONE")
            badge = render_risk_badge(risk_label)
            high_risk = t("data.high_risk_label") if row.get("is_high_risk") else t("data.below_threshold")
            hazardous = t("data.hazardous_yes") if row["is_hazardous"] else t("data.hazardous_no")
            st.markdown(f"**{row['name']}** &nbsp; {badge}", unsafe_allow_html=True)
            st.markdown(f"**{high_risk}** (threshold ≥ {threshold})")
            st.markdown(t("data.potentially_hazardous", value=hazardous))
            st.markdown(t("data.close_approach", date=row.get('close_approach_date', row.get('date', 'N/A'))))
            st.markdown(t("data.orbiting_body", body=row.get('orbiting_body', 'N/A')))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("data.diameter_metric"), f"{row.get('diameter_avg_m', 0):.1f} m",
                   help=t("data.diameter_help", min=row.get('diameter_min_m', 0), max=row.get('diameter_max_m', 0)))
        c2.metric(t("data.velocity_metric"), f"{row.get('velocity_kmh', 0):,.0f} km/h")
        c3.metric(t("data.miss_metric"), f"{row.get('miss_distance_km', 0):,.0f} km")
        c4.metric(t("data.risk_metric"), f"{row.get('risk_score', 0):.3f}")


if __name__ == "__main__":
    main()
