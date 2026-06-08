from __future__ import annotations

import html
import textwrap

import pandas as pd
import streamlit as st


THEME_CSS = """
<style>
:root {
    --bg: #f7f8fa;
    --panel: #ffffff;
    --panel-soft: #f3f6f8;
    --line: #d9dee7;
    --text: #111827;
    --muted: #4b5563;
    --accent: #f97316;
    --accent-2: #047857;
    --accent-3: #2563eb;
    --danger: #ef4444;
    --shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
}

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: "Segoe UI", Arial, sans-serif;
}

.stApp::after {
    content: "Lucas Regis | lucaaregis4r@gmail.com";
    position: fixed;
    right: 1.2rem;
    bottom: 0.85rem;
    z-index: 9999;
    padding: 0.32rem 0.55rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.42);
    color: rgba(17, 24, 39, 0.58);
    font-size: 0.72rem;
    font-weight: 700;
    pointer-events: none;
    box-shadow: 0 8px 18px rgba(17, 24, 39, 0.08);
}

[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #f9fafb;
}

div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
div[data-baseweb="input"],
div[data-baseweb="input"] *,
textarea,
input {
    color: #111827 !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #ffffff !important;
    border-color: #d1d5db !important;
}

div[data-baseweb="popover"],
ul[role="listbox"],
div[role="listbox"] {
    background-color: #ffffff !important;
    color: #111827 !important;
}

li[role="option"],
div[role="option"] {
    color: #111827 !important;
    background-color: #ffffff !important;
}

li[role="option"]:hover,
div[role="option"]:hover {
    background-color: #f3f4f6 !important;
}

span[data-baseweb="tag"] {
    background-color: #e0f2fe !important;
    color: #0f172a !important;
}

span[data-baseweb="tag"] *,
[data-testid="stMultiSelect"] span,
[data-testid="stMultiSelect"] div[data-baseweb="tag"] * {
    color: #0f172a !important;
}

/* Streamlit/BaseWeb select contrast guard.
   Keep selected values readable even inside the dark sidebar. */
[data-testid="stSidebar"] div[data-baseweb="select"],
[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] div[data-baseweb="select"] div,
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] p,
[data-testid="stSidebar"] [data-baseweb="select"] [class*="singleValue"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="placeholder"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="valueContainer"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="Input"],
[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border-color: #d1d5db !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] svg,
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #111827 !important;
    fill: #111827 !important;
}

[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"],
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] p {
    background: #dbeafe !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}

[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
    color: #0f172a !important;
    fill: #0f172a !important;
}

[data-baseweb="popover"] div,
[data-baseweb="popover"] span,
[data-baseweb="popover"] p,
[role="listbox"] div,
[role="listbox"] span,
[role="listbox"] p,
[role="option"] div,
[role="option"] span,
[role="option"] p {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

.block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
    max-width: 1380px;
}

.hero-shell {
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 20px 24px 18px 24px;
    background:
        linear-gradient(105deg, rgba(4, 120, 87, 0.10) 0%, transparent 42%),
        linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    box-shadow: var(--shadow);
    margin-bottom: 1.15rem;
}

.hero-kicker {
    display: inline-block;
    color: #ffffff;
    background: #111827;
    border-radius: 999px;
    padding: 0.22rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}

.hero-title {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 2.9rem;
    font-weight: 800;
    letter-spacing: 0;
    line-height: 1.02;
    margin: 0;
}

.hero-subtitle {
    color: var(--muted);
    font-size: 1.05rem;
    max-width: 820px;
    margin-top: 0.7rem;
}

.section-card {
    background: var(--panel);
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.8rem 0.95rem 0.2rem 0.95rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.section-title {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    letter-spacing: 0;
    margin-bottom: 0.2rem;
}

.section-note {
    color: var(--muted);
    margin-bottom: 0.9rem;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    box-shadow: var(--shadow);
    color: var(--text);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
}

div[data-testid="stMetricValue"] {
    color: var(--text);
    font-weight: 800;
    white-space: normal;
    overflow-wrap: anywhere;
}

button[data-baseweb="tab"] {
    background: #ffffff;
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,0.06);
    margin-right: 0.25rem;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #ecfdf5;
    border-color: #047857;
}

button[data-baseweb="tab"] p {
    font-weight: 700;
}

.stDataFrame, .stPlotlyChart {
    border-radius: 8px;
    overflow: hidden;
}

.method-note {
    border-left: 4px solid var(--accent-2);
    background: #ffffff;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    margin: 0.75rem 0;
    color: var(--text);
}

.method-note strong {
    color: var(--text);
}

.report-section {
    margin: 1rem 0 0.65rem 0;
    padding-top: 0.25rem;
}

.report-section h2 {
    color: var(--text);
    font-size: 1.55rem;
    line-height: 1.2;
    margin: 0;
}

.report-section p {
    color: var(--muted);
    margin: 0.3rem 0 0 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.85rem;
    margin: 0.6rem 0 1rem 0;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-left: 4px solid var(--accent-2);
    border-radius: 8px;
    box-shadow: var(--shadow);
    padding: 0.86rem 0.92rem;
    break-inside: avoid;
    page-break-inside: avoid;
}

.metric-card.leader {
    border-left-color: var(--accent);
    background: linear-gradient(180deg, #ffffff 0%, #fff7ed 100%);
}

.metric-label {
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.metric-value {
    color: var(--text);
    font-size: 1.55rem;
    line-height: 1.15;
    font-weight: 800;
    margin-top: 0.18rem;
    overflow-wrap: anywhere;
}

.metric-subtitle {
    color: var(--muted);
    font-size: 0.88rem;
    margin-top: 0.28rem;
}

.player-card-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin: 0.8rem 0 1rem 0;
}

.player-summary-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-top: 5px solid var(--player-color, var(--accent-2));
    border-radius: 8px;
    box-shadow: var(--shadow);
    padding: 1rem;
    break-inside: avoid;
    page-break-inside: avoid;
}

.player-summary-name {
    color: var(--text);
    font-size: 1.25rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 0.75rem;
    overflow-wrap: anywhere;
}

.player-summary-stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.55rem 0.8rem;
}

.player-stat-label {
    color: var(--muted);
    font-size: 0.78rem;
}

.player-stat-value {
    color: var(--text);
    font-weight: 800;
    font-size: 1rem;
}

.pdf-table {
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
    font-size: 0.9rem;
}

.pdf-table th {
    background: #111827;
    color: #ffffff;
    text-align: left;
    padding: 0.48rem 0.55rem;
}

.pdf-table td {
    color: var(--text);
    border-top: 1px solid #e5e7eb;
    padding: 0.45rem 0.55rem;
}

.page-break {
    break-before: page;
    page-break-before: always;
}

@media (max-width: 900px) {
    .hero-title {
        font-size: 2.3rem;
    }
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 640px) {
    .metric-grid,
    .player-card-grid {
        grid-template-columns: 1fr;
    }
}

@media print {
    @page {
        size: A4 landscape;
        margin: 10mm;
    }
    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    header,
    footer {
        display: none !important;
    }
    .block-container {
        max-width: none !important;
        padding: 0 !important;
    }
    .stApp {
        background: #ffffff !important;
    }
    .hero-shell,
    .section-card,
    .metric-card,
    .player-summary-card {
        box-shadow: none !important;
    }
    .metric-card,
    .player-summary-card,
    .stPlotlyChart,
    .pdf-table {
        break-inside: avoid;
        page-break-inside: avoid;
    }
    .metric-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .stTabs [data-baseweb="tab-list"] {
        display: none;
    }
    .stApp::after {
        right: 0.65rem;
        bottom: 0.45rem;
        background: rgba(255, 255, 255, 0.55);
        color: rgba(17, 24, 39, 0.45);
        border-color: rgba(148, 163, 184, 0.25);
        box-shadow: none;
    }
}
</style>
"""


EXPORT_CSS = """
<style>
[data-testid="stSidebar"] {
    display: none !important;
}
.block-container {
    max-width: 1500px;
}
</style>
"""


def inject_theme(export_mode: bool = False) -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    if export_mode:
        st.markdown(EXPORT_CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        textwrap.dedent(
            """
        <div class="hero-shell">
            <div class="hero-kicker">StatsBomb Open Data</div>
            <h1 class="hero-title">Copa do Mundo</h1>
            <div class="hero-subtitle" style="margin-top:0.4rem;font-size:0.88rem;color:#94a3b8;">
                Projeto por Lucas Regis | lucaaregis4r@gmail.com
            </div>
            <div class="hero-subtitle">
                Território, sequências, ameaça ofensiva e comparações de desempenho.
            </div>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def start_section(title: str, note: str) -> None:
    note_html = f'<div class="section-note">{note}</div>' if note else ""
    st.markdown(
        textwrap.dedent(
            f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            {note_html}
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = "") -> None:
    subtitle_html = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        textwrap.dedent(
            f"""
        <div class="report-section">
            <h2>{html.escape(title)}</h2>
            {subtitle_html}
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, subtitle: str = "", leader: bool = False) -> None:
    with st.container(border=True):
        st.metric(str(label), str(value))
        if subtitle:
            st.caption(str(subtitle))


def render_metric_grid(cards: list[dict]) -> None:
    if not cards:
        return
    columns = st.columns(min(3, len(cards)))
    for idx, card in enumerate(cards):
        with columns[idx % len(columns)]:
            with st.container(border=True):
                st.metric(str(card.get("label", "")), str(card.get("value", "")))
                subtitle = card.get("subtitle", "")
                if subtitle:
                    st.caption(str(subtitle))


def render_player_summary_card(player_name: str, stats: dict[str, str], color: str) -> None:
    with st.container(border=True):
        st.markdown(f"### {player_name}")
        items = list(stats.items())
        if not items:
            return
        columns = st.columns(2)
        for idx, (label, value) in enumerate(items):
            with columns[idx % 2]:
                st.metric(str(label), str(value))


def render_pdf_table(frame: pd.DataFrame, columns: list[str] | None = None) -> None:
    if frame.empty:
        st.info("Sem dados para tabela.")
        return
    display = frame[columns].copy() if columns else frame.copy()
    for column in display.columns:
        if pd.api.types.is_numeric_dtype(display[column]):
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{float(value):.2f}")
    st.markdown(display.to_html(index=False, classes="pdf-table", border=0, escape=True), unsafe_allow_html=True)
