from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.context import ANALYSIS_MODES, ANALYSIS_PRESETS
from src.labels import action_label, team_label
from src.preprocess import FIELD_ZONES, MATCH_STATE_ORDER, TIME_BUCKET_ORDER, filter_events
from src.possession_value import ACTION_FAMILY_ORDER, action_family


ANALYTIC_PAGES = [
    "Resumo",
    "Mapa e Territorio",
    "Sequencias e Transicoes",
    "Perigo Ofensivo",
    "Comparar Equipes",
    "Comparar Jogadores",
    "Confiabilidade",
    "Notas Metodologicas",
]


def format_match_label_pt(row: pd.Series) -> str:
    date_label = row["match_date"].strftime("%Y-%m-%d") if pd.notna(row["match_date"]) else "Data desconhecida"
    return (
        f"{row['year']} | {team_label(row['home_team'])} {row['home_score']}-"
        f"{row['away_score']} {team_label(row['away_team'])} | {date_label}"
    )


def render_page_and_year_filters(matches: pd.DataFrame) -> tuple[str, tuple[int, ...]]:
    st.sidebar.markdown("## Menu")
    page = st.sidebar.radio(
        "Navegacao",
        options=ANALYTIC_PAGES,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("## Filtros")
    available_years = sorted(matches["year"].dropna().unique().tolist())
    default_years = [max(available_years)] if available_years else []
    if page in {"Confiabilidade"}:
        default_years = available_years
    selected_years = st.sidebar.multiselect("Ano", options=available_years, default=default_years)
    return page, tuple(selected_years)


def _situation_label(row: pd.Series) -> str:
    pattern = str(row.get("play_pattern", ""))
    action = str(row.get("action_type", ""))
    if pattern in {"From Corner", "From Free Kick", "From Throw In"}:
        return "Bola parada"
    if action in {"Ball Recovery", "Interception", "Pressure", "Duel", "Block"}:
        return "Defesa"
    if pattern in {"From Counter"}:
        return "Transicao"
    return "Ataque"


def _match_options(matches: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    return (
        matches[matches["match_id"].isin(events["match_id"].unique())]
        .assign(match_label=lambda df: df.apply(format_match_label_pt, axis=1))
        .sort_values(["year", "match_date", "match_id"])
    )


def render_context_shell(matches: pd.DataFrame) -> dict:
    st.sidebar.markdown("## Contexto da Analise")
    mode = st.sidebar.selectbox("Modo de analise", ANALYSIS_MODES, index=0)
    preset = st.sidebar.selectbox("Preset", ANALYSIS_PRESETS, index=0)
    st.sidebar.markdown("**Competicao:** Copa do Mundo")

    available_years = sorted(matches["year"].dropna().unique().tolist())
    default_years = [max(available_years)] if available_years else []
    if mode == "Explorar torneio inteiro":
        default_years = available_years
    years = st.sidebar.multiselect("Ano", options=available_years, default=default_years)
    return {"mode": mode, "preset": preset, "years": tuple(years)}


def render_analysis_context_filters(
    events: pd.DataFrame,
    matches: pd.DataFrame,
    context: dict,
) -> tuple[pd.DataFrame, dict]:
    filtered = filter_events(events, years=context.get("years"))
    context = dict(context)

    if filtered.empty:
        st.sidebar.warning("Sem eventos para o ano selecionado.")
        return filtered.copy(), context

    teams = sorted(filtered["team_name"].dropna().unique().tolist())
    mode = context["mode"]

    primary_team = None
    team_a = None
    team_b = None
    opponent = None
    match_id = None

    if mode == "Explorar torneio inteiro":
        st.sidebar.caption("Recorte agregado do torneio.")
    elif mode == "Comparacao visual":
        visual_type = st.sidebar.radio("Tipo de comparacao", ["Jogadores", "Selecoes"], horizontal=True)
        context["visual_type"] = visual_type
        if visual_type == "Selecoes":
            team_a = st.sidebar.selectbox("Selecao A", teams, index=0, format_func=team_label, key="visual_team_a")
            b_options = [team for team in teams if team != team_a] or teams
            team_b = st.sidebar.selectbox("Selecao B", b_options, index=0, format_func=team_label, key="visual_team_b")
            filtered = filtered[filtered["team_name"].isin([team_a, team_b])]
        else:
            primary_team = st.sidebar.selectbox("Selecao", teams, index=0, format_func=team_label, key="visual_players_team")
            filtered = filtered[filtered["team_name"] == primary_team]
    elif mode == "Comparar duas selecoes":
        team_a = st.sidebar.selectbox("Selecao A", teams, index=0, format_func=team_label)
        b_options = [team for team in teams if team != team_a] or teams
        team_b = st.sidebar.selectbox("Selecao B", b_options, index=0, format_func=team_label)
        filtered = filtered[filtered["team_name"].isin([team_a, team_b])]
    elif mode == "Analisar uma partida":
        match_options = _match_options(matches, filtered)
        labels = match_options["match_label"].tolist()
        selected_label = st.sidebar.selectbox("Partida", labels)
        match_id = match_options.loc[match_options["match_label"] == selected_label, "match_id"].iloc[0]
        filtered = filtered[filtered["match_id"] == match_id]
        match_row = match_options[match_options["match_id"] == match_id].iloc[0]
        team_a = match_row["home_team"]
        team_b = match_row["away_team"]
        primary_team = team_a
        st.sidebar.caption(f"Equipes: {team_label(team_a)} x {team_label(team_b)}")
    else:
        primary_team = st.sidebar.selectbox("Selecao principal", teams, index=0, format_func=team_label)
        team_matches = matches[
            matches["match_id"].isin(filtered.loc[filtered["team_name"] == primary_team, "match_id"].unique())
        ]
        opponents = sorted(
            set(team_matches["home_team"].tolist() + team_matches["away_team"].tolist()) - {primary_team}
        )
        opponent_options = ["Todos"] + opponents
        opponent = st.sidebar.selectbox("Adversario", opponent_options, format_func=team_label)
        candidate_match_ids = team_matches["match_id"].tolist()
        if opponent != "Todos":
            candidate_match_ids = team_matches[
                (team_matches["home_team"].eq(opponent)) | (team_matches["away_team"].eq(opponent))
            ]["match_id"].tolist()
        match_options = (
            matches[matches["match_id"].isin(candidate_match_ids)]
            .assign(match_label=lambda df: df.apply(format_match_label_pt, axis=1))
            .sort_values(["year", "match_date", "match_id"])
        )
        match_labels = ["Todos os jogos"] + match_options["match_label"].tolist()
        selected_match = st.sidebar.selectbox("Partida", match_labels)
        if selected_match != "Todos os jogos":
            match_id = match_options.loc[match_options["match_label"] == selected_match, "match_id"].iloc[0]
        filtered = filtered[filtered["team_name"] == primary_team]
        if opponent != "Todos":
            filtered = filtered[filtered["match_id"].isin(candidate_match_ids)]
        if match_id:
            filtered = filtered[filtered["match_id"] == match_id]

    st.sidebar.markdown("## Filtros rapidos")
    period_labels = sorted(filtered["period_label"].dropna().unique().tolist())
    selected_periods = st.sidebar.multiselect("Periodo", options=period_labels, default=period_labels)
    filtered = filter_events(filtered, period_labels=selected_periods)

    selected_players: list[str] = []
    players = sorted(filtered["player_name"].dropna().unique().tolist())
    if players:
        if mode in {"Comparar jogadores", "Comparacao visual"} and context.get("visual_type") != "Selecoes":
            selected_players = st.sidebar.multiselect("Jogadores", players, default=players[:2])
        else:
            selected_players = st.sidebar.multiselect("Jogador", players, default=[])
        if selected_players:
            filtered = filtered[filtered["player_name"].isin(selected_players)]

    action_types = sorted(filtered["action_type"].dropna().unique().tolist())
    selected_actions = st.sidebar.multiselect("Tipo de acao", action_types, default=action_types, format_func=action_label)
    filtered = filter_events(filtered, action_types=selected_actions)

    if not filtered.empty:
        families = filtered.apply(lambda row: action_family(row.get("action_type"), row.get("play_pattern")), axis=1)
        filtered = filtered.assign(action_family=families)
        family_options = [family for family in ACTION_FAMILY_ORDER if family in filtered["action_family"].unique()]
        selected_families = st.sidebar.multiselect("Familia de acao", family_options, default=family_options)
        if selected_families:
            filtered = filtered[filtered["action_family"].isin(selected_families)]

    with st.sidebar.expander("Filtros avancados"):
        zones = [zone for zone in FIELD_ZONES.keys() if zone in filtered["zone"].dropna().unique()]
        selected_zones = st.multiselect("Zona do campo", zones, default=zones)
        filtered = filter_events(filtered, zones=selected_zones)

        if not filtered.empty:
            situations = filtered.apply(_situation_label, axis=1)
            filtered = filtered.assign(situation=situations)
            selected_situations = st.multiselect("Situacao", sorted(filtered["situation"].unique()), default=sorted(filtered["situation"].unique()))
            filtered = filtered[filtered["situation"].isin(selected_situations)]

        max_remaining = int(np.ceil(filtered["minutes_remaining"].max())) if not filtered.empty else 1
        remaining_range = st.slider("Minutos restantes", 0, max(max_remaining, 1), (0, max(max_remaining, 1)))
        filtered = filtered[
            filtered["minutes_remaining"].fillna(0).between(remaining_range[0], remaining_range[1], inclusive="both")
        ]

        match_states = [state for state in MATCH_STATE_ORDER if state in filtered.get("match_state", pd.Series(dtype=str)).astype(str).unique()]
        if match_states:
            selected_match_states = st.multiselect("Momento do time", match_states, default=match_states)
            filtered = filtered[filtered["match_state"].astype(str).isin(selected_match_states)]

    context.update(
        {
            "primary_team": primary_team,
            "team_a": team_a,
            "team_b": team_b,
            "opponent": opponent,
            "match_id": match_id,
            "periods": selected_periods,
            "players": selected_players,
        }
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Filtros avancados ficam recolhidos para reduzir ruido.")
    return filtered.copy(), context


def render_event_filters(events: pd.DataFrame, matches: pd.DataFrame, selected_years: tuple[int, ...]) -> pd.DataFrame:
    filtered = filter_events(events, years=selected_years)

    teams = sorted(filtered["team_name"].dropna().unique().tolist())
    all_teams = st.sidebar.checkbox("Todas as selecoes", value=True)
    if not all_teams:
        selected_teams = st.sidebar.multiselect("Selecao / time", options=teams, default=teams, format_func=team_label)
        filtered = filter_events(filtered, teams=selected_teams)

    match_options = (
        matches[matches["match_id"].isin(filtered["match_id"].unique())]
        .assign(match_label=lambda df: df.apply(format_match_label_pt, axis=1))
        .sort_values(["year", "match_date", "match_id"])
    )
    match_labels = match_options["match_label"].tolist()
    all_matches = st.sidebar.checkbox("Todos os jogos", value=True)
    if not all_matches:
        selected_match_labels = st.sidebar.multiselect("Jogo", options=match_labels, default=match_labels)
        selected_match_ids = match_options.loc[
            match_options["match_label"].isin(selected_match_labels), "match_id"
        ].tolist()
        filtered = filter_events(filtered, match_ids=selected_match_ids)

    action_types = sorted(filtered["action_type"].dropna().unique().tolist())
    all_actions = st.sidebar.checkbox("Todos os tipos de acao", value=True)
    if not all_actions:
        selected_actions = st.sidebar.multiselect(
            "Tipo de acao",
            options=action_types,
            default=action_types,
            format_func=action_label,
        )
        filtered = filter_events(filtered, action_types=selected_actions)

    period_labels = sorted(filtered["period_label"].dropna().unique().tolist())
    selected_periods = st.sidebar.multiselect("Periodo do jogo", options=period_labels, default=period_labels)
    filtered = filter_events(filtered, period_labels=selected_periods)

    match_states = [state for state in MATCH_STATE_ORDER if state in filtered["match_state"].astype(str).unique()]
    selected_match_states = st.sidebar.multiselect("Momento do time", options=match_states, default=match_states)
    if selected_match_states:
        filtered = filtered[filtered["match_state"].astype(str).isin(selected_match_states)]

    zones = list(FIELD_ZONES.keys())
    selected_zones = st.sidebar.multiselect("Zona do campo", options=zones, default=zones)
    filtered = filter_events(filtered, zones=selected_zones)

    time_buckets = [bucket for bucket in TIME_BUCKET_ORDER if bucket in filtered["time_remaining_bucket"].astype(str).unique()]
    selected_time_buckets = st.sidebar.multiselect(
        "Faixa de tempo restante",
        options=time_buckets,
        default=time_buckets,
    )
    if selected_time_buckets:
        filtered = filtered[filtered["time_remaining_bucket"].astype(str).isin(selected_time_buckets)]

    max_remaining = int(np.ceil(filtered["minutes_remaining"].max())) if not filtered.empty else 0
    slider_max = max(max_remaining, 1)
    remaining_range = st.sidebar.slider(
        "Minutos restantes no jogo",
        min_value=0,
        max_value=slider_max,
        value=(0, slider_max),
    )
    filtered = filtered[
        filtered["minutes_remaining"].fillna(0).between(remaining_range[0], remaining_range[1], inclusive="both")
    ]

    possession_choices = ["Todos"] + sorted(filtered["possession_team_name"].dropna().unique().tolist())
    selected_possession_team = st.sidebar.selectbox("Time da posse", options=possession_choices, format_func=team_label)
    if selected_possession_team != "Todos":
        filtered = filtered[filtered["possession_team_name"] == selected_possession_team]

    st.sidebar.markdown("---")
    st.sidebar.caption("Filtros globais aplicados ao recorte atual.")
    return filtered.copy()
