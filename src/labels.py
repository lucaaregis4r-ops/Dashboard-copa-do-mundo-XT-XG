from __future__ import annotations

import pandas as pd


ACTION_LABELS_PT = {
    "50/50": "Disputa 50/50",
    "Ball Receipt*": "Recepção de bola",
    "Ball Recovery": "Recuperação de bola",
    "Block": "Bloqueio",
    "Carry": "Condução",
    "Clearance": "Corte",
    "Dispossessed": "Desarmado",
    "Dribble": "Drible",
    "Dribbled Past": "Driblado",
    "Duel": "Duelo",
    "Error": "Erro",
    "Foul Committed": "Falta cometida",
    "Foul Won": "Falta sofrida",
    "Goal Keeper": "Goleiro",
    "Half End": "Fim do tempo",
    "Half Start": "Início do tempo",
    "Injury Stoppage": "Parada por lesão",
    "Interception": "Interceptação",
    "Miscontrol": "Domínio errado",
    "Own Goal Against": "Gol contra sofrido",
    "Own Goal For": "Gol contra a favor",
    "Pass": "Passe",
    "Player Off": "Jogador saiu",
    "Player On": "Jogador entrou",
    "Pressure": "Pressão",
    "Referee Ball-Drop": "Bola ao chão",
    "Shield": "Proteção",
    "Shot": "Finalização",
    "Starting XI": "Escalação inicial",
    "Substitution": "Substituição",
    "Tactical Shift": "Mudança tática",
    "Unknown": "Desconhecido",
}

COUNTRY_LABELS_PT = {
    "Argentina": "Argentina",
    "Australia": "Austrália",
    "Belgium": "Bélgica",
    "Brazil": "Brasil",
    "Cameroon": "Camarões",
    "Canada": "Canadá",
    "Colombia": "Colombia",
    "Costa Rica": "Costa Rica",
    "Croatia": "Croácia",
    "Denmark": "Dinamarca",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Ghana": "Gana",
    "Iceland": "Islândia",
    "Iran": "Irã",
    "Japan": "Japão",
    "Mexico": "México",
    "Morocco": "Marrocos",
    "Netherlands": "Holanda",
    "Nigeria": "Nigeria",
    "Panama": "Panamá",
    "Peru": "Peru",
    "Poland": "Polonia",
    "Portugal": "Portugal",
    "Qatar": "Catar",
    "Russia": "Russia",
    "Saudi Arabia": "Arábia Saudita",
    "Senegal": "Senegal",
    "Serbia": "Sérvia",
    "South Korea": "Coreia do Sul",
    "Spain": "Espanha",
    "Sweden": "Suecia",
    "Switzerland": "Suíça",
    "Tunisia": "Tunisia",
    "United States": "Estados Unidos",
    "Uruguay": "Uruguai",
    "Wales": "Pais de Gales",
    "Unknown": "Desconhecido",
}

COUNTRY_FLAG_CODES = {
    "Argentina": "AR",
    "Australia": "AU",
    "Belgium": "BE",
    "Brazil": "BR",
    "Cameroon": "CM",
    "Canada": "CA",
    "Colombia": "CO",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Denmark": "DK",
    "Ecuador": "EC",
    "Egypt": "EG",
    "England": "GB",
    "France": "FR",
    "Germany": "DE",
    "Ghana": "GH",
    "Iceland": "IS",
    "Iran": "IR",
    "Japan": "JP",
    "Mexico": "MX",
    "Morocco": "MA",
    "Netherlands": "NL",
    "Nigeria": "NG",
    "Panama": "PA",
    "Peru": "PE",
    "Poland": "PL",
    "Portugal": "PT",
    "Qatar": "QA",
    "Russia": "RU",
    "Saudi Arabia": "SA",
    "Senegal": "SN",
    "Serbia": "RS",
    "South Korea": "KR",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Tunisia": "TN",
    "United States": "US",
    "Uruguay": "UY",
    "Wales": "GB",
}

METRIC_LABELS_PT = {
    "total_actions": "Total de ações",
    "passes": "Passes",
    "shots": "Finalizações",
    "carries": "Conduções",
    "pressures": "Pressões",
    "recoveries": "Recuperações",
    "xg": "xG",
    "under_pressure_rate": "Sob pressão",
    "attacking_zone_rate": "Taxa em zona de ataque",
    "avg_actions_per_match": "Ações por jogo",
    "matches": "Jogos",
    "action_variety": "Variedade de ações",
    "goals": "Gols",
    "assists": "Assistências",
    "events": "Eventos",
    "threat_added": "Ameaça adicionada",
    "progressive_events": "Ações progressivas",
    "delta_xt_total": "Delta xT total",
    "delta_xt_mean": "Delta xT médio",
    "delta_valor_posse_mean": "Mudança média valor posse",
    "future_xg_associated": "xG futuro associado",
    "future_shot_rate": "Chance de chute futuro",
    "final_third_entries": "Entradas no terço final",
    "box_entries": "Entradas na área",
    "shots": "Finalizações",
    "xg_per_shot": "xG por finalização",
    "attacking_zone_rate": "Taxa em zona de ataque",
}


ACTION_COLORS = {
    "Shot": "#f97316",
    "Pass": "#2563eb",
    "Carry": "#059669",
    "Dribble": "#7c3aed",
    "Ball Receipt*": "#eab308",
    "Ball Receipt": "#eab308",
    "Pressure": "#374151",
    "Ball Recovery": "#65a30d",
    "Interception": "#0f766e",
    "Duel": "#64748b",
    "Block": "#0891b2",
    "Clearance": "#0369a1",
    "Foul Won": "#ec4899",
    "Foul Committed": "#991b1b",
    "Dispossessed": "#dc2626",
    "Miscontrol": "#b45309",
    "Error": "#7f1d1d",
    "Offside": "#9f1239",
    "Goal Keeper": "#475569",
    "Unknown": "#9ca3af",
}

ACTION_GROUPS = {
    "Pass": "Criação ofensiva",
    "Ball Receipt*": "Criação ofensiva",
    "Ball Receipt": "Criação ofensiva",
    "Carry": "Progressão com bola",
    "Dribble": "Progressão com bola",
    "Shot": "Finalização",
    "Pressure": "Recuperação / defesa",
    "Ball Recovery": "Recuperação / defesa",
    "Interception": "Recuperação / defesa",
    "Block": "Recuperação / defesa",
    "Clearance": "Recuperação / defesa",
    "Goal Keeper": "Recuperação / defesa",
    "Duel": "Disputas / duelos",
    "50/50": "Disputas / duelos",
    "Dispossessed": "Erros / perdas",
    "Miscontrol": "Erros / perdas",
    "Error": "Erros / perdas",
    "Offside": "Erros / perdas",
    "Foul Committed": "Erros / perdas",
    "Foul Won": "Bola parada / faltas",
}

ACTION_GROUP_COLORS = {
    "Criação ofensiva": "#2563eb",
    "Progressão com bola": "#059669",
    "Finalização": "#f97316",
    "Recuperação / defesa": "#0f766e",
    "Disputas / duelos": "#64748b",
    "Erros / perdas": "#dc2626",
    "Bola parada / faltas": "#ec4899",
    "Outros": "#9ca3af",
}

ACTION_ICONS = {
    "Shot": "Alvo",
    "Pass": "Seta",
    "Carry": "Bola",
    "Dribble": "Zigue",
    "Ball Receipt*": "Recepção",
    "Ball Receipt": "Recepção",
    "Pressure": "Pressão",
    "Ball Recovery": "Recuperação",
    "Interception": "Corte",
    "Duel": "Duelo",
    "Block": "Bloqueio",
    "Clearance": "Corte",
}

KEY_ACTION_ORDER = ["Shot", "Pass", "Carry", "Dribble", "Ball Receipt*", "Ball Recovery", "Pressure"]


def action_label(value: object) -> str:
    return ACTION_LABELS_PT.get(str(value), str(value))


def action_group(value: object) -> str:
    raw = str(value)
    if raw in ACTION_GROUPS:
        return ACTION_GROUPS[raw]
    reverse = {label: action for action, label in ACTION_LABELS_PT.items()}
    return ACTION_GROUPS.get(reverse.get(raw, raw), "Outros")


def action_color(value: object) -> str:
    raw = str(value)
    if raw in ACTION_COLORS:
        return ACTION_COLORS[raw]
    reverse = {label: action for action, label in ACTION_LABELS_PT.items()}
    return ACTION_COLORS.get(reverse.get(raw, raw), "#9ca3af")


def action_group_color(value: object) -> str:
    return ACTION_GROUP_COLORS.get(str(value), "#9ca3af")


def action_icon_label(value: object) -> str:
    raw = str(value)
    reverse = {label: action for action, label in ACTION_LABELS_PT.items()}
    action = raw if raw in ACTION_LABELS_PT else reverse.get(raw, raw)
    icon = ACTION_ICONS.get(action)
    label = action_label(action)
    return f"{icon} - {label}" if icon else label


def team_label(value: object) -> str:
    raw = str(value)
    label = COUNTRY_LABELS_PT.get(raw, raw)
    code = COUNTRY_FLAG_CODES.get(raw)
    if not code:
        return label
    flag = "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in code.upper())
    return f"{flag} {label}"


def translate_actions(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    result = frame.copy()
    for column in columns or ["action_type", "current_action", "previous_action", "next_action"]:
        if column in result.columns:
            result[column] = result[column].map(action_label)
    return result


def translate_teams(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    result = frame.copy()
    for column in columns or ["team_name", "possession_team_name", "home_team", "away_team", "selection"]:
        if column in result.columns:
            result[column] = result[column].map(team_label)
    return result


def translate_metrics(frame: pd.DataFrame, metric_col: str = "metric") -> pd.DataFrame:
    result = frame.copy()
    if metric_col in result.columns:
        result[metric_col] = result[metric_col].map(lambda value: METRIC_LABELS_PT.get(str(value), str(value)))
    return result
