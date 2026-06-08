from __future__ import annotations

import pandas as pd

from src.labels import action_label, team_label


SMALL_SAMPLE_THRESHOLD = 30
VERY_SMALL_SAMPLE_THRESHOLD = 10


def sample_alert(count: int, context: str = "contexto") -> str | None:
    if count < VERY_SMALL_SAMPLE_THRESHOLD:
        return f"Amostra muito pequena para este {context}: {count} eventos. Nao use como insight principal."
    if count < SMALL_SAMPLE_THRESHOLD:
        return f"Amostra pequena para este {context}: {count} eventos. Leia com cautela."
    return None


def _value(frame: pd.DataFrame, entity_col: str, entity: str, metric: str) -> float:
    if frame.empty or metric not in frame.columns:
        return 0.0
    value = frame.loc[frame[entity_col] == entity, metric]
    if value.empty or pd.isna(value.iloc[0]):
        return 0.0
    return float(value.iloc[0])


def generate_summary_narrative(events: pd.DataFrame) -> str:
    if events.empty:
        return "Sem eventos suficientes neste recorte."

    teams = events["team_name"].nunique()
    actions = len(events)
    xg = pd.to_numeric(events["shot_xg"], errors="coerce").sum(min_count=1)
    xg_text = "sem xG detectado" if pd.isna(xg) else f"xG {xg:.2f}"
    return f"{actions:,} eventos, {teams} selecoes, {xg_text}.".replace(",", ".")


def generate_markov_narrative(rankings: pd.DataFrame, current_action: str | None = None) -> str:
    if rankings.empty:
        return "Sem sequencias suficientes neste contexto."

    top = rankings.iloc[0]
    action = action_label(current_action) if current_action else "este contexto"
    return (
        f"Depois de {action}: {action_label(top['next_action'])} "
        f"({top['probability']:.1%})."
    )


def generate_threat_narrative(team_summary: pd.DataFrame) -> str:
    if team_summary.empty:
        return "Sem eventos suficientes para estimar ameaca."

    metric = "delta_xt_total" if "delta_xt_total" in team_summary.columns else "ameaca_adicionada"
    label = "delta_xT" if metric == "delta_xt_total" else "ameaca"
    top = team_summary.sort_values(metric, ascending=False).iloc[0]
    team = top.get("team_name", "Equipe")
    return f"{team_label(team)} lidera em {label} no recorte ({float(top.get(metric, 0.0)):.2f})."


def zone_transition_reading(rankings: pd.DataFrame, current_action: str, zone: str) -> str:
    if rankings.empty:
        return "Sem sequencias suficientes para esta acao e zona."

    top = rankings.iloc[0]
    xg_delta = top.get("xg_delta_medio")
    xg_text = ""
    if pd.notna(xg_delta):
        xg_text = f" Variacao xG evento seguinte: {float(xg_delta):+.3f}."
    return (
        f"{zone}, depois de {action_label(current_action)}: "
        f"{action_label(top['next_action'])} ({top['probability']:.1%}).{xg_text}"
    )


def second_order_reading(rankings: pd.DataFrame, previous_action: str, current_action: str) -> str:
    if rankings.empty:
        return "Sem sequencias suficientes para este encadeamento."

    top = rankings.iloc[0]
    return (
        f"{action_label(previous_action)} -> {action_label(current_action)} -> "
        f"{action_label(top['next_action'])} ({top['probability']:.1%})."
    )


def offensive_danger_reading(team_summary: pd.DataFrame) -> str:
    return generate_threat_narrative(team_summary)


def generate_team_comparison_narrative(summary: pd.DataFrame, team_a: str, team_b: str) -> str:
    if summary.empty:
        return "Sem dados suficientes para comparar as equipes."

    xg_a = _value(summary, "team_name", team_a, "xg")
    xg_b = _value(summary, "team_name", team_b, "xg")
    threat_a = _value(summary, "team_name", team_a, "delta_xt_total")
    threat_b = _value(summary, "team_name", team_b, "delta_xt_total")
    xg_leader = team_a if xg_a >= xg_b else team_b
    threat_leader = team_a if threat_a >= threat_b else team_b
    return (
        f"{team_label(xg_leader)} tem mais xG no recorte. "
        f"{team_label(threat_leader)} aparece melhor em valor da posse. "
        "Leia junto com volume e amostra."
    )


def generate_player_comparison_narrative(summary: pd.DataFrame, player_a: str, player_b: str) -> str:
    if summary.empty:
        return f"Comparacao: {player_a} x {player_b}."

    threat_a = _value(summary, "player_name", player_a, "delta_xt_total")
    threat_b = _value(summary, "player_name", player_b, "delta_xt_total")
    future_a = _value(summary, "player_name", player_a, "future_xg_associated")
    future_b = _value(summary, "player_name", player_b, "future_xg_associated")
    threat_leader = player_a if threat_a >= threat_b else player_b
    future_leader = player_a if future_a >= future_b else player_b
    return (
        f"{threat_leader} soma mais valor da posse. "
        f"{future_leader} aparece mais antes de chances. "
        "Funcoes e minutos mudam a leitura."
    )


def generate_linkedin_caption_suggestion(title: str, visual_type: str = "comparacao") -> str:
    subject = "jogadores" if visual_type == "Jogadores" else "selecoes"
    return (
        f"Testando uma leitura de valor de posse: {title}. "
        f"A ideia nao e dizer quem e melhor, mas comparar como os {subject} participam da construcao de ameaca. "
        "Fonte: StatsBomb Open Data."
    )


def overview_reading(events: pd.DataFrame) -> str:
    return generate_summary_narrative(events)


def transition_reading(rankings: pd.DataFrame, current_action: str | None = None) -> str:
    return generate_markov_narrative(rankings, current_action)


def team_comparison_reading(summary: pd.DataFrame, team_a: str, team_b: str) -> str:
    return generate_team_comparison_narrative(summary, team_a, team_b)


def player_comparison_reading(player_a: str, player_b: str) -> str:
    return f"Comparacao: {player_a} x {player_b}."
