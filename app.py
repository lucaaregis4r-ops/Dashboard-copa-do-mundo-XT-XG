import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from src.bayes import add_dirichlet_posterior, confidence_label
from src.comparisons import build_entity_summary, format_comparison_table
from src.context import context_title, ordered_tabs_for_preset
from src.filters import render_analysis_context_filters, render_context_shell
from src.labels import action_label, team_label, translate_actions, translate_metrics, translate_teams

try:
    from src.labels import KEY_ACTION_ORDER, action_color, action_group, action_group_color, action_icon_label
except ImportError:
    KEY_ACTION_ORDER = ["Shot", "Pass", "Carry", "Dribble", "Ball Receipt*", "Ball Recovery", "Pressure"]

    def action_color(value):
        colors = {
            "Shot": "#f97316",
            "Pass": "#2563eb",
            "Carry": "#059669",
            "Dribble": "#7c3aed",
            "Ball Receipt*": "#eab308",
            "Ball Recovery": "#65a30d",
            "Pressure": "#374151",
        }
        return colors.get(str(value), "#9ca3af")

    def action_group(value):
        groups = {
            "Shot": "Finalização",
            "Pass": "Criação ofensiva",
            "Carry": "Progressão com bola",
            "Dribble": "Progressão com bola",
            "Ball Receipt*": "Criação ofensiva",
            "Ball Recovery": "Recuperação / defesa",
            "Pressure": "Recuperação / defesa",
        }
        return groups.get(str(value), "Outros")

    def action_group_color(value):
        colors = {
            "Criação ofensiva": "#2563eb",
            "Progressão com bola": "#059669",
            "Finalização": "#f97316",
            "Recuperação / defesa": "#0f766e",
            "Outros": "#9ca3af",
        }
        return colors.get(str(value), "#9ca3af")

    def action_icon_label(value):
        return action_label(value)
from src.load_data import check_data_availability, load_events, load_matches
from src.markov import (
    build_action_zone_model,
    build_first_order_model,
    build_second_order_model,
    build_team_transition_vectors,
    compute_similarity_matrix,
    evaluate_year_transfer,
    get_action_rankings,
    get_action_zone_rankings,
    get_second_order_rankings,
)
try:
    from src.narrative import (
        generate_linkedin_caption_suggestion,
        generate_player_comparison_narrative,
        generate_team_comparison_narrative,
        sample_alert,
    )
except ImportError:
    from src.narrative import sample_alert

    def generate_player_comparison_narrative(summary, player_a, player_b):
        return f"Comparacao: {player_a} x {player_b}."

    def generate_team_comparison_narrative(summary, team_a, team_b):
        return f"Comparacao: {team_label(team_a)} x {team_label(team_b)}."

    def generate_linkedin_caption_suggestion(title, visual_type="comparacao"):
        return f"Comparacao visual: {title}. Fonte: StatsBomb Open Data."
try:
    from src.possession_value import (
        ACTION_FAMILY_ORDER,
        add_possession_future_features,
        add_possession_value_deltas,
        action_family,
        build_state_values,
        format_sequence_metrics,
        summarize_sequence_value,
    )
except ImportError:
    from src.possession_value import (
        ACTION_FAMILY_ORDER,
        add_possession_future_features,
        action_family,
        format_sequence_metrics,
        summarize_sequence_value,
    )

    def build_state_values(events, state_col="value_state", min_cases_for_goal=30):
        return pd.DataFrame()

    def add_possession_value_deltas(events):
        frame = add_possession_future_features(events).copy()
        for column in [
            "delta_chance_finalizacao",
            "delta_xg_futuro",
            "delta_valor_posse",
            "delta_xt",
            "xt_origin",
            "xt_destination",
            "value_delta_available",
        ]:
            if column not in frame.columns:
                frame[column] = 0.0
        return frame
from src.preprocess import (
    FIELD_ZONES,
    MATCH_STATE_ORDER,
    TIME_BUCKET_ORDER,
    add_sequence_features,
    preprocess_events,
)
try:
    from src.theme import (
        inject_theme,
        render_hero,
        render_metric_grid,
        render_pdf_table,
        render_player_summary_card,
        render_section_header,
        start_section,
    )
except ImportError:
    from src.theme import inject_theme, render_hero, start_section

    def render_section_header(title: str, subtitle: str = "") -> None:
        st.markdown(f"## {title}")
        if subtitle:
            st.caption(subtitle)

    def render_metric_grid(cards: list[dict]) -> None:
        columns = st.columns(3)
        for idx, card in enumerate(cards):
            columns[idx % 3].metric(str(card.get("label", "")), str(card.get("value", "")), str(card.get("subtitle", "")) or None)

    def render_player_summary_card(player_name: str, stats: dict[str, str], color: str = "#2563eb") -> None:
        st.markdown(f"### {player_name}")
        for label, value in stats.items():
            st.metric(label, value)

    def render_pdf_table(frame: pd.DataFrame, columns: list[str] | None = None) -> None:
        display = frame[columns].copy() if columns else frame.copy()
        st.dataframe(display, use_container_width=True, hide_index=True)


# Definitive native Streamlit card renderers.
# These intentionally override theme imports to avoid stale HTML card renderers
# being kept alive by Streamlit/PyInstaller cache.
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


def render_player_summary_card(player_name: str, stats: dict[str, str], color: str = "#2563eb") -> None:
    with st.container(border=True):
        st.markdown(f"### {player_name}")
        items = list(stats.items())
        if not items:
            return
        columns = st.columns(2)
        for idx, (label, value) in enumerate(items):
            with columns[idx % 2]:
                st.metric(str(label), str(value))
from src.threat import add_threat_features, build_player_threat_summary, build_team_threat_summary, build_zone_threat_summary
from src.visualizations import (
    create_action_bar_chart,
    create_comparison_bar_chart,
    create_metric_strip,
    create_pitch_scatter,
    create_similarity_heatmap,
    create_thirds_probability_pitch,
    create_transition_heatmap,
    create_zone_heatmap,
    style_metric_delta,
)

try:
    from src.visualizations import create_zone_metric_heatmap
except ImportError:
    def create_zone_metric_heatmap(
        zone_values: pd.DataFrame,
        value_col: str,
        title: str,
        colorbar_title: str = "Valor",
        value_format: str = "decimal2",
    ):
        fallback = zone_values.rename(columns={value_col: "event_count"})
        return create_zone_heatmap(fallback, title=title)


def create_pitch_scatter_safe(
    events: pd.DataFrame,
    color_by_action: bool = True,
    title: str = "Mapa de eventos no campo",
    max_points: int = 6000,
    marker_size: int = 7,
    marker_opacity: float = 0.88,
    pitch_color: str = "#127a4f",
    export_mode: bool = False,
    show_plotly_legend: bool = False,
) -> go.Figure:
    frame = events.dropna(subset=["x", "y"]).copy()
    if len(frame) > max_points:
        frame = frame.sample(max_points, random_state=7)

    fig = go.Figure()
    line_color = "#f7f3e9"
    line_traces = [
        ([0, 120, 120, 0, 0], [0, 0, 80, 80, 0]),
        ([60, 60], [0, 80]),
        ([0, 18, 18, 0, 0], [18, 18, 62, 62, 18]),
        ([102, 120, 120, 102, 102], [18, 18, 62, 62, 18]),
        ([0, 6, 6, 0, 0], [30, 30, 50, 50, 30]),
        ([114, 120, 120, 114, 114], [30, 30, 50, 50, 30]),
    ]
    for xs, ys in line_traces:
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line=dict(color=line_color, width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    theta = np.linspace(0, 2 * np.pi, 80)
    fig.add_trace(
        go.Scatter(
            x=60 + 10 * np.cos(theta),
            y=40 + 10 * np.sin(theta),
            mode="lines",
            line=dict(color=line_color, width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    if frame.empty:
        fig.add_annotation(text="Sem eventos com coordenadas para os filtros atuais.", x=60, y=40, showarrow=False)
    elif color_by_action:
        for action, group in frame.groupby("action_type"):
            fig.add_trace(
                go.Scatter(
                    x=group["x"],
                    y=group["y"],
                    mode="markers",
                    name=action_label(action),
                    marker=dict(
                        size=marker_size,
                        color=action_color(action),
                        opacity=marker_opacity,
                        line=dict(color="#ffffff", width=0.9),
                    ),
                    showlegend=show_plotly_legend,
                    customdata=np.stack([group["team_name"].map(team_label), group["player_name"]], axis=1),
                    hoverinfo="skip" if export_mode else None,
                    hovertemplate=None if export_mode else "Ação: %{fullData.name}<br>Time: %{customdata[0]}<br>Jogador: %{customdata[1]}<br>x=%{x:.1f} y=%{y:.1f}<extra></extra>",
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=frame["x"],
                y=frame["y"],
                mode="markers",
                name="Eventos",
                marker=dict(size=marker_size, color="#ffdd57", opacity=marker_opacity, line=dict(color="#ffffff", width=0.9)),
                showlegend=show_plotly_legend,
                customdata=np.stack([frame["action_type"].map(action_label), frame["team_name"].map(team_label)], axis=1),
                hoverinfo="skip" if export_mode else None,
                hovertemplate=None if export_mode else "Ação: %{customdata[0]}<br>Time: %{customdata[1]}<br>x=%{x:.1f} y=%{y:.1f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#111827", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=pitch_color,
        margin=dict(l=10, r=10, t=44, b=18),
        height=540,
        xaxis=dict(range=[0, 120], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[80, 0], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        showlegend=show_plotly_legend,
        legend=dict(title="", bgcolor="rgba(255,255,255,0)", font=dict(color="#111827", size=11), orientation="h", y=-0.14, x=0),
        font=dict(color="#111827", size=13),
    )
    return fig


def render_pitch_map(
    events: pd.DataFrame,
    title: str,
    key: str,
    color_by_action: bool = False,
    marker_size: int = 7,
    marker_opacity: float = 0.82,
    pitch_color: str = "#127a4f",
    export_mode: bool = False,
    show_plotly_legend: bool = False,
) -> None:
    st.plotly_chart(
        create_pitch_scatter_safe(
            events,
            color_by_action=color_by_action,
            title=title,
            marker_size=marker_size,
            marker_opacity=marker_opacity,
            pitch_color=pitch_color,
            export_mode=export_mode,
            show_plotly_legend=show_plotly_legend,
        ),
        use_container_width=True,
        key=key,
    )


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DASHBOARD_DATA_DIR", BASE_DIR))

st.set_page_config(
    page_title="World Cup Performance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def get_matches() -> pd.DataFrame:
    return load_matches(DATA_DIR)


@st.cache_data(show_spinner=True)
def get_events(years: tuple[int, ...]) -> pd.DataFrame:
    raw_events = load_events(DATA_DIR, years=years)
    cleaned = preprocess_events(raw_events)
    return add_sequence_features(cleaned)


@st.cache_data(show_spinner=False)
def enrich_events(events: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    match_cols = ["match_id", "home_team", "away_team", "home_score", "away_score"]
    frame = events.merge(matches[match_cols], on="match_id", how="left")
    frame = frame.sort_values(["year", "match_id", "period", "index"]).copy()

    frame["team_side"] = np.select(
        [frame["team_name"].eq(frame["home_team"]), frame["team_name"].eq(frame["away_team"])],
        ["home", "away"],
        default="unknown",
    )
    frame["opponent_team_name"] = np.select(
        [frame["team_side"].eq("home"), frame["team_side"].eq("away")],
        [frame["away_team"], frame["home_team"]],
        default="Unknown",
    )
    frame["is_goal_event"] = (
        frame["shot_outcome"].eq("Goal") | frame["action_type"].eq("Own Goal For")
    ).astype(int)
    frame["home_goal_event"] = (frame["team_side"].eq("home") & frame["is_goal_event"].eq(1)).astype(int)
    frame["away_goal_event"] = (frame["team_side"].eq("away") & frame["is_goal_event"].eq(1)).astype(int)
    frame["home_score_live"] = frame.groupby("match_id")["home_goal_event"].cumsum()
    frame["away_score_live"] = frame.groupby("match_id")["away_goal_event"].cumsum()

    frame["team_score_live"] = np.select(
        [frame["team_side"].eq("home"), frame["team_side"].eq("away")],
        [frame["home_score_live"], frame["away_score_live"]],
        default=np.nan,
    )
    frame["opponent_score_live"] = np.select(
        [frame["team_side"].eq("home"), frame["team_side"].eq("away")],
        [frame["away_score_live"], frame["home_score_live"]],
        default=np.nan,
    )
    frame["score_diff"] = frame["team_score_live"] - frame["opponent_score_live"]
    frame["match_state"] = np.select(
        [frame["score_diff"].gt(0), frame["score_diff"].lt(0), frame["score_diff"].eq(0)],
        ["Ganhando", "Perdendo", "Empatando"],
        default="Desconhecido",
    )
    frame["match_state"] = pd.Categorical(frame["match_state"], categories=MATCH_STATE_ORDER, ordered=True)
    frame["time_remaining_bucket"] = pd.Categorical(
        frame["time_remaining_bucket"],
        categories=TIME_BUCKET_ORDER + ["Desconhecido"],
        ordered=True,
    )
    frame["live_score_label"] = (
        frame["team_score_live"].fillna(0).astype(int).astype(str)
        + "-"
        + frame["opponent_score_live"].fillna(0).astype(int).astype(str)
    )
    return frame


def _safe_percent(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def _format_decision_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    result = translate_actions(frame)
    result = result.rename(
        columns={
            "next_action": "proxima_acao",
            "count": "casos",
            "probability": "probabilidade",
            "raw_probability": "probabilidade_bruta",
            "posterior_probability": "probabilidade_suavizada",
            "difference": "ajuste_bayesiano",
            "observed_cases": "casos_observados",
            "chance_finalizacao_futura": "chance_finalizacao_futura",
            "xg_futuro_medio": "xg_futuro_medio",
            "xg_futuro_total_medio": "xg_futuro_total_medio",
            "delta_xt_medio": "delta_xt_medio",
            "delta_valor_posse_medio": "mudanca_valor_posse_media",
            "valor_caminho": "valor_caminho",
            "xg_delta_medio": "variacao_xg_evento_seguinte",
            "xg_proxima_acao": "xg_medio_evento_seguinte",
            "confidence": "confianca",
        }
    )
    return result


def _top_transition_matrix(matrix: pd.DataFrame, limit: int = 25) -> pd.DataFrame:
    if matrix.empty or len(matrix.index) <= limit:
        return matrix.rename(index=action_label, columns=action_label)

    row_strength = matrix.sum(axis=1).sort_values(ascending=False).head(limit).index
    col_strength = matrix.sum(axis=0).sort_values(ascending=False).head(limit).index
    reduced = matrix.loc[row_strength, col_strength]
    return reduced.rename(index=action_label, columns=action_label)


def _format_comparison_display(frame: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    result = frame.copy()
    if entity_col == "team_name":
        result = translate_teams(result, ["team_name"])
        result = result.rename(columns={"team_name": "Seleção"})
    elif entity_col == "player_name":
        result = result.rename(columns={"player_name": "Jogador"})
    rename_map = {
        "total_actions": "Total de ações",
        "passes": "passes",
        "shots": "Finalizações",
        "goals": "Gols",
        "assists": "Assistências",
        "carries": "Conduções",
        "pressures": "Pressões",
        "recoveries": "Recuperações",
        "xg": "xG",
        "under_pressure_rate": "Sob pressão",
        "attacking_zone_rate": "Taxa zona ataque",
        "avg_actions_per_match": "Ações por jogo",
        "delta_xt_total": "Delta xT total",
        "delta_xt_mean": "Delta xT médio",
        "delta_valor_posse_mean": "Mudança média valor posse",
        "future_xg_associated": "xG futuro associado",
        "future_shot_rate": "Chance chute futuro",
        "final_third_entries": "Entradas no terço final",
        "box_entries": "Entradas na área",
        "progressive_events": "Ações progressivas",
        "threat_added": "Ameaça adicionada",
    }
    return result.rename(columns=rename_map)


def _build_performance_profiles(events: pd.DataFrame, entity_col: str, selected: list[str]) -> pd.DataFrame:
    frame = events[events[entity_col].isin(selected)].copy()
    if "threat_added" not in frame.columns or "is_progressive_event" not in frame.columns:
        frame = add_threat_features(frame)
    if "delta_xt" not in frame.columns or "future_xg" not in frame.columns:
        frame = add_possession_value_deltas(frame)
    if "pass_goal_assist" not in frame.columns:
        frame["pass_goal_assist"] = False
    if "is_goal_event" not in frame.columns:
        frame["is_goal_event"] = frame["shot_outcome"].eq("Goal") if "shot_outcome" in frame.columns else False
    for column, default in {
        "delta_xt": 0.0,
        "delta_valor_posse": 0.0,
        "future_xg": 0.0,
        "future_shot": False,
        "final_third_entry": False,
        "box_entry": False,
    }.items():
        if column not in frame.columns:
            frame[column] = default
    if entity_col == "player_name":
        frame = frame[frame["player_name"].ne("Unknown")]
    if frame.empty:
        return pd.DataFrame()

    grouped = frame.groupby(entity_col, dropna=False)
    profiles = grouped.agg(
        events=("event_id", "count"),
        threat_added=("threat_added", "sum"),
        progressive_events=("is_progressive_event", "sum"),
        goals=("is_goal_event", "sum"),
        assists=("pass_goal_assist", "sum"),
        shots=("is_shot", "sum"),
        xg=("shot_xg", "sum"),
        under_pressure_rate=("under_pressure", "mean"),
        attacking_zone_rate=("zone", lambda series: series.astype(str).str.startswith("ataque").mean()),
        delta_xt_total=("delta_xt", "sum"),
        delta_xt_mean=("delta_xt", "mean"),
        delta_valor_posse_mean=("delta_valor_posse", "mean"),
        future_xg_associated=("future_xg", "sum"),
        future_shot_rate=("future_shot", "mean"),
        final_third_entries=("final_third_entry", "sum"),
        box_entries=("box_entry", "sum"),
    ).reset_index()
    profiles["xg_per_shot"] = profiles["xg"] / profiles["shots"].replace(0, np.nan)
    return profiles


def _profile_long(profiles: pd.DataFrame, entity_col: str, metrics: list[str]) -> pd.DataFrame:
    if profiles.empty:
        return pd.DataFrame()
    profiles = profiles.copy()
    for metric in metrics:
        if metric not in profiles.columns:
            profiles[metric] = 0.0
    return profiles[[entity_col] + metrics].melt(id_vars=[entity_col], value_vars=metrics, var_name="metric", value_name="value")


def _metric_value(profiles: pd.DataFrame, entity_col: str, entity: str, metric: str) -> float:
    if metric not in profiles.columns:
        return 0.0
    value = profiles.loc[profiles[entity_col] == entity, metric]
    if value.empty or pd.isna(value.iloc[0]):
        return 0.0
    return float(value.iloc[0])


def _is_export_mode() -> bool:
    env_value = str(os.environ.get("DASHBOARD_EXPORT_MODE", "")).lower()
    if env_value in {"1", "true", "yes", "pdf"}:
        return True
    try:
        query_value = st.query_params.get("export", "")
    except Exception:
        query_value = ""
    return str(query_value).lower() in {"1", "true", "yes", "pdf"}


def render_pdf_generator() -> None:
    st.markdown("### Exportar PDF")
    st.caption("Use o botao abaixo e escolha 'Salvar como PDF' na janela de impressao do navegador.")
    components.html(
        """
        <button
            onclick="window.parent.print()"
            style="
                width: 100%;
                border: 1px solid #cbd5e1;
                background: #111827;
                color: #ffffff;
                padding: 0.72rem 0.9rem;
                border-radius: 8px;
                font-weight: 800;
                cursor: pointer;
                font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            "
        >
            Gerar PDF
        </button>
        """,
        height=58,
    )


def _inject_theme_compat(export_mode: bool = False) -> None:
    try:
        inject_theme(export_mode=export_mode)
    except TypeError:
        inject_theme()
    _inject_select_contrast_guard()


def _inject_select_contrast_guard() -> None:
    st.markdown(
        """
        <style>
        /* Hard override for Streamlit/BaseWeb select values.
           This is intentionally injected from app.py so it still works if an old theme.py is cached. */
        [data-testid="stSidebar"] [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] *,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] input,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] input,
        [data-testid="stSidebar"] div[role="combobox"],
        [data-testid="stSidebar"] div[role="combobox"] *,
        [data-testid="stSidebar"] input[aria-autocomplete="list"],
        [data-testid="stSidebar"] input[role="combobox"] {
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
            caret-color: #111827 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[role="combobox"] {
            background: #ffffff !important;
            border-color: #d1d5db !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] svg,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] svg,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] svg {
            color: #111827 !important;
            fill: #111827 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="tag"],
        [data-testid="stSidebar"] [data-baseweb="tag"] *,
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"],
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] * {
            background: #dbeafe !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }

        [data-baseweb="popover"],
        [data-baseweb="popover"] *,
        [role="listbox"],
        [role="listbox"] *,
        [role="option"],
        [role="option"] * {
            background-color: #ffffff !important;
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_number(value: float, kind: str = "decimal2") -> str:
    if pd.isna(value):
        return "-"
    if kind == "int":
        return f"{int(round(float(value))):,}".replace(",", ".")
    if kind == "percent":
        return f"{float(value):.1%}"
    if kind == "signed3":
        return f"{float(value):+.3f}"
    if kind == "signed4":
        return f"{float(value):+.4f}"
    return f"{float(value):.2f}"


def _entity_display(entity: str, entity_col: str) -> str:
    return team_label(entity) if entity_col == "team_name" else str(entity)


def _metric_leader(profiles: pd.DataFrame, entity_col: str, entities: list[str], metric: str) -> str | None:
    values = {entity: _metric_value(profiles, entity_col, entity, metric) for entity in entities}
    if not values:
        return None
    return max(values, key=values.get)


def _top_values(frame: pd.DataFrame, col: str, limit: int) -> list[str]:
    if frame.empty or col not in frame.columns:
        return []
    return frame[col].dropna().value_counts().head(limit).index.tolist()


def _render_profile_chart(
    profiles: pd.DataFrame,
    entity_col: str,
    metrics: list[str],
    title: str,
    translate_entity: bool = False,
    key_prefix: str = "profile",
) -> None:
    chart_data = _profile_long(profiles, entity_col, metrics)
    if chart_data.empty:
        return
    if translate_entity:
        chart_data = translate_teams(chart_data, [entity_col])
    chart_data = translate_metrics(chart_data)
    st.plotly_chart(
        render_comparison_bar_chart(chart_data, entity_col, "value", "metric", title),
        use_container_width=True,
        key=f"{key_prefix}_{title}_{entity_col}",
    )


def render_comparison_bar_chart(frame: pd.DataFrame, color_col: str, value_col: str, label_col: str, title: str) -> go.Figure:
    if frame.empty:
        return go.Figure()
    data = frame.copy().sort_values(value_col, ascending=True)
    fig = px.bar(
        data,
        x=value_col,
        y=label_col,
        color=color_col,
        orientation="h",
        barmode="group",
        title=title,
        color_discrete_sequence=["#2563eb", "#f97316", "#047857"],
        text=value_col,
    )
    text_template, tick_format = _horizontal_value_formats(data[value_col])
    fig.update_traces(texttemplate=text_template, textposition="outside", cliponaxis=False)
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#111827", size=14),
        title=dict(font=dict(size=20, color="#111827")),
        margin=dict(l=170, r=85, t=68, b=48),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            font=dict(color="#111827", size=13),
            title="",
        ),
        xaxis=dict(title="", gridcolor="#e5e7eb", zerolinecolor="#9ca3af", zerolinewidth=2, automargin=True, tickformat=tick_format),
        yaxis=dict(title="", automargin=True),
        height=520,
    )
    _pad_horizontal_axis(fig, data[value_col])
    return fig


def _ordered_action_categories(actions: pd.Series) -> list[str]:
    available = actions.dropna().astype(str).unique().tolist()
    key_labels = [action_label(action) for action in KEY_ACTION_ORDER]
    ordered = [label for label in key_labels if label in available]
    remaining = sorted([action for action in available if action not in ordered])
    return ordered + remaining


def _horizontal_value_formats(values: pd.Series) -> tuple[str, str]:
    numeric = pd.to_numeric(values, errors="coerce").abs().dropna()
    if numeric.empty:
        return "%{x:.2f}", ".2f"
    max_abs = float(numeric.max())
    if max_abs and max_abs < 0.01:
        return "%{x:.4f}", ".4f"
    if max_abs < 0.1:
        return "%{x:.3f}", ".3f"
    if max_abs < 1:
        return "%{x:.2f}", ".2f"
    if max_abs < 10:
        return "%{x:.1f}", ".1f"
    return "%{x:,.0f}", ",.0f"


def _legend_actions_for_frame(frame: pd.DataFrame, limit: int = 10) -> list[str]:
    if frame.empty or "action_type" not in frame.columns:
        return []
    available = frame["action_type"].dropna().astype(str).unique().tolist()
    ordered = [action for action in KEY_ACTION_ORDER if action in available]
    remaining = sorted([action for action in available if action not in ordered])
    return (ordered + remaining)[:limit]


def _pad_horizontal_axis(fig: go.Figure, values: pd.Series, pad: float = 1.18) -> go.Figure:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return fig
    max_value = float(numeric.max())
    min_value = float(numeric.min())
    if max_value <= 0 and min_value >= 0:
        return fig
    max_abs = max(abs(max_value), abs(min_value))
    min_visible = 0.01 if max_abs <= 0.01 else 0.0
    lower = min(0.0, min_value * pad)
    upper = max(max_value * pad if max_value > 0 else 0.0, min_visible)
    if upper > lower:
        fig.update_xaxes(range=[lower, upper])
    return fig


def render_action_family_chart(frame: pd.DataFrame, entity_col: str, title: str) -> go.Figure:
    if frame.empty:
        return go.Figure()
    data = frame.copy()
    data["action_group"] = data["action_type"].map(action_group)
    summary = data.groupby([entity_col, "action_group"], dropna=False)["count"].sum().reset_index()
    group_order = (
        summary.groupby("action_group")["count"]
        .sum()
        .sort_values(ascending=True)
        .index.tolist()
    )
    color_map = {group: action_group_color(group) for group in summary["action_group"].unique()}
    fig = px.bar(
        summary,
        x="count",
        y="action_group",
        color="action_group",
        facet_col=entity_col,
        orientation="h",
        text="count",
        title=title,
        category_orders={"action_group": group_order},
        color_discrete_map=color_map,
    )
    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="Grupo: %{y}<br>Eventos: %{x}<extra></extra>")
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#111827", size=14),
        title=dict(font=dict(size=20, color="#111827")),
        margin=dict(l=180, r=90, t=74, b=48),
        showlegend=False,
        xaxis=dict(title="Eventos", gridcolor="#e5e7eb", zerolinecolor="#d1d5db"),
        yaxis=dict(title="", automargin=True),
        height=460,
    )
    _pad_horizontal_axis(fig, summary["count"])
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    return fig


def render_action_mix_chart(frame: pd.DataFrame, entity_col: str, title: str) -> go.Figure:
    if frame.empty:
        return go.Figure()
    data = frame.copy()
    data["action_display"] = data["action_type"].map(action_icon_label)
    data["action_group"] = data["action_type"].map(action_group)
    data["percent"] = data["count"] / data.groupby(entity_col)["count"].transform("sum").replace(0, np.nan)
    action_order = _ordered_action_categories(data["action_type"].map(action_label))
    display_order = [action_icon_label(label) for label in action_order]
    totals = data.groupby("action_display")["count"].sum().sort_values(ascending=False)
    remaining_display = [name for name in totals.index.tolist() if name not in display_order]
    display_order = [name for name in display_order if name in totals.index] + remaining_display
    color_map = {action_icon_label(action): action_color(action) for action in data["action_type"].unique()}
    fig = px.bar(
        data,
        x="count",
        y="action_display",
        color="action_display",
        facet_col=entity_col,
        orientation="h",
        title=title,
        text="count",
        category_orders={"action_display": list(reversed(display_order))},
        color_discrete_map=color_map,
        custom_data=["action_group", "percent"],
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="Ação: %{y}<br>Grupo: %{customdata[0]}<br>Eventos: %{x}<br>% do jogador/equipe: %{customdata[1]:.1%}<extra></extra>",
    )
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#111827", size=14),
        title=dict(font=dict(size=20, color="#111827")),
        margin=dict(l=190, r=95, t=68, b=48),
        showlegend=False,
        xaxis=dict(title="Eventos", gridcolor="#e5e7eb", zerolinecolor="#d1d5db"),
        yaxis=dict(title="", automargin=True),
        bargap=0.22,
        height=max(500, min(780, 34 * data["action_display"].nunique() + 230)),
    )
    _pad_horizontal_axis(fig, data["count"])
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    return fig


def _visual_metric_row(profiles: pd.DataFrame, entity_col: str, entities: list[str]) -> None:
    metrics = [
        ("xG", "xg", "decimal2"),
        ("Finalizações", "shots", "int"),
        ("Assistências", "assists", "int"),
        ("xG futuro associado", "future_xg_associated", "decimal2"),
        ("Delta xT total", "delta_xt_total", "signed3"),
        ("Ameaça média", "delta_xt_mean", "signed4"),
        ("Entradas na área", "box_entries", "int"),
        ("Ações de alto valor", "high_value_actions", "int"),
    ]
    cards = []
    for label, metric, fmt in metrics:
        values = []
        for entity in entities:
            value = _metric_value(profiles, entity_col, entity, metric)
            values.append(f"{_entity_display(entity, entity_col)} {_format_number(value, fmt)}")
        leader = _metric_leader(profiles, entity_col, entities, metric)
        cards.append(
            {
                "label": label,
                "value": " | ".join(values),
                "subtitle": f"Lidera: {_entity_display(leader, entity_col)}" if leader else "",
                "leader": True,
            }
        )
    render_metric_grid(cards)


def _prepare_visual_profiles(events: pd.DataFrame, entity_col: str, entities: list[str]) -> pd.DataFrame:
    profiles = _build_performance_profiles(events, entity_col, entities)
    if profiles.empty:
        return profiles
    frame = add_possession_value_deltas(events[events[entity_col].isin(entities)])
    high_value = (
        frame.assign(delta_xt_numeric=pd.to_numeric(frame.get("delta_xt", 0.0), errors="coerce").fillna(0.0))
        .groupby(entity_col)["delta_xt_numeric"]
        .apply(lambda series: int((series >= 0.025).sum()))
        .rename("high_value_actions")
        .reset_index()
    )
    profiles = profiles.drop(columns=["high_value_actions"], errors="ignore").merge(high_value, on=entity_col, how="left")
    profiles["high_value_actions"] = profiles["high_value_actions"].fillna(0).astype(int)
    return profiles


def _render_threat_distribution(events: pd.DataFrame, entity_col: str, entities: list[str], title: str) -> None:
    frame = add_possession_value_deltas(events[events[entity_col].isin(entities)]).copy()
    if frame.empty:
        return
    if "action_family" not in frame.columns:
        frame["action_family"] = frame.apply(lambda row: action_family(row.get("action_type"), row.get("play_pattern")), axis=1)
    frame["delta_xt_positive"] = pd.to_numeric(frame.get("delta_xt", 0.0), errors="coerce").fillna(0.0).clip(lower=0.0)
    summary = (
        frame.groupby([entity_col, "action_family"], dropna=False)["delta_xt_positive"]
        .sum()
        .reset_index(name="ameaca")
    )
    if entity_col == "team_name":
        summary = translate_teams(summary, [entity_col])
    fig = px.bar(
        summary.sort_values("ameaca", ascending=True),
        x="ameaca",
        y="action_family",
        color=entity_col,
        orientation="h",
        barmode="group",
        title=title,
        color_discrete_sequence=["#2563eb", "#f97316", "#047857"],
    )
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#111827", size=14),
        title=dict(font=dict(size=20, color="#111827")),
        margin=dict(l=150, r=30, t=62, b=42),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom", title=""),
        xaxis=dict(title="Ameaça", gridcolor="#e5e7eb"),
        yaxis=dict(title="", automargin=True),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"threat_distribution_{entity_col}_{'_'.join(map(str, entities))}")


PLAYER_COLORS = ["#2563eb", "#f97316"]


def _player_summary_stats(profiles: pd.DataFrame, player: str) -> dict[str, str]:
    return {
        "Total de ações": _format_number(_metric_value(profiles, "player_name", player, "events"), "int"),
        "xG": _format_number(_metric_value(profiles, "player_name", player, "xg")),
        "Delta xT total": _format_number(_metric_value(profiles, "player_name", player, "delta_xt_total"), "signed3"),
        "xG futuro associado": _format_number(_metric_value(profiles, "player_name", player, "future_xg_associated")),
        "Gols + assistências": (
            f"{_format_number(_metric_value(profiles, 'player_name', player, 'goals'), 'int')} + "
            f"{_format_number(_metric_value(profiles, 'player_name', player, 'assists'), 'int')}"
        ),
        "Entradas na área": _format_number(_metric_value(profiles, "player_name", player, "box_entries"), "int"),
        "Entradas no terço final": _format_number(_metric_value(profiles, "player_name", player, "final_third_entries"), "int"),
    }


def _map_summary(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "Sem eventos com os filtros atuais."
    zones = ", ".join(frame["zone"].dropna().astype(str).value_counts().head(2).index.tolist()) or "-"
    actions = ", ".join(frame["action_type"].dropna().map(action_label).value_counts().head(3).index.tolist()) or "-"
    return f"Eventos: {len(frame):,} | Zonas frequentes: {zones} | Ações comuns: {actions}".replace(",", ".")


def _action_mix_reading(action_mix: pd.DataFrame, entity_col: str) -> str:
    if action_mix.empty:
        return ""
    parts = []
    for entity, group in action_mix.groupby(entity_col, dropna=False):
        top_actions = group.sort_values("count", ascending=False).head(3)["action_type"].map(action_label).tolist()
        if top_actions:
            parts.append(f"{entity}: {', '.join(top_actions)}")
    return " | ".join(parts)


def render_action_legend(actions: list[str] | None = None, title: str = "Legenda", key: str | None = None) -> None:
    selected = actions or ["Shot", "Pass", "Carry", "Dribble", "Ball Receipt*", "Pressure", "Ball Recovery"]
    if not selected:
        return
    fig = go.Figure()
    for action in selected:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=action_icon_label(action),
                marker=dict(size=11, color=action_color(action), line=dict(color="#ffffff", width=1)),
                showlegend=True,
                hoverinfo="skip",
            )
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#4b5563")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=86,
        margin=dict(l=0, r=0, t=26, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0)",
            font=dict(color="#111827", size=12),
            tracegroupgap=4,
        ),
        showlegend=True,
    )
    if key is None:
        st.session_state["_action_legend_render_counter"] = st.session_state.get("_action_legend_render_counter", 0) + 1
        key = f"action_legend_{st.session_state['_action_legend_render_counter']}"
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "staticPlot": True},
        key=key,
    )


def render_visual_comparison_page(events: pd.DataFrame, context: dict) -> None:
    render_section_header("Relatório visual", "Comparação pronta para apresentação e exportação em PDF.")
    if events.empty:
        st.info("Nao ha eventos para montar a comparacao visual.")
        return

    export_mode = _is_export_mode()
    formato = "16:9" if export_mode else st.radio("Formato", ["16:9", "1:1", "4:5"], horizontal=True, key="visual_format")
    if not export_mode:
        st.markdown(f"**Layout:** {formato}")

    visual_type = context.get("visual_type", "Selecoes")
    if visual_type == "Jogadores":
        entities = context.get("players", [])[:2]
        entity_col = "player_name"
        if len(entities) < 2:
            st.info("Escolha dois jogadores nos filtros rapidos.")
            return
        title = f"{entities[0]} x {entities[1]}"
        profiles = _prepare_visual_profiles(events, entity_col, entities)
        translate_entity = False
        narrative = generate_player_comparison_narrative(profiles, entities[0], entities[1])
    else:
        entities = [context.get("team_a"), context.get("team_b")]
        entity_col = "team_name"
        if not all(entities):
            st.info("Escolha duas selecoes.")
            return
        title = f"{team_label(entities[0])} x {team_label(entities[1])}"
        profiles = _prepare_visual_profiles(events, entity_col, entities)
        translate_entity = True
        narrative = generate_team_comparison_narrative(profiles, entities[0], entities[1])

    if profiles.empty:
        st.info("Nao ha dados suficientes para essa comparacao.")
        return

    st.markdown(f"## {title}")
    if not export_mode:
        st.info(narrative)
    if visual_type == "Jogadores":
        player_cols = st.columns(2)
        for idx, player in enumerate(entities):
            with player_cols[idx]:
                render_player_summary_card(player, _player_summary_stats(profiles, player), PLAYER_COLORS[idx])
    else:
        _visual_metric_row(profiles, entity_col, entities)

    production_metrics = ["xg", "shots", "assists", "xg_per_shot"]
    value_metrics = ["delta_xt_total", "future_xg_associated", "delta_xt_mean", "box_entries", "high_value_actions"]
    left, right = st.columns(2)
    with left:
        _render_profile_chart(profiles, entity_col, production_metrics, "Produção final", translate_entity=translate_entity, key_prefix="visual_production")
    with right:
        _render_profile_chart(profiles, entity_col, value_metrics, "Valor da posse", translate_entity=translate_entity, key_prefix="visual_value")

    _render_threat_distribution(events, entity_col, entities, "Ameaça por tipo de ação")

    comparison_scope_events = events[events[entity_col].isin(entities)]
    action_mix = (
        comparison_scope_events
        .groupby([entity_col, "action_type"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if entity_col == "team_name":
        action_mix = translate_teams(action_mix, [entity_col])
    action_mix_display = translate_actions(action_mix)
    reading = _action_mix_reading(action_mix_display, entity_col)
    render_section_header("Perfil de ações", "Famílias primeiro, detalhe depois.")
    if reading:
        st.caption(reading)
    render_action_legend(_legend_actions_for_frame(comparison_scope_events), title="Cores das acoes")
    st.plotly_chart(
        render_action_family_chart(action_mix_display, entity_col, "Famílias de ações"),
        use_container_width=True,
        key=f"visual_action_family_{entity_col}",
    )
    st.plotly_chart(
        render_action_mix_chart(action_mix_display, entity_col, "Mix de ações"),
        use_container_width=True,
        key=f"visual_action_mix_{entity_col}",
    )

    st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
    render_section_header("Mapas de ações", "Eventos localizados no campo para cada lado da comparação.")
    render_action_legend(_legend_actions_for_frame(comparison_scope_events), title="Legenda do campo")
    map_cols = st.columns(2)
    for idx, entity in enumerate(entities):
        entity_events = events[events[entity_col] == entity]
        with map_cols[idx]:
            render_pitch_map(
                entity_events,
                title=f"Mapa de ações - {_entity_display(entity, entity_col)}",
                key=f"visual_map_{idx}",
                color_by_action=True,
                export_mode=export_mode,
            )
            st.caption(_map_summary(entity_events))

    summary_columns = [
        entity_col,
        "events",
        "xg",
        "delta_xt_total",
        "future_xg_associated",
        "goals",
        "assists",
        "box_entries",
        "final_third_entries",
    ]
    summary_table = profiles[summary_columns].copy()
    summary_table = summary_table.rename(
        columns={
            entity_col: "Jogador" if entity_col == "player_name" else "Seleção",
            "events": "Total de ações",
            "xg": "xG",
            "delta_xt_total": "Delta xT total",
            "future_xg_associated": "xG futuro associado",
            "goals": "Gols",
            "assists": "Assistências",
            "box_entries": "Entradas na área",
            "final_third_entries": "Entradas no terço final",
        }
    )
    if entity_col == "team_name":
        summary_table["Seleção"] = summary_table["Seleção"].map(team_label)
    render_section_header("Tabela resumida", "Versão compacta para PDF.")
    render_pdf_table(summary_table)

    caption = generate_linkedin_caption_suggestion(title, visual_type)
    if not export_mode:
        st.text_area("Legenda sugerida", caption, height=90, disabled=True)
    st.markdown("Fonte: StatsBomb Open Data | Projeto por Lucas Regis | lucaaregis4r@gmail.com")


def _available_preferred_actions(actions: list[str], preferred: list[str], fallback_limit: int = 3) -> list[str]:
    selected = [action for action in preferred if action in actions]
    if selected:
        return selected
    return actions[:fallback_limit]


def render_overview(events: pd.DataFrame, matches: pd.DataFrame) -> None:
    start_section("Visao Geral dos Dados", "")

    match_counts = matches.groupby("year")["match_id"].nunique()
    strip = pd.DataFrame(
        [
            {"label": "Jogos 2018", "value": int(match_counts.get(2018, 0))},
            {"label": "Jogos 2022", "value": int(match_counts.get(2022, 0))},
            {"label": "Eventos", "value": len(events)},
            {"label": "Selecoes", "value": events["team_name"].nunique()},
            {"label": "Acoes", "value": events["action_type"].nunique()},
        ]
    )
    st.plotly_chart(create_metric_strip(strip), use_container_width=True)

    year_counts = events.groupby("year").size().reset_index(name="event_count")
    team_counts = translate_teams(events.groupby("team_name").size().reset_index(name="event_count")).sort_values("event_count", ascending=False)
    action_counts = translate_actions(events.groupby("action_type").size().reset_index(name="event_count")).sort_values("event_count", ascending=False)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(create_action_bar_chart(year_counts, "year", "event_count", "Eventos por Copa"), use_container_width=True)
        st.dataframe(year_counts, use_container_width=True, hide_index=True)
    with right:
        st.plotly_chart(create_action_bar_chart(team_counts.head(20), "team_name", "event_count", "Top times por volume"), use_container_width=True)

    st.plotly_chart(create_action_bar_chart(action_counts.head(20), "action_type", "event_count", "Top acoes da base"), use_container_width=True)
    st.dataframe(action_counts.rename(columns={"action_type": "tipo_de_acao", "event_count": "eventos"}), use_container_width=True, hide_index=True)
    render_stat_explorer(events)


def render_summary_page(events: pd.DataFrame, matches: pd.DataFrame) -> None:
    render_overview(events, matches)


def render_map_territory_page(events: pd.DataFrame) -> None:
    render_action_maps(events, key_prefix="territory")
    st.markdown("### Tercos do campo")
    render_field_thirds(events, key_prefix="territory")


def render_sequences_page(events: pd.DataFrame) -> None:
    start_section("Caminhos de Ameaca", "")
    sequence_events = add_possession_value_deltas(events)
    model = build_first_order_model(sequence_events)
    zone_model = build_action_zone_model(sequence_events)
    second_model = build_second_order_model(sequence_events)

    if model["transition_counts"].empty:
        st.info("Sem sequencias suficientes neste recorte.")
        return

    counts = model["transition_counts"].copy()
    total_transitions = int(counts["count"].sum())
    contexts = int(counts["current_action"].nunique())
    median_cases = int(counts.groupby("current_action")["observed_cases"].max().median())
    top_volume = counts.sort_values("count", ascending=False).iloc[0]

    delta_xt_series = pd.to_numeric(
        counts.get("delta_xt_medio", pd.Series(np.nan, index=counts.index)),
        errors="coerce",
    )
    value_counts = counts[delta_xt_series.notna()].copy()
    top_value = value_counts.sort_values("valor_caminho", ascending=False).iloc[0] if not value_counts.empty else top_volume

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transicoes observadas", f"{total_transitions:,}".replace(",", "."))
    col2.metric("Contextos de acao", contexts)
    col3.metric("Mediana por contexto", median_cases)
    col4.metric("Melhor caminho", f"{action_label(top_value['current_action'])} -> {action_label(top_value['next_action'])}", f"{float(top_value.get('valor_caminho', 0.0)):+.4f}")

    st.metric("Sequencia mais frequente", f"{action_label(top_volume['current_action'])} -> {action_label(top_volume['next_action'])}", f"{int(top_volume['count'])} casos")

    st.markdown("### Depois de uma acao, o que costuma vir?")
    available_actions = sorted(counts["current_action"].unique().tolist())
    default_action = counts.groupby("current_action")["count"].sum().sort_values(ascending=False).index[0]
    selected_action = st.selectbox(
        "Acao atual",
        options=available_actions,
        index=available_actions.index(default_action),
        key="seq_current_action",
        format_func=action_label,
    )
    rankings = get_action_rankings(model, selected_action)
    observed_cases = int(rankings["observed_cases"].iloc[0]) if not rankings.empty else 0
    alert = sample_alert(observed_cases, "acao")
    if alert:
        st.warning(alert)

    top_next = translate_actions(rankings.head(8), columns=["next_action"])
    left_chart, right_chart = st.columns(2)
    with left_chart:
        st.plotly_chart(
            create_action_bar_chart(top_next, "next_action", "probability", "Proximas acoes mais frequentes"),
            use_container_width=True,
        )
    value_rankings = translate_actions(rankings.sort_values("valor_caminho", ascending=False).head(8), columns=["next_action"])
    with right_chart:
        st.plotly_chart(
            create_action_bar_chart(value_rankings, "next_action", "valor_caminho", "Caminhos com maior valor ponderado"),
            use_container_width=True,
        )

    if not rankings.empty:
        best_value = rankings.sort_values("valor_caminho", ascending=False).iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Proximo passo de maior valor", action_label(best_value["next_action"]))
        c2.metric("Mudanca media de valor", f"{float(best_value.get('delta_xt_medio', 0.0)):+.4f}")
        c3.metric("Chance de finalizar depois", _safe_percent(best_value.get("chance_finalizacao_futura", np.nan)))

    with st.expander("Dados da sequencia"):
        st.dataframe(_format_decision_table(rankings), use_container_width=True, hide_index=True)

    with st.expander("Matriz de sequencias"):
        transition_matrix = _top_transition_matrix(model["transition_matrix"])
        st.plotly_chart(create_transition_heatmap(transition_matrix, "Proxima acao por acao atual"), use_container_width=True)
        st.dataframe(transition_matrix, use_container_width=True)

    st.markdown("### Essa sequencia muda conforme a zona?")
    if zone_model["transition_counts"].empty:
        st.info("Nao ha observacoes suficientes para cruzar acao e zona.")
    else:
        zcounts = zone_model["transition_counts"]
        zones_for_action = sorted(zcounts.loc[zcounts["current_action"] == selected_action, "zone"].unique().tolist())
        if not zones_for_action:
            st.info("Nao ha zonas suficientes para a acao selecionada.")
        else:
            selected_zone = st.selectbox("Zona do campo", zones_for_action, key="seq_zone_selector")
            zone_rankings = get_action_zone_rankings(zone_model, selected_action, selected_zone)
            zone_cases = int(zone_rankings["observed_cases"].iloc[0]) if not zone_rankings.empty else 0
            alert = sample_alert(zone_cases, "acao + zona")
            if alert:
                st.warning(alert)
            with st.expander("Dados por acao e zona"):
                st.dataframe(_format_decision_table(zone_rankings), use_container_width=True, hide_index=True)
            if not zone_rankings.empty:
                zone_value = translate_actions(zone_rankings.sort_values("valor_caminho", ascending=False).head(8), columns=["next_action"])
                st.plotly_chart(
                    create_action_bar_chart(zone_value, "next_action", "valor_caminho", "Caminhos de maior valor nesta zona"),
                    use_container_width=True,
                )

    st.markdown("### O que a acao anterior muda?")
    if second_model["transition_counts"].empty:
        st.info("Nao ha sequencias suficientes para avaliar o contexto anterior.")
    else:
        scounts = second_model["transition_counts"]
        previous_actions = sorted(scounts["previous_action"].unique().tolist())
        current_actions = sorted(scounts["current_action"].unique().tolist())
        c1, c2 = st.columns(2)
        selected_previous = c1.selectbox(
            "Acao anterior",
            previous_actions,
            key="seq_second_previous",
            format_func=action_label,
        )
        valid_current = sorted(scounts.loc[scounts["previous_action"] == selected_previous, "current_action"].unique().tolist())
        selected_current = c2.selectbox(
            "Acao atual",
            valid_current or current_actions,
            key="seq_second_current",
            format_func=action_label,
        )
        second_rankings = get_second_order_rankings(second_model, selected_previous, selected_current)
        second_cases = int(second_rankings["observed_cases"].iloc[0]) if not second_rankings.empty else 0
        alert = sample_alert(second_cases, "sequencia de segunda ordem")
        if alert:
            st.warning(alert)
        if not second_rankings.empty:
            second_value = translate_actions(second_rankings.sort_values("valor_caminho", ascending=False).head(8), columns=["next_action"])
            st.plotly_chart(
                create_action_bar_chart(second_value, "next_action", "valor_caminho", "Caminhos de maior valor na sequencia curta"),
                use_container_width=True,
            )
        with st.expander("Dados da sequencia curta"):
            st.dataframe(_format_decision_table(second_rankings), use_container_width=True, hide_index=True)


def render_offensive_danger_page(events: pd.DataFrame) -> None:
    start_section("Perigo Ofensivo", "")
    sequence_events = add_possession_value_deltas(events)
    if sequence_events.empty:
        st.info("Sem eventos suficientes para estimar perigo ofensivo.")
        return

    shots = sequence_events[sequence_events["is_shot"]].copy()
    non_shots = sequence_events[~sequence_events["is_shot"]].copy()
    total_xg = float(pd.to_numeric(shots["shot_xg"], errors="coerce").fillna(0.0).sum())
    total_shots = int(len(shots))
    possessions = int(sequence_events["possession_sequence_id"].nunique())
    shot_possessions = int(sequence_events.loc[sequence_events["is_shot"], "possession_sequence_id"].nunique())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Finalizacoes", f"{total_shots:,}".replace(",", "."))
    col2.metric("xG", f"{total_xg:.2f}")
    col3.metric("xG por chute", f"{(total_xg / total_shots):.3f}" if total_shots else "0.000")
    col4.metric("Posses com chute", f"{(shot_possessions / possessions):.1%}" if possessions else "0.0%")

    with st.expander("Auditoria da posse"):
        state_values = build_state_values(sequence_events)
        source_counts = sequence_events["possession_id_source"].value_counts().reset_index()
        source_counts.columns = ["origem_posse", "eventos"]
        in_possession_rate = float(sequence_events["event_team_in_possession"].mean()) if "event_team_in_possession" in sequence_events.columns else 0.0
        value_delta_rate = float(sequence_events["value_delta_available"].fillna(False).mean()) if "value_delta_available" in sequence_events.columns else 0.0
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Sequencias", possessions)
        a2.metric("Eventos da equipe em posse", f"{in_possession_rate:.1%}")
        a3.metric("Estados 12x8 usados", max(len(state_values) - 1, 0) if not state_values.empty else 0)
        a4.metric("Eventos com valor calculado", f"{value_delta_rate:.1%}")
        st.dataframe(source_counts, use_container_width=True, hide_index=True)

    alert = sample_alert(len(events), "recorte ofensivo")
    if alert:
        st.warning(alert)

    tab_quality, tab_creation, tab_progression, tab_set_piece, tab_raw = st.tabs(
        [
            "Qualidade das chances",
            "Criacao antes do chute",
            "Progressao territorial",
            "Bola parada",
            "Dados brutos",
        ]
    )

    with tab_quality:
        if shots.empty:
            st.info("Nao ha finalizacoes no recorte atual.")
        else:
            quality = (
                shots.groupby("team_name", dropna=False)
                .agg(
                    finalizacoes=("event_id", "count"),
                    gols=("is_goal_event", "sum"),
                    xg=("shot_xg", "sum"),
                )
                .reset_index()
            )
            quality["xg_por_chute"] = quality["xg"] / quality["finalizacoes"].replace(0, np.nan)
            quality = translate_teams(quality.sort_values("xg", ascending=False), ["team_name"])
            st.plotly_chart(create_action_bar_chart(quality.head(12), "team_name", "xg", "xG por selecao"), use_container_width=True)
            st.dataframe(format_sequence_metrics(quality), use_container_width=True, hide_index=True)

    with tab_creation:
        creation = summarize_sequence_value(non_shots, ["action_family", "action_type", "zone"], include_shots=False)
        if creation.empty:
            st.info("Nao ha acoes anteriores a finalizacao suficientes no recorte.")
        else:
            family_options = [family for family in ACTION_FAMILY_ORDER if family in creation["action_family"].unique()]
            if not family_options:
                st.info("Nao ha familias de acao disponiveis no recorte.")
                return
            selected_family = st.selectbox("Familia de acao", family_options, key="creation_family")
            filtered_creation = creation[creation["action_family"] == selected_family].copy()
            min_cases = st.slider("Ocorrencias minimas", 1, 100, 10, key="creation_min_cases")
            filtered_creation = filtered_creation[filtered_creation["ocorrencias"] >= min_cases]
            if filtered_creation.empty:
                st.info("Nenhuma acao passou pelo minimo de ocorrencias.")
            else:
                action_options = sorted(filtered_creation["action_type"].unique().tolist())
                selected_action = st.selectbox("Acao", action_options, key="creation_action", format_func=action_label)
                action_zone = filtered_creation[filtered_creation["action_type"] == selected_action].copy()
                metric_options = {
                    "Mudanca no xG futuro esperado": ("delta_xg_futuro_medio", "decimal4", "xG futuro"),
                    "Mudanca na chance de finalizacao": ("delta_chance_finalizacao_medio", "percent", "Chance"),
                    "Mudanca no valor da posse": ("delta_valor_posse_medio", "decimal4", "Valor"),
                    "Delta xT eventos": ("delta_xt_medio", "decimal4", "delta xT"),
                    "Chance de a posse terminar em finalizacao": ("chance_finalizacao_futura", "percent", "Chance"),
                    "Finalizacao em ate 5 acoes": ("finalizacao_ate_5", "percent", "Ate 5"),
                }
                metric_label = st.selectbox("Metrica do mapa", list(metric_options.keys()), key="creation_map_metric")
                metric_col, value_format, colorbar = metric_options[metric_label]
                st.plotly_chart(
                    create_zone_metric_heatmap(
                        action_zone,
                        metric_col,
                        f"{metric_label} - {action_label(selected_action)}",
                        colorbar,
                        value_format=value_format,
                    ),
                    use_container_width=True,
                )
                table = translate_actions(filtered_creation.sort_values(metric_col, ascending=False), ["action_type"])
                rankings = translate_actions(
                    filtered_creation.groupby(["action_type"], dropna=False)
                    .agg(
                        ocorrencias=("ocorrencias", "sum"),
                        delta_chance_finalizacao_medio=("delta_chance_finalizacao_medio", "mean"),
                        delta_xg_futuro_medio=("delta_xg_futuro_medio", "mean"),
                        delta_valor_posse_medio=("delta_valor_posse_medio", "mean"),
                        delta_xt_medio=("delta_xt_medio", "mean"),
                        xg_futuro_medio=("xg_futuro_medio", "mean"),
                    )
                    .reset_index()
                    .sort_values("delta_valor_posse_medio", ascending=False),
                    ["action_type"],
                )
                left, right = st.columns(2)
                with left:
                    st.plotly_chart(
                        create_action_bar_chart(rankings.head(12), "action_type", "delta_chance_finalizacao_medio", "Acoes que mais mudam a chance de finalizacao"),
                        use_container_width=True,
                    )
                with right:
                    st.plotly_chart(
                        create_action_bar_chart(rankings.head(12), "action_type", "delta_xg_futuro_medio", "Acoes que mais mudam o xG futuro esperado"),
                        use_container_width=True,
                    )
                scatter = px.scatter(
                    rankings,
                    x="ocorrencias",
                    y="delta_valor_posse_medio",
                    size="ocorrencias",
                    color="delta_xg_futuro_medio",
                    hover_name="action_type",
                    title="Volume e valor medio por acao",
                    color_continuous_scale="Tealgrn",
                )
                scatter.update_layout(
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    font=dict(color="#111827", size=13),
                    title=dict(font=dict(color="#111827", size=18)),
                    xaxis=dict(gridcolor="#e5e7eb"),
                    yaxis=dict(gridcolor="#e5e7eb"),
                )
                st.plotly_chart(scatter, use_container_width=True)
                with st.expander("Dados por acao e zona", expanded=True):
                    st.dataframe(format_sequence_metrics(table), use_container_width=True, hide_index=True)

    with tab_progression:
        progression = summarize_sequence_value(non_shots, ["action_family", "action_type", "zone"], include_shots=False)
        progression = progression[progression["action_type"].isin(["Pass", "Carry", "Dribble"])] if not progression.empty else progression
        if progression.empty:
            st.info("Nao ha acoes de progressao suficientes no recorte.")
        else:
            prog_metric_options = {
                "Mudanca no valor da posse": ("delta_valor_posse_medio", "decimal4", "Valor"),
                "Mudanca no xG futuro esperado": ("delta_xg_futuro_medio", "decimal4", "xG futuro"),
                "Mudanca na chance de finalizacao": ("delta_chance_finalizacao_medio", "percent", "Chance"),
                "Delta xT eventos": ("delta_xt_medio", "decimal4", "delta xT"),
                "Progressao media": ("progressao_media", "decimal4", "Metros"),
                "Entradas no terco final": ("entrada_terco_final_pct", "percent", "Entrada"),
                "Entradas na area": ("entrada_area_pct", "percent", "Area"),
                "Finalizacao em ate 3 acoes": ("finalizacao_ate_3", "percent", "Ate 3"),
            }
            prog_action = st.selectbox(
                "Acao de progressao",
                sorted(progression["action_type"].unique().tolist()),
                key="progression_action",
                format_func=action_label,
            )
            prog_metric_label = st.selectbox("Metrica", list(prog_metric_options.keys()), key="progression_metric")
            prog_col, prog_format, prog_colorbar = prog_metric_options[prog_metric_label]
            prog_zone = progression[progression["action_type"] == prog_action]
            st.plotly_chart(
                create_zone_metric_heatmap(
                    prog_zone,
                    prog_col,
                    f"{prog_metric_label} - {action_label(prog_action)}",
                    prog_colorbar,
                    value_format=prog_format,
                ),
                use_container_width=True,
            )
            prog_rank = translate_actions(
                progression.groupby("action_type", dropna=False)
                .agg(
                    ocorrencias=("ocorrencias", "sum"),
                    delta_valor_posse_medio=("delta_valor_posse_medio", "mean"),
                    delta_xg_futuro_medio=("delta_xg_futuro_medio", "mean"),
                    delta_xt_medio=("delta_xt_medio", "mean"),
                    progressao_media=("progressao_media", "mean"),
                )
                .reset_index()
                .sort_values("delta_valor_posse_medio", ascending=False),
                ["action_type"],
            )
            st.plotly_chart(
                create_action_bar_chart(prog_rank.head(12), "action_type", "delta_valor_posse_medio", "Conducoes, passes e dribles por mudanca de valor"),
                use_container_width=True,
            )
            with st.expander("Dados de progressao"):
                st.dataframe(format_sequence_metrics(translate_actions(progression, ["action_type"])), use_container_width=True, hide_index=True)

    with tab_set_piece:
        set_piece = sequence_events[sequence_events["action_family"].eq("Bola parada")].copy()
        if set_piece.empty:
            st.info("Nao ha eventos de bola parada no recorte.")
        else:
            set_piece_summary = summarize_sequence_value(set_piece, ["team_name", "action_type"], include_shots=True)
            set_piece_summary = translate_teams(translate_actions(set_piece_summary, ["action_type"]), ["team_name"])
            st.plotly_chart(
                create_action_bar_chart(set_piece_summary.head(12), "team_name", "xg_futuro_total", "xG futuro em posses de bola parada"),
                use_container_width=True,
            )
            st.dataframe(format_sequence_metrics(set_piece_summary), use_container_width=True, hide_index=True)

    with tab_raw:
        team_future = summarize_sequence_value(sequence_events, ["team_name"], include_shots=False)
        player_future = summarize_sequence_value(sequence_events, ["player_name"], include_shots=False)
        action_future = summarize_sequence_value(sequence_events, ["action_family", "action_type"], include_shots=False)
        with st.expander("Equipe"):
            st.dataframe(format_sequence_metrics(translate_teams(team_future, ["team_name"])), use_container_width=True, hide_index=True)
        with st.expander("Jogador"):
            st.dataframe(format_sequence_metrics(player_future.sort_values("xg_futuro_total", ascending=False).head(100)), use_container_width=True, hide_index=True)
        with st.expander("Acao"):
            st.dataframe(format_sequence_metrics(translate_actions(action_future, ["action_type"])), use_container_width=True, hide_index=True)
        with st.expander("Eventos com valor futuro"):
            cols = [
                "match_id",
                "team_name",
                "player_name",
                "action_family",
                "action_type",
                "zone",
                "future_shot",
                "future_goal",
                "future_xg",
                "sum_future_xg",
                "actions_until_shot",
                "shot_within_3",
                "shot_within_5",
                "shot_within_10",
                "possession_id_source",
                "possession_event_index",
                "possession_event_count",
                "event_team_in_possession",
                "value_state",
                "visual_zone_origin",
                "visual_zone_destination",
                "value_state_origin",
                "value_state_destination",
                "state_origin",
                "state_destination",
                "V_shot_origin",
                "V_shot_destination",
                "V_xg_origin",
                "V_xg_destination",
                "xt_origin",
                "xt_destination",
                "delta_chance_finalizacao",
                "delta_xg_futuro",
                "delta_valor_posse",
                "delta_xt",
                "territorial_progression",
                "final_third_entry",
                "box_entry",
            ]
            st.dataframe(format_sequence_metrics(sequence_events[cols].head(1000)), use_container_width=True, hide_index=True)


def render_models_validation_page(events: pd.DataFrame, availability: dict, filtered_events: pd.DataFrame) -> None:
    start_section(
        "Confiabilidade",
        "Amostra, estabilidade e limites do recorte.",
    )
    render_quality_notes(availability, filtered_events)
    with st.expander("Suavizacao de probabilidades"):
        render_bayesian(filtered_events)
    with st.expander("Validacao 2018 x 2022"):
        render_transfer(events)
    with st.expander("Similaridade entre selecoes"):
        render_similarity(filtered_events)
    with st.expander("Cenario exploratorio"):
        render_model_2026(events[events["year"].isin([2018, 2022])])


def render_methodology_page() -> None:
    start_section(
        "Notas Metodologicas",
        "Definicoes curtas para leitura das metricas.",
    )
    st.markdown(
        """
<div class="method-note"><strong>xG</strong><br>
O xG descreve a qualidade estimada de uma finalizacao. Ele nao mede sozinho dominio territorial,
controle, pressao, tomada de decisao ou qualidade coletiva da posse.</div>

<div class="method-note"><strong>Valor da posse</strong><br>
Passes, conducoes, dribles e recuperacoes nao recebem xG proprio. O app estima se a posse ficou
em estado melhor ou pior depois da acao, usando eventos, coordenadas e valor futuro.</div>

<div class="method-note"><strong>Valor futuro da posse</strong><br>
Para cada evento, o app procura a proxima finalizacao posterior na mesma posse. Esse xG e associado
a acoes anteriores, mas continua pertencendo ao chute.</div>

<div class="method-note"><strong>Sequencias</strong><br>
As sequencias mostram frequencias observadas entre acoes e zonas. Elas organizam padroes de fluxo,
valor futuro e mudanca de valor da posse, mas nao provam causalidade.</div>

<div class="method-note"><strong>Amostra e interpretacao</strong><br>
Toda leitura deve ser entendida como "no recorte analisado". Em contextos com poucos eventos, o
dashboard mostra alerta e trata probabilidades como pistas exploratorias.</div>

<div class="method-note"><strong>Dados de evento</strong><br>
Eventos StatsBomb registram acoes com bola e algumas informacoes contextuais. Sem tracking data,
nao vemos toda movimentacao sem bola, cobertura defensiva, linhas de passe disponiveis ou pressao
espacial completa.</div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_explorer(events: pd.DataFrame) -> None:
    st.markdown("### Explorador de estatisticas")

    if events.empty:
        st.info("Nao ha dados suficientes para montar o explorador com os filtros atuais.")
        return

    dimension_options = {
        "Selecao": "team_name",
        "Jogador": "player_name",
        "Tipo de acao": "action_type",
        "Zona": "zone",
        "Periodo": "period_label",
        "Momento do time": "match_state",
        "Tempo restante": "time_remaining_bucket",
    }
    metric_options = {
        "Total de eventos": "event_count",
        "xG somado": "xg_sum",
        "Eventos sob pressao (%)": "under_pressure_pct",
        "Mudancas de posse": "possession_changes",
        "Gols detectados": "goals",
        "Minutos restantes medios": "minutes_remaining_avg",
    }

    col1, col2, col3 = st.columns(3)
    dimension_label = col1.selectbox("Agrupar por", list(dimension_options.keys()), key="stats_dimension")
    metric_label = col2.selectbox("Metrica", list(metric_options.keys()), key="stats_metric")
    top_n = col3.slider("Top N", min_value=5, max_value=30, value=12, key="stats_top_n")

    group_col = dimension_options[dimension_label]
    summary = (
        events.groupby(group_col, dropna=False)
        .agg(
            event_count=("event_id", "count"),
            xg_sum=("shot_xg", "sum"),
            under_pressure_pct=("under_pressure", lambda s: float(s.mean()) * 100 if len(s) else 0.0),
            possession_changes=("possession_change", "sum"),
            goals=("is_goal_event", "sum"),
            minutes_remaining_avg=("minutes_remaining", "mean"),
        )
        .reset_index()
        .rename(columns={group_col: "segmento"})
    )
    if group_col == "action_type":
        summary["segmento"] = summary["segmento"].map(action_label)
    elif group_col in {"team_name", "possession_team_name"}:
        summary["segmento"] = summary["segmento"].map(team_label)

    value_col = metric_options[metric_label]
    ranking = summary.sort_values(value_col, ascending=False).head(top_n)

    st.plotly_chart(
        create_action_bar_chart(ranking, "segmento", value_col, f"{metric_label} por {dimension_label.lower()}"),
        use_container_width=True,
    )
    st.dataframe(
        ranking.rename(columns={"segmento": dimension_label}),
        use_container_width=True,
        hide_index=True,
    )


def render_action_maps(events: pd.DataFrame, key_prefix: str = "map") -> None:
    start_section("Mapa de Acoes", "")

    if events.empty:
        st.info("Nao ha eventos para os filtros atuais.")
        return

    teams = sorted(events["team_name"].dropna().unique().tolist())
    actions = sorted(events["action_type"].dropna().unique().tolist())
    zones = sorted(events["zone"].dropna().unique().tolist())

    default_teams = _top_values(events, "team_name", 2)
    default_actions = _available_preferred_actions(actions, ["Shot", "Carry", "Dribble", "Pass"], fallback_limit=3)

    teams_key = f"{key_prefix}_map_selected_teams"
    actions_key = f"{key_prefix}_map_selected_actions"
    zones_key = f"{key_prefix}_map_selected_zones"
    color_key = f"{key_prefix}_map_color_by_action"
    size_key = f"{key_prefix}_map_marker_size"
    opacity_key = f"{key_prefix}_map_marker_opacity"
    max_points_key = f"{key_prefix}_map_max_points"
    pitch_color_key = f"{key_prefix}_map_pitch_color"

    st.session_state.setdefault(teams_key, default_teams)
    st.session_state.setdefault(actions_key, default_actions)
    st.session_state.setdefault(zones_key, zones)

    with st.expander("Filtros do mapa", expanded=True):
        p1, p2, p3, p4 = st.columns(4)
        if p1.button("Finalizacoes", use_container_width=True, key=f"{key_prefix}_map_preset_shots"):
            st.session_state[actions_key] = _available_preferred_actions(actions, ["Shot"], fallback_limit=1)
        if p2.button("Progressao", use_container_width=True, key=f"{key_prefix}_map_preset_progression"):
            st.session_state[actions_key] = _available_preferred_actions(actions, ["Carry", "Dribble", "Pass"], fallback_limit=3)
        if p3.button("Pressao", use_container_width=True, key=f"{key_prefix}_map_preset_pressure"):
            st.session_state[actions_key] = _available_preferred_actions(actions, ["Pressure", "Duel", "Interception"], fallback_limit=3)
        if p4.button("Top volume", use_container_width=True, key=f"{key_prefix}_map_preset_volume"):
            st.session_state[actions_key] = _top_values(events, "action_type", 4)

        st.session_state[teams_key] = [team for team in st.session_state[teams_key] if team in teams] or default_teams
        st.session_state[actions_key] = [action for action in st.session_state[actions_key] if action in actions] or default_actions
        st.session_state[zones_key] = [zone for zone in st.session_state[zones_key] if zone in zones] or zones

        col1, col2 = st.columns(2)
        selected_teams = col1.multiselect(
            "Selecoes no mapa",
            options=teams,
            format_func=team_label,
            key=teams_key,
        )
        selected_actions = col2.multiselect(
            "Acoes no mapa",
            options=actions,
            format_func=action_label,
            key=actions_key,
        )
        selected_zones = st.multiselect(
            "Zonas no mapa",
            options=zones,
            key=zones_key,
        )

        v1, v2, v3, v4 = st.columns(4)
        color_by_action = v1.checkbox("Cor por acao", value=True, key=color_key)
        marker_size = v2.slider("Tamanho", 3, 14, 7, key=size_key)
        marker_opacity = v3.slider("Opacidade", 0.2, 1.0, 0.88, 0.05, key=opacity_key)
        max_points = v4.slider("Eventos no desenho", 200, 10000, 2500, 200, key=max_points_key)
        pitch_color = st.color_picker("Cor do campo", "#127a4f", key=pitch_color_key)

    map_events = events.copy()
    if selected_teams:
        map_events = map_events[map_events["team_name"].isin(selected_teams)]
    if selected_actions:
        map_events = map_events[map_events["action_type"].isin(selected_actions)]
    if selected_zones:
        map_events = map_events[map_events["zone"].isin(selected_zones)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Eventos no mapa", f"{len(map_events):,}".replace(",", "."))
    c2.metric("Selecoes", map_events["team_name"].nunique() if not map_events.empty else 0)
    c3.metric("Acoes", map_events["action_type"].nunique() if not map_events.empty else 0)

    if map_events.empty:
        st.info("A combinacao escolhida nao tem eventos com os filtros atuais.")
        return

    if color_by_action:
        render_action_legend(_legend_actions_for_frame(map_events), title="Legenda do campo")
    render_pitch_map(
        map_events,
        title="Mapa de ações",
        key=f"{key_prefix}_pitch_scatter",
        color_by_action=color_by_action,
        marker_size=marker_size,
        marker_opacity=marker_opacity,
        pitch_color=pitch_color,
        export_mode=_is_export_mode(),
    )

    zone_counts = map_events.groupby(["zone"]).size().reset_index(name="event_count").sort_values("event_count", ascending=False)
    st.plotly_chart(create_zone_heatmap(zone_counts), use_container_width=True, key=f"{key_prefix}_zone_heatmap")
    st.dataframe(zone_counts, use_container_width=True, hide_index=True)


def render_field_thirds(events: pd.DataFrame, key_prefix: str = "thirds") -> None:
    start_section(
        "Campo por Tercos",
        "Escolha uma selecao e veja as sequencias mais comuns em defesa, meio e ataque.",
    )

    if events.empty:
        st.info("Nao ha eventos suficientes nos filtros atuais.")
        return

    teams = sorted(events["team_name"].dropna().unique().tolist())
    selected_team = st.selectbox("Selecao", teams, format_func=team_label, key=f"{key_prefix}_thirds_team")
    team_events = events[(events["team_name"] == selected_team) & (events["next_action"] != "END")].copy()
    team_events = team_events[team_events["field_third"].ne("Desconhecido")]
    if team_events.empty:
        st.info("Nao ha eventos com coordenadas para esta selecao nos filtros atuais.")
        return

    team_events["current_xg"] = pd.to_numeric(team_events["shot_xg"], errors="coerce").fillna(0.0)
    next_xg_source = team_events["next_shot_xg"] if "next_shot_xg" in team_events.columns else pd.Series(0.0, index=team_events.index)
    team_events["next_xg"] = pd.to_numeric(next_xg_source, errors="coerce").fillna(0.0)
    team_events["xg_delta"] = team_events["next_xg"] - team_events["current_xg"]

    transitions = (
        team_events.groupby(["field_third", "action_type", "next_action"], dropna=False)
        .agg(
            casos=("event_id", "count"),
            xg_delta_medio=("xg_delta", "mean"),
            xg_medio_proxima_acao=("next_xg", "mean"),
        )
        .reset_index()
        .rename(columns={"action_type": "current_action"})
    )
    transitions["casos_observados_no_terco"] = transitions.groupby("field_third")["casos"].transform("sum")
    transitions["probability"] = transitions["casos"] / transitions["casos_observados_no_terco"].replace(0, np.nan)
    best_by_third = (
        transitions.sort_values(["field_third", "probability", "casos"], ascending=[True, False, False])
        .groupby("field_third", as_index=False)
        .head(1)
    )

    pitch_frame = translate_actions(best_by_third, columns=["current_action", "next_action"])
    st.plotly_chart(
        create_thirds_probability_pitch(pitch_frame, title=f"Campo por tercos - {team_label(selected_team)}"),
        use_container_width=True,
        key=f"{key_prefix}_thirds_pitch",
    )

    detail = transitions.sort_values(["field_third", "probability", "casos"], ascending=[True, False, False]).copy()
    detail = translate_actions(detail, columns=["current_action", "next_action"])
    detail = detail.rename(
        columns={
            "field_third": "terco",
            "current_action": "acao_atual",
            "next_action": "proxima_acao",
            "probability": "probabilidade",
            "xg_delta_medio": "variacao_xg_evento_seguinte",
            "xg_medio_proxima_acao": "xg_medio_evento_seguinte",
        }
    )
    st.dataframe(
        detail[
            [
                "terco",
                "acao_atual",
                "proxima_acao",
                "casos",
                "probabilidade",
                "variacao_xg_evento_seguinte",
                "xg_medio_evento_seguinte",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_first_order(events: pd.DataFrame) -> None:
    start_section("Proxima Acao", "")

    model = build_first_order_model(events)
    if model["transition_counts"].empty:
        st.info("Nao ha transicoes suficientes para construir a matriz com os filtros atuais.")
        return

    st.plotly_chart(create_transition_heatmap(_top_transition_matrix(model["transition_matrix"]), "Proxima acao por acao atual"), use_container_width=True)
    st.dataframe(_top_transition_matrix(model["transition_matrix"]), use_container_width=True)

    available_actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
    selected_action = st.selectbox("Acao atual", options=available_actions, key="first_order_action", format_func=action_label)
    rankings = get_action_rankings(model, selected_action)

    st.dataframe(_format_decision_table(rankings), use_container_width=True, hide_index=True)


def render_action_zone(events: pd.DataFrame) -> None:
    start_section("Acao + Zona", "")

    model = build_action_zone_model(events)
    if model["transition_counts"].empty:
        st.info("Nao ha observacoes suficientes por acao e zona nos filtros atuais.")
        return

    col1, col2 = st.columns(2)
    actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
    zones = sorted(model["transition_counts"]["zone"].unique().tolist())
    selected_action = col1.selectbox("Acao atual", actions, key="zone_action", format_func=action_label)
    selected_zone = col2.selectbox("Zona", zones, key="zone_selector")

    rankings = get_action_zone_rankings(model, selected_action, selected_zone)
    st.dataframe(_format_decision_table(rankings), use_container_width=True, hide_index=True)

    total_cases = int(rankings["observed_cases"].iloc[0]) if not rankings.empty else 0
    if 0 < total_cases < 30:
        st.warning("Baixa confianca: poucos eventos observados.")


def render_second_order(events: pd.DataFrame) -> None:
    start_section("Sequencia Curta", "")

    model = build_second_order_model(events)
    if model["transition_counts"].empty:
        st.info("Nao ha sequencias suficientes para este encadeamento.")
        return

    col1, col2 = st.columns(2)
    previous_actions = sorted(model["transition_counts"]["previous_action"].unique().tolist())
    current_actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
    selected_previous = col1.selectbox("Acao anterior", previous_actions, key="second_prev", format_func=action_label)
    selected_current = col2.selectbox("Acao atual", current_actions, key="second_curr", format_func=action_label)

    rankings = get_second_order_rankings(model, selected_previous, selected_current)
    st.dataframe(_format_decision_table(rankings), use_container_width=True, hide_index=True)

    if not rankings.empty:
        total_cases = int(rankings["observed_cases"].iloc[0])
        st.metric("Casos observados", total_cases, confidence_label(total_cases))
        if total_cases < 30:
            st.warning("Baixa confianca: poucos eventos observados.")


def render_bayesian(events: pd.DataFrame) -> None:
    start_section("Suavizacao de Probabilidades", "")

    alpha = st.slider("Alpha do prior Dirichlet", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    context_mode = st.radio(
        "Contexto",
        options=["Acao atual", "Acao atual + zona", "Acao anterior + acao atual"],
        horizontal=True,
    )

    if context_mode == "Acao atual":
        model = build_first_order_model(events)
        actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
        if not actions:
            st.info("Nenhum contexto encontrado para os filtros selecionados.")
            return
        selected_action = st.selectbox("Acao atual", actions, key="bayes_action_only", format_func=action_label)
        base = get_action_rankings(model, selected_action)
        context_label = action_label(selected_action)
    elif context_mode == "Acao atual + zona":
        model = build_action_zone_model(events)
        actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
        zones = sorted(model["transition_counts"]["zone"].unique().tolist())
        if not actions or not zones:
            st.info("Nenhum contexto encontrado para os filtros selecionados.")
            return
        col1, col2 = st.columns(2)
        selected_action = col1.selectbox("Acao atual", actions, key="bayes_action_zone_action", format_func=action_label)
        selected_zone = col2.selectbox("Zona", zones, key="bayes_action_zone_zone")
        base = get_action_zone_rankings(model, selected_action, selected_zone)
        context_label = f"{action_label(selected_action)} | {selected_zone}"
    else:
        model = build_second_order_model(events)
        previous_actions = sorted(model["transition_counts"]["previous_action"].unique().tolist())
        current_actions = sorted(model["transition_counts"]["current_action"].unique().tolist())
        if not previous_actions or not current_actions:
            st.info("Nenhum contexto encontrado para os filtros selecionados.")
            return
        col1, col2 = st.columns(2)
        selected_previous = col1.selectbox("Acao anterior", previous_actions, key="bayes_prev", format_func=action_label)
        selected_current = col2.selectbox("Acao atual", current_actions, key="bayes_curr", format_func=action_label)
        base = get_second_order_rankings(model, selected_previous, selected_current)
        context_label = f"{action_label(selected_previous)} -> {action_label(selected_current)}"

    if base.empty:
        st.info("Nenhum contexto encontrado para os filtros selecionados.")
        return

    bayes_df = add_dirichlet_posterior(base, alpha=alpha)
    bayes_df["confidence"] = bayes_df["observed_cases"].map(confidence_label)

    st.metric("Contexto", context_label)
    st.dataframe(_format_decision_table(bayes_df), use_container_width=True, hide_index=True)

    if int(bayes_df["observed_cases"].iloc[0]) < 30:
        st.warning("Baixa confianca: poucos eventos observados.")


def render_transfer(events: pd.DataFrame) -> None:
    start_section("Comparacao 2018 x 2022", "")

    transfer = evaluate_year_transfer(events, train_year=2018, test_year=2022)
    results = transfer["metrics"]
    if results.empty:
        st.info("Nao foi possivel calcular a transferencia 2018 x 2022 com os dados atuais.")
        return

    display_results = results.copy()
    display_results["model"] = display_results["model"].replace({"Markov 2018": "Sequencias 2018", "Baseline 2018": "Frequencia geral 2018"})
    st.dataframe(display_results, use_container_width=True, hide_index=True)
    if transfer["markov_beats_baseline"]:
        st.success(transfer["interpretation"])
    else:
        st.info(transfer["interpretation"])

    markov_row = results.loc[results["model"] == "Markov 2018"].iloc[0]
    baseline_row = results.loc[results["model"] == "Baseline 2018"].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Acerto Top-1", _safe_percent(markov_row["top_1_accuracy"]), style_metric_delta(markov_row["top_1_accuracy"] - baseline_row["top_1_accuracy"]))
    col2.metric("Acerto Top-3", _safe_percent(markov_row["top_3_accuracy"]), style_metric_delta(markov_row["top_3_accuracy"] - baseline_row["top_3_accuracy"]))
    col3.metric("Ganho em log loss", f"{markov_row['log_loss']:.3f}", f"{baseline_row['log_loss'] - markov_row['log_loss']:.3f}")


def render_similarity(events: pd.DataFrame) -> None:
    start_section("Similaridade entre Selecoes", "")

    vectors = build_team_transition_vectors(events)
    if vectors.empty:
        st.info("Nao ha dados suficientes para calcular similaridade entre selecoes.")
        return

    similarity = compute_similarity_matrix(vectors).rename(index=team_label, columns=team_label)
    st.plotly_chart(create_similarity_heatmap(similarity), use_container_width=True)

    teams = similarity.index.tolist()
    selected_team = st.selectbox("Selecao de referencia", teams, key="similarity_team")
    rankings = similarity.loc[selected_team].drop(labels=[selected_team], errors="ignore").sort_values(ascending=False).reset_index()
    rankings.columns = ["selection", "similarity"]
    st.dataframe(rankings, use_container_width=True, hide_index=True)


def render_compare_players(events: pd.DataFrame, key_prefix: str = "players") -> None:
    render_section_header("Comparação de jogadores", "Perfil comparativo com produção final, valor da posse e mapas de ações.")

    comparison_events = add_possession_value_deltas(add_threat_features(events))
    summary = build_entity_summary(comparison_events, "player_name")
    if summary.empty or summary["player_name"].nunique() < 2:
        st.info("Nao ha jogadores suficientes nos filtros atuais para comparar.")
        return

    options = sorted(summary["player_name"].tolist())
    col1, col2 = st.columns(2)
    player_a = col1.selectbox("Jogador A", options, index=0, key=f"{key_prefix}_player_a")
    default_b = 1 if len(options) > 1 else 0
    player_b = col2.selectbox("Jogador B", options, index=default_b, key=f"{key_prefix}_player_b")
    profiles = _build_performance_profiles(comparison_events, "player_name", [player_a, player_b])
    if profiles.empty:
        st.info("Nao ha dados suficientes para montar perfis comparaveis.")
        return

    for player in [player_a, player_b]:
        player_events = int(_metric_value(profiles, "player_name", player, "events"))
        alert = sample_alert(player_events, f"jogador {player}")
        if alert:
            st.warning(alert)

    cols = st.columns(2)
    for idx, player in enumerate([player_a, player_b]):
        with cols[idx]:
            render_player_summary_card(player, _player_summary_stats(profiles, player), PLAYER_COLORS[idx])

    production_metrics = ["events", "goals", "assists", "shots", "xg", "xg_per_shot"]
    value_metrics = ["delta_xt_total", "future_xg_associated", "future_shot_rate", "box_entries", "final_third_entries"]
    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_profile_chart(profiles, "player_name", production_metrics, "Produção final", key_prefix=f"{key_prefix}_production")
    with chart_right:
        _render_profile_chart(profiles, "player_name", value_metrics, "Valor da posse", key_prefix=f"{key_prefix}_value")

    action_mix = translate_actions(
        comparison_events[comparison_events["player_name"].isin([player_a, player_b])]
        .groupby(["player_name", "action_type"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    family_fig = render_action_family_chart(action_mix, "player_name", "Famílias de ações dos jogadores")
    action_mix_fig = render_action_mix_chart(action_mix, "player_name", "Mix de ações dos jogadores")
    reading = _action_mix_reading(action_mix, "player_name")
    if reading:
        st.caption(reading)
    render_action_legend(_legend_actions_for_frame(comparison_events[comparison_events["player_name"].isin([player_a, player_b])]), title="Cores das acoes")
    st.plotly_chart(family_fig, use_container_width=True, key=f"{key_prefix}_player_action_family_chart")
    with st.expander("Mix detalhado de ações", expanded=True):
        st.plotly_chart(action_mix_fig, use_container_width=True, key=f"{key_prefix}_player_action_mix_chart")
        st.dataframe(action_mix, use_container_width=True, hide_index=True)

    with st.expander("Mapas de ações dos jogadores", expanded=True):
        m0, m1, m2, m3 = st.columns(4)
        action_scope = m0.selectbox(
            "Ações no mapa",
            ["Todas", "Finalizações", "Passes", "Conduções", "Dribles", "Pressões e recuperações"],
            key=f"{key_prefix}_player_map_action_scope",
        )
        player_marker_size = m1.slider("Tamanho dos pontos", 3, 14, 7, key=f"{key_prefix}_player_map_marker_size")
        player_marker_opacity = m2.slider("Opacidade dos pontos", 0.2, 1.0, 0.88, 0.05, key=f"{key_prefix}_player_map_marker_opacity")
        player_pitch_color = m3.color_picker("Cor do campo", "#127a4f", key=f"{key_prefix}_player_map_pitch_color")
        scope_actions = {
            "Finalizações": ["Shot"],
            "Passes": ["Pass"],
            "Conduções": ["Carry"],
            "Dribles": ["Dribble"],
            "Pressões e recuperações": ["Pressure", "Ball Recovery", "Interception"],
        }.get(action_scope)
        map_scope_events = events[events["player_name"].isin([player_a, player_b])]
        if scope_actions:
            map_scope_events = map_scope_events[map_scope_events["action_type"].isin(scope_actions)]
        render_action_legend(_legend_actions_for_frame(map_scope_events), title="Legenda do campo")
        left, right = st.columns(2)
        with left:
            player_a_events = events[events["player_name"] == player_a]
            if scope_actions:
                player_a_events = player_a_events[player_a_events["action_type"].isin(scope_actions)]
            render_pitch_map(
                player_a_events,
                title=f"Mapa de ações - {player_a}",
                key=f"{key_prefix}_player_a_pitch_map",
                color_by_action=True,
                marker_size=player_marker_size,
                marker_opacity=player_marker_opacity,
                pitch_color=player_pitch_color,
                export_mode=_is_export_mode(),
            )
            st.caption(_map_summary(player_a_events))
        with right:
            player_b_events = events[events["player_name"] == player_b]
            if scope_actions:
                player_b_events = player_b_events[player_b_events["action_type"].isin(scope_actions)]
            render_pitch_map(
                player_b_events,
                title=f"Mapa de ações - {player_b}",
                key=f"{key_prefix}_player_b_pitch_map",
                color_by_action=True,
                marker_size=player_marker_size,
                marker_opacity=player_marker_opacity,
                pitch_color=player_pitch_color,
                export_mode=_is_export_mode(),
            )
            st.caption(_map_summary(player_b_events))

    summary_table = profiles[
        [
            "player_name",
            "events",
            "xg",
            "delta_xt_total",
            "future_xg_associated",
            "goals",
            "assists",
            "box_entries",
            "final_third_entries",
        ]
    ].rename(
        columns={
            "player_name": "Jogador",
            "events": "Total de ações",
            "xg": "xG",
            "delta_xt_total": "Delta xT total",
            "future_xg_associated": "xG futuro associado",
            "goals": "Gols",
            "assists": "Assistências",
            "box_entries": "Entradas na área",
            "final_third_entries": "Entradas no terço final",
        }
    )
    render_section_header("Tabela resumida", "Principais métricas da comparação.")
    render_pdf_table(summary_table)

    with st.expander("Tabela completa de comparacao"):
        base_metrics = [
            "total_actions",
            "passes",
            "shots",
            "goals",
            "assists",
            "xg",
            "delta_xt_total",
            "delta_xt_mean",
            "future_xg_associated",
            "future_shot_rate",
            "box_entries",
            "final_third_entries",
            "avg_actions_per_match",
        ]
        comparison_table = format_comparison_table(summary, "player_name", player_a, player_b, base_metrics)
        st.dataframe(_format_comparison_display(comparison_table, "player_name"), use_container_width=True, hide_index=True)
        st.dataframe(profiles, use_container_width=True, hide_index=True)


def render_compare_teams(events: pd.DataFrame, key_prefix: str = "teams") -> None:
    start_section("Comparar Equipes", "")

    comparison_events = add_possession_value_deltas(add_threat_features(events))
    summary = build_entity_summary(comparison_events, "team_name")
    if summary.empty or summary["team_name"].nunique() < 2:
        st.info("Nao ha equipes suficientes nos filtros atuais para comparar.")
        return

    options = sorted(summary["team_name"].tolist())
    col1, col2 = st.columns(2)
    team_a = col1.selectbox("Equipe A", options, index=0, key=f"{key_prefix}_team_a", format_func=team_label)
    default_b = 1 if len(options) > 1 else 0
    team_b = col2.selectbox("Equipe B", options, index=default_b, key=f"{key_prefix}_team_b", format_func=team_label)
    profiles = _build_performance_profiles(comparison_events, "team_name", [team_a, team_b])
    if profiles.empty:
        st.info("Nao ha dados suficientes para montar perfis comparaveis.")
        return

    for team in [team_a, team_b]:
        team_events = int(_metric_value(profiles, "team_name", team, "events"))
        alert = sample_alert(team_events, f"equipe {team_label(team)}")
        if alert:
            st.warning(alert)

    vectors = build_team_transition_vectors(events)
    similarity_score = None
    if not vectors.empty and team_a in vectors.index and team_b in vectors.index:
        similarity = compute_similarity_matrix(vectors)
        similarity_score = float(similarity.loc[team_a, team_b])

    _visual_metric_row(profiles, "team_name", [team_a, team_b])

    if similarity_score is not None:
        st.metric("Similaridade de fluxo entre as equipes", f"{similarity_score:.3f}")

    production_metrics = ["events", "goals", "assists", "shots", "xg", "xg_per_shot"]
    value_metrics = ["delta_xt_total", "future_xg_associated", "future_shot_rate", "box_entries", "final_third_entries"]
    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_profile_chart(profiles, "team_name", production_metrics, "Produção final", translate_entity=True, key_prefix=f"{key_prefix}_production")
    with chart_right:
        _render_profile_chart(profiles, "team_name", value_metrics, "Valor da posse", translate_entity=True, key_prefix=f"{key_prefix}_value")

    action_mix = translate_actions(
        comparison_events[comparison_events["team_name"].isin([team_a, team_b])]
        .groupby(["team_name", "action_type"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    action_mix = translate_teams(action_mix, ["team_name"])
    family_fig = render_action_family_chart(action_mix, "team_name", "Famílias de ações das equipes")
    action_mix_fig = render_action_mix_chart(action_mix, "team_name", "Mix de ações das equipes")
    reading = _action_mix_reading(action_mix, "team_name")
    if reading:
        st.caption(reading)
    render_action_legend(_legend_actions_for_frame(comparison_events[comparison_events["team_name"].isin([team_a, team_b])]), title="Cores das acoes")
    st.plotly_chart(family_fig, use_container_width=True, key=f"{key_prefix}_team_action_family_chart")
    with st.expander("Mix detalhado de ações", expanded=True):
        st.plotly_chart(action_mix_fig, use_container_width=True, key=f"{key_prefix}_team_action_mix_chart")
        st.dataframe(action_mix, use_container_width=True, hide_index=True)

    zone_counts = comparison_events[comparison_events["team_name"].isin([team_a, team_b])].groupby(["team_name", "zone"]).size().reset_index(name="event_count")
    with st.expander("Mapas de territorio por equipe"):
        left, right = st.columns(2)
        with left:
            st.plotly_chart(create_zone_heatmap(zone_counts[zone_counts["team_name"] == team_a], title=f"Zonas - {team_label(team_a)}"), use_container_width=True, key=f"{key_prefix}_team_a_zone_map")
        with right:
            st.plotly_chart(create_zone_heatmap(zone_counts[zone_counts["team_name"] == team_b], title=f"Zonas - {team_label(team_b)}"), use_container_width=True, key=f"{key_prefix}_team_b_zone_map")

    with st.expander("Tabela completa de comparacao"):
        base_metrics = [
            "total_actions",
            "passes",
            "shots",
            "goals",
            "assists",
            "xg",
            "delta_xt_total",
            "delta_xt_mean",
            "future_xg_associated",
            "future_shot_rate",
            "box_entries",
            "final_third_entries",
            "attacking_zone_rate",
        ]
        comparison_table = format_comparison_table(summary, "team_name", team_a, team_b, base_metrics)
        st.dataframe(_format_comparison_display(comparison_table, "team_name"), use_container_width=True, hide_index=True)
        st.dataframe(translate_teams(profiles, ["team_name"]), use_container_width=True, hide_index=True)


def render_model_2026(events: pd.DataFrame) -> None:
    start_section("Cenario Exploratorio", "")

    alpha = st.slider("Alpha de suavizacao", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    model = build_second_order_model(events)
    action_zone_model = build_action_zone_model(events)

    actions = sorted(events["action_type"].dropna().unique().tolist())
    zones = list(FIELD_ZONES.keys())
    col1, col2, col3 = st.columns(3)
    selected_action = col1.selectbox("Acao atual", actions, key="model_2026_action", format_func=action_label)
    selected_zone = col2.selectbox("Zona", zones, key="model_2026_zone")
    previous_choice = col3.selectbox(
        "Acao anterior (opcional)",
        ["Sem contexto anterior"] + actions,
        key="model_2026_prev",
        format_func=lambda value: value if value == "Sem contexto anterior" else action_label(value),
    )

    if previous_choice == "Sem contexto anterior":
        base = get_action_zone_rankings(action_zone_model, selected_action, selected_zone)
    else:
        base = get_second_order_rankings(model, previous_choice, selected_action)
        if base.empty:
            base = get_action_zone_rankings(action_zone_model, selected_action, selected_zone)

    if base.empty:
        st.info("Nenhuma combinacao encontrada. O app aplicara suavizacao quando houver contexto semelhante disponivel.")
        return

    bayes_df = add_dirichlet_posterior(base, alpha=alpha)
    bayes_df["confidence"] = bayes_df["observed_cases"].map(confidence_label)
    st.dataframe(_format_decision_table(bayes_df), use_container_width=True, hide_index=True)

def render_quality_notes(availability: dict, filtered_events: pd.DataFrame) -> None:
    start_section("Qualidade do Recorte", "")

    if not availability["three_sixty_available"]:
        st.warning("Os dados `three-sixty` nao estao completos. O dashboard continua funcionando apenas com eventos.")
    else:
        st.success("Pastas `three-sixty` detectadas. O app segue compativel mesmo sem utiliza-las diretamente.")

    if filtered_events.empty:
        st.warning("Os filtros atuais nao retornaram eventos. Ajuste os filtros para continuar a analise.")
        return

    frame = add_possession_value_deltas(filtered_events)
    shots = frame[frame["is_shot"]]
    relevant = frame[frame["action_type"].isin(["Pass", "Carry", "Dribble", "Shot", "Ball Recovery", "Interception"])]
    possessions = frame["possession_sequence_id"].nunique() if "possession_sequence_id" in frame.columns else 0
    games = frame["match_id"].nunique()
    sparse_contexts = (
        frame.groupby(["action_type", "zone"]).size().reset_index(name="eventos").query("eventos < 30")
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Jogos", games)
    c2.metric("Eventos", f"{len(frame):,}".replace(",", "."))
    c3.metric("Finalizacoes", len(shots))
    c4.metric("Acoes relevantes", len(relevant))
    c5.metric("Posses", possessions)

    warnings = []
    if games < 2:
        warnings.append("Recorte curto: um jogo pode pesar demais.")
    if len(shots) < 10:
        warnings.append("Poucos chutes: xG fica instavel.")
    elif len(shots) < 30:
        warnings.append("Amostra de chutes pequena. Leia xG com cautela.")
    if len(relevant) < 30:
        warnings.append("Poucas acoes relevantes. Evite ranking forte.")
    if not sparse_contexts.empty:
        warnings.append(f"{len(sparse_contexts)} contextos acao-zona têm baixa amostra.")

    if warnings:
        for item in warnings:
            st.warning(item)
    else:
        st.success("Recorte com volume razoavel para leitura exploratoria.")

    with st.expander("Contextos com baixa amostra"):
        if sparse_contexts.empty:
            st.info("Nenhum contexto acao-zona abaixo de 30 eventos.")
        else:
            sparse_display = translate_actions(sparse_contexts.sort_values("eventos").head(100), ["action_type"])
            st.dataframe(
                sparse_display.rename(columns={"action_type": "acao", "zone": "zona"}),
                use_container_width=True,
                hide_index=True,
            )


def _cockpit_summary(events: pd.DataFrame) -> dict:
    if events.empty:
        return {
            "events": 0,
            "shots": 0,
            "xg": 0.0,
            "xg_per_shot": 0.0,
            "threat_total": 0.0,
            "threat_avg": 0.0,
            "high_value_actions": 0,
            "final_third_actions": 0,
            "box_entries": 0,
            "recovery_shot_rate": 0.0,
        }
    frame = add_possession_value_deltas(events)
    shots = frame[frame["is_shot"]]
    recoveries = frame[frame["action_type"].isin(["Ball Recovery", "Interception"])]
    xg = float(pd.to_numeric(shots.get("shot_xg", 0.0), errors="coerce").fillna(0.0).sum())
    delta_xt = pd.to_numeric(frame.get("delta_xt", 0.0), errors="coerce").fillna(0.0)
    positive_delta = delta_xt.clip(lower=0.0)
    return {
        "events": int(len(frame)),
        "shots": int(len(shots)),
        "xg": xg,
        "xg_per_shot": xg / len(shots) if len(shots) else 0.0,
        "threat_total": float(positive_delta.sum()),
        "threat_avg": float(delta_xt.mean()) if len(delta_xt) else 0.0,
        "high_value_actions": int((delta_xt >= 0.025).sum()),
        "final_third_actions": int(frame["field_third"].eq("Ataque").sum()),
        "box_entries": int(frame["box_entry"].sum()),
        "recovery_shot_rate": float(recoveries["future_shot"].mean()) if not recoveries.empty else 0.0,
    }


def render_cockpit_header(context: dict, filtered_events: pd.DataFrame, filtered_matches: pd.DataFrame) -> None:
    st.markdown(f"## {context_title(context, filtered_matches)}")
    meta = [
        context.get("mode", ""),
        context.get("preset", ""),
        f"{len(filtered_events):,} eventos".replace(",", "."),
        f"{filtered_matches['match_id'].nunique() if not filtered_matches.empty else 0} jogos",
    ]
    st.caption(" | ".join([item for item in meta if item]))


def render_cockpit_cards(events: pd.DataFrame, context: dict) -> None:
    if context.get("mode") == "Comparar duas selecoes" and context.get("team_a") and context.get("team_b"):
        team_a = context["team_a"]
        team_b = context["team_b"]
        summary_a = _cockpit_summary(events[events["team_name"] == team_a])
        summary_b = _cockpit_summary(events[events["team_name"] == team_b])
        cards = [
            ("xG", "xg", "decimal2"),
            ("Finalizações", "shots", "int"),
            ("Ameaça total", "threat_total", "decimal2"),
            ("Ameaça média", "threat_avg", "signed4"),
            ("Ações alto valor", "high_value_actions", "int"),
            ("Entradas na área", "box_entries", "int"),
        ]
        metric_cards = []
        for label, key, fmt in cards:
            a_value = summary_a[key]
            b_value = summary_b[key]
            leader = team_a if a_value >= b_value else team_b
            metric_cards.append(
                {
                    "label": label,
                    "value": f"{team_label(team_a)} {_format_number(a_value, fmt)} | {team_label(team_b)} {_format_number(b_value, fmt)}",
                    "subtitle": f"Lidera: {team_label(leader)}",
                    "leader": True,
                }
            )
        render_metric_grid(metric_cards)
        return

    summary = _cockpit_summary(events)
    render_metric_grid(
        [
            {"label": "Eventos", "value": _format_number(summary["events"], "int")},
            {"label": "Finalizações", "value": _format_number(summary["shots"], "int")},
            {"label": "xG", "value": _format_number(summary["xg"])},
            {"label": "Ameaça total", "value": _format_number(summary["threat_total"])},
            {"label": "Ameaça média", "value": _format_number(summary["threat_avg"], "signed4")},
            {"label": "Ações de alto valor", "value": _format_number(summary["high_value_actions"], "int")},
            {"label": "Entradas na área", "value": _format_number(summary["box_entries"], "int")},
        ]
    )


def render_cockpit_tabs(
    events: pd.DataFrame,
    matches: pd.DataFrame,
    availability: dict,
    context: dict,
    all_events: pd.DataFrame,
) -> None:
    tab_names = ordered_tabs_for_preset(context.get("preset", ""), context.get("mode", ""))
    tabs = st.tabs(tab_names)
    tab_map = dict(zip(tab_names, tabs))

    with tab_map["Resumo"]:
        render_summary_page(events, matches)
    with tab_map["Territorio"]:
        render_map_territory_page(events)
    with tab_map["Progressao"]:
        render_field_thirds(events, key_prefix="progression")
        with st.expander("Mapa territorial"):
            render_action_maps(events, key_prefix="progression")
    with tab_map["Ameaca"]:
        render_offensive_danger_page(events)
    with tab_map["Caminhos"]:
        render_sequences_page(events)
    with tab_map["Jogadores"]:
        render_compare_players(events, key_prefix="players_tab")
    with tab_map["Comparacao"]:
        if context.get("mode") == "Comparacao visual":
            render_visual_comparison_page(events, context)
        elif context.get("mode") == "Comparar jogadores":
            render_compare_players(events, key_prefix="comparison_players_tab")
        else:
            render_compare_teams(events, key_prefix="comparison_teams_tab")
    with tab_map["Confiabilidade"]:
        render_models_validation_page(all_events, availability, events)
    with tab_map["Metodologia"]:
        render_methodology_page()


def main() -> None:
    export_mode = _is_export_mode()
    _inject_theme_compat(export_mode=export_mode)
    render_hero()
    if export_mode:
        st.caption("Modo PDF ativo: filtros e sidebar ficam reduzidos para impressão.")

    availability = check_data_availability(DATA_DIR)
    matches = get_matches()

    if matches.empty:
        st.error("Nao foi possivel carregar dados locais suficientes. Verifique as pastas `matches/` e `events/`.")
        return

    context = render_context_shell(matches)
    selected_years = context.get("years", tuple())
    if not selected_years:
        st.warning("Selecione pelo menos um ano para carregar os eventos.")
        return

    events = enrich_events(get_events(selected_years), matches)
    if events.empty:
        st.error("Nao foi possivel carregar eventos para os anos selecionados. Verifique a pasta `events/`.")
        return

    filtered_events, context = render_analysis_context_filters(events, matches, context)
    filtered_matches = matches[matches["match_id"].isin(filtered_events["match_id"].unique())]

    if export_mode or context.get("mode") == "Comparacao visual":
        render_pdf_generator()

    render_cockpit_header(context, filtered_events, filtered_matches)
    if filtered_events.empty:
        st.warning("Os filtros atuais nao retornaram eventos.")
        return
    render_cockpit_cards(filtered_events, context)
    render_cockpit_tabs(filtered_events, filtered_matches, availability, context, events)


if __name__ == "__main__":
    main()
