from __future__ import annotations

import pandas as pd

from src.labels import team_label


ANALYSIS_MODES = [
    "Analisar uma selecao",
    "Comparar duas selecoes",
    "Analisar uma partida",
    "Comparar jogadores",
    "Comparacao visual",
    "Explorar torneio inteiro",
]

ANALYSIS_PRESETS = [
    "Visao geral da selecao",
    "Pre-jogo: comparar selecoes",
    "Pos-jogo: explicar diferenca entre equipes",
    "Transicoes ofensivas",
    "Recuperacao e contra-ataque",
    "Criacao de chances",
    "Mapa territorial",
    "Jogadores-chave",
    "Robustez da analise",
]

COCKPIT_TABS = [
    "Resumo",
    "Territorio",
    "Progressao",
    "Ameaca",
    "Caminhos",
    "Jogadores",
    "Comparacao",
    "Confiabilidade",
    "Metodologia",
]

PRESET_FIRST_TAB = {
    "Visao geral da selecao": "Resumo",
    "Pre-jogo: comparar selecoes": "Comparacao",
    "Pos-jogo: explicar diferenca entre equipes": "Comparacao",
    "Transicoes ofensivas": "Caminhos",
    "Recuperacao e contra-ataque": "Caminhos",
    "Criacao de chances": "Ameaca",
    "Mapa territorial": "Territorio",
    "Jogadores-chave": "Jogadores",
    "Robustez da analise": "Confiabilidade",
}


def ordered_tabs_for_preset(preset: str, mode: str) -> list[str]:
    tabs = COCKPIT_TABS.copy()
    if mode == "Comparar jogadores":
        first = "Jogadores"
    elif mode == "Comparacao visual":
        first = "Comparacao"
    elif mode == "Comparar duas selecoes":
        first = "Comparacao"
    elif mode == "Analisar uma partida":
        first = "Resumo"
    else:
        first = PRESET_FIRST_TAB.get(preset, "Resumo")
    if first in tabs:
        tabs.remove(first)
        tabs.insert(0, first)
    return tabs


def context_title(context: dict, matches: pd.DataFrame | None = None) -> str:
    mode = context.get("mode", "")
    year_label = ", ".join(str(year) for year in context.get("years", []) or [])
    year_label = year_label or "anos selecionados"
    match_id = context.get("match_id")

    if match_id and matches is not None and not matches.empty:
        row = matches[matches["match_id"] == match_id]
        if not row.empty:
            item = row.iloc[0]
            return (
                f"{team_label(item['home_team'])} x {team_label(item['away_team'])} "
                f"- {item.get('stage', 'Partida')} - {item.get('year', year_label)}"
            )

    if mode == "Comparar duas selecoes":
        return f"Comparando: {team_label(context.get('team_a', 'Selecao A'))} vs {team_label(context.get('team_b', 'Selecao B'))} - {year_label}"
    if mode == "Comparar jogadores":
        team = context.get("primary_team")
        return f"Jogadores - {team_label(team) if team else year_label}"
    if mode == "Comparacao visual":
        if context.get("visual_type") == "Jogadores":
            players = context.get("players", [])
            if len(players) >= 2:
                return f"{players[0]} x {players[1]} - {year_label}"
            return f"Comparacao visual de jogadores - {year_label}"
        return f"Comparacao visual - {team_label(context.get('team_a', 'Selecao A'))} vs {team_label(context.get('team_b', 'Selecao B'))} - {year_label}"
    if mode == "Explorar torneio inteiro":
        return f"Copa do Mundo - {year_label}"
    team = context.get("primary_team")
    if team:
        opponent = context.get("opponent")
        if opponent and opponent != "Todos":
            return f"{team_label(team)} vs {team_label(opponent)} - {year_label}"
        return f"{team_label(team)} - Copa do Mundo {year_label}"
    return f"Recorte atual - {year_label}"
