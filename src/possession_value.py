from __future__ import annotations

import numpy as np
import pandas as pd

from src.preprocess import assign_zone


CREATION_ACTIONS = {
    "Pass",
    "Carry",
    "Dribble",
    "Ball Receipt*",
    "Ball Receipt",
    "Miscontrol",
}
SHOT_ACTIONS = {"Shot"}
DEFENSIVE_ACTIONS = {
    "Ball Recovery",
    "Interception",
    "Pressure",
    "Duel",
    "Block",
    "Clearance",
    "Dispossessed",
    "Foul Committed",
}
SET_PIECE_PATTERNS = {
    "From Corner",
    "From Free Kick",
    "From Throw In",
    "From Keeper",
}
SET_PIECE_ACTIONS = {"Foul Won", "Corner", "Free Kick"}
LOSS_ACTIONS = {
    "Dispossessed",
    "Miscontrol",
    "Foul Committed",
    "Error",
    "Bad Behaviour",
    "Offside",
}
RECOVERY_ACTIONS = {"Ball Recovery", "Interception"}
RESTART_ACTIONS = {"Half Start", "Half End", "Substitution", "Player On", "Player Off", "Tactical Shift"}
TERMINAL_STATE = "perda_posse"
PASS_COMPLETE_OUTCOMES = {"Unknown", "nan", "None", ""}
VALUE_GRID_X_BINS = 12
VALUE_GRID_Y_BINS = 8
PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0


ACTION_FAMILY_ORDER = [
    "Criacao ofensiva",
    "Finalizacao",
    "Recuperacao/defesa",
    "Bola parada",
    "Outros/contextuais",
]


def action_family(action_type: str, play_pattern: str | None = None) -> str:
    action = str(action_type)
    pattern = str(play_pattern or "")
    if action in SHOT_ACTIONS:
        return "Finalizacao"
    if action in SET_PIECE_ACTIONS or pattern in SET_PIECE_PATTERNS:
        return "Bola parada"
    if action in CREATION_ACTIONS:
        return "Criacao ofensiva"
    if action in DEFENSIVE_ACTIONS:
        return "Recuperacao/defesa"
    return "Outros/contextuais"


def _possession_key(frame: pd.DataFrame) -> pd.Series:
    if "possession" in frame.columns and frame["possession"].notna().any():
        statsbomb_key = (
            frame["match_id"].astype(str)
            + "|"
            + frame["period"].astype(str)
            + "|"
            + frame["possession"].astype(str)
            + "|"
            + frame["possession_team_name"].astype(str)
        )
        if frame["possession"].notna().all():
            return statsbomb_key
        reconstructed_key = _reconstruct_possession_key(frame)
        return statsbomb_key.where(frame["possession"].notna(), reconstructed_key)

    return _reconstruct_possession_key(frame)


def _possession_source(frame: pd.DataFrame) -> pd.Series:
    if "possession" not in frame.columns or not frame["possession"].notna().any():
        return pd.Series("reconstruida", index=frame.index)
    if frame["possession"].notna().all():
        return pd.Series("statsbomb", index=frame.index)
    return pd.Series(np.where(frame["possession"].notna(), "statsbomb", "reconstruida"), index=frame.index)


def _is_complete_pass(pass_outcome: pd.Series) -> pd.Series:
    return pass_outcome.astype(str).isin(PASS_COMPLETE_OUTCOMES)


def assign_value_state(x: float, y: float) -> str:
    if pd.isna(x) or pd.isna(y):
        return "Unknown"

    x_value = min(max(float(x), 0.0), PITCH_LENGTH)
    y_value = min(max(float(y), 0.0), PITCH_WIDTH)
    x_bin = min(int(x_value / (PITCH_LENGTH / VALUE_GRID_X_BINS)), VALUE_GRID_X_BINS - 1)
    y_bin = min(int(y_value / (PITCH_WIDTH / VALUE_GRID_Y_BINS)), VALUE_GRID_Y_BINS - 1)
    return f"x{x_bin + 1:02d}_y{y_bin + 1:02d}"


def _reconstruct_possession_key(frame: pd.DataFrame) -> pd.Series:
    sequence_ids: list[str] = []
    current_id = 0
    previous_match = None
    previous_period = None
    previous_team = None
    previous_action = None
    previous_pass_outcome = None

    for row in frame.itertuples(index=False):
        match_id = getattr(row, "match_id", None)
        period = getattr(row, "period", None)
        possession_team = getattr(row, "possession_team_name", None)
        event_team = getattr(row, "team_name", None)
        team = possession_team if possession_team and possession_team != "Unknown" else event_team
        action = str(getattr(row, "action_type", ""))
        pass_outcome = str(getattr(row, "pass_outcome", ""))
        incomplete_pass = action == "Pass" and pass_outcome not in PASS_COMPLETE_OUTCOMES
        new_sequence = False

        if previous_match is None or match_id != previous_match or period != previous_period:
            new_sequence = True
        elif team != previous_team:
            new_sequence = True
        elif action in RECOVERY_ACTIONS:
            new_sequence = True
        elif previous_action in LOSS_ACTIONS | RESTART_ACTIONS | {"Shot", "Goal Keeper"}:
            new_sequence = True
        elif previous_action == "Pass" and previous_pass_outcome not in PASS_COMPLETE_OUTCOMES:
            new_sequence = True
        elif incomplete_pass:
            new_sequence = False

        if new_sequence:
            current_id += 1

        sequence_ids.append(f"{match_id}|{period}|reconstruida|{current_id}|{team}")
        previous_match = match_id
        previous_period = period
        previous_team = team
        previous_action = action
        previous_pass_outcome = pass_outcome

    return pd.Series(sequence_ids, index=frame.index)


def _end_coordinates(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    pass_end_x = pd.to_numeric(frame.get("pass_end_x", np.nan), errors="coerce")
    pass_end_y = pd.to_numeric(frame.get("pass_end_y", np.nan), errors="coerce")
    carry_end_x = pd.to_numeric(frame.get("carry_end_x", np.nan), errors="coerce")
    carry_end_y = pd.to_numeric(frame.get("carry_end_y", np.nan), errors="coerce")

    end_x = pass_end_x.where(frame["action_type"].eq("Pass"), carry_end_x)
    end_y = pass_end_y.where(frame["action_type"].eq("Pass"), carry_end_y)
    return end_x, end_y


def add_possession_future_features(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events.copy()

    frame = events.copy()
    frame = frame.sort_values(["match_id", "period", "index"]).reset_index(drop=True)
    frame["possession_id_source"] = _possession_source(frame)
    frame["possession_sequence_id"] = _possession_key(frame)
    frame["possession_event_index"] = frame.groupby("possession_sequence_id", sort=False).cumcount() + 1
    frame["possession_event_count"] = frame.groupby("possession_sequence_id", sort=False)["event_id"].transform("count")
    possession_team = frame.get("possession_team_name", pd.Series("Unknown", index=frame.index)).fillna("Unknown").astype(str)
    event_team = frame.get("team_name", pd.Series("Unknown", index=frame.index)).fillna("Unknown").astype(str)
    frame["event_team_in_possession"] = possession_team.eq("Unknown") | event_team.eq(possession_team)
    frame["action_family"] = [
        action_family(action, pattern)
        for action, pattern in zip(frame["action_type"], frame.get("play_pattern", pd.Series("", index=frame.index)))
    ]

    shot_xg = pd.to_numeric(frame.get("shot_xg", 0.0), errors="coerce").fillna(0.0)
    frame["is_shot"] = frame["action_type"].eq("Shot")
    if "is_goal_event" in frame.columns:
        frame["is_goal_event"] = frame["is_goal_event"].fillna(False).astype(bool)
    else:
        frame["is_goal_event"] = frame.get("shot_outcome", pd.Series("", index=frame.index)).astype(str).eq("Goal")

    frame["future_shot"] = False
    frame["future_goal"] = False
    frame["future_xg"] = 0.0
    frame["max_future_xg"] = 0.0
    frame["sum_future_xg"] = 0.0
    frame["actions_until_shot"] = np.nan
    frame["shot_within_3"] = False
    frame["shot_within_5"] = False
    frame["shot_within_10"] = False

    for _, idx in frame.groupby("possession_sequence_id", sort=False).groups.items():
        positions = list(idx)
        n = len(positions)
        future_shot_positions: list[int] = []
        future_goal_seen = False
        future_xgs: list[float] = []

        for local_pos in range(n - 1, -1, -1):
            row_idx = positions[local_pos]
            if future_shot_positions and bool(frame.at[row_idx, "event_team_in_possession"]):
                next_shot_local = future_shot_positions[-1]
                distance = next_shot_local - local_pos
                frame.at[row_idx, "future_shot"] = True
                frame.at[row_idx, "future_goal"] = future_goal_seen
                frame.at[row_idx, "future_xg"] = future_xgs[-1]
                frame.at[row_idx, "max_future_xg"] = max(future_xgs)
                frame.at[row_idx, "sum_future_xg"] = sum(future_xgs)
                frame.at[row_idx, "actions_until_shot"] = distance
                frame.at[row_idx, "shot_within_3"] = distance <= 3
                frame.at[row_idx, "shot_within_5"] = distance <= 5
                frame.at[row_idx, "shot_within_10"] = distance <= 10

            if bool(frame.at[row_idx, "is_shot"]):
                future_shot_positions.append(local_pos)
                future_xgs.append(float(shot_xg.iloc[row_idx]))
                future_goal_seen = future_goal_seen or bool(frame.at[row_idx, "is_goal_event"])

    end_x, end_y = _end_coordinates(frame)
    start_x = pd.to_numeric(frame.get("x", np.nan), errors="coerce")
    start_y = pd.to_numeric(frame.get("y", np.nan), errors="coerce")
    frame["value_state"] = [assign_value_state(x, y) for x, y in zip(start_x, start_y)]
    frame["end_x_for_sequence"] = end_x
    frame["end_y_for_sequence"] = end_y
    frame["territorial_progression"] = (end_x - start_x).where(end_x.notna() & start_x.notna(), 0.0)
    frame["final_third_entry"] = (start_x < 80) & (end_x >= 80)
    starts_outside_box = ~((start_x >= 102) & start_y.between(18, 62, inclusive="both"))
    ends_inside_box = (end_x >= 102) & end_y.between(18, 62, inclusive="both")
    frame["box_entry"] = starts_outside_box & ends_inside_box
    frame["future_threat"] = frame["future_shot"].astype(float) * pd.to_numeric(frame["future_xg"], errors="coerce").fillna(0.0)
    return frame


def build_state_values(events: pd.DataFrame, state_col: str = "value_state", min_cases_for_goal: int = 30) -> pd.DataFrame:
    frame = events.copy() if "future_shot" in events.columns else add_possession_future_features(events)
    if state_col == "value_state" and state_col not in frame.columns:
        x_values = pd.to_numeric(frame.get("x", np.nan), errors="coerce")
        y_values = pd.to_numeric(frame.get("y", np.nan), errors="coerce")
        frame[state_col] = [assign_value_state(x, y) for x, y in zip(x_values, y_values)]
    if frame.empty or state_col not in frame.columns:
        return pd.DataFrame()
    if "event_team_in_possession" in frame.columns:
        frame = frame[frame["event_team_in_possession"].fillna(False)].copy()
    if frame.empty:
        return pd.DataFrame()
    shot_xg = pd.to_numeric(frame.get("shot_xg", 0.0), errors="coerce").fillna(0.0)
    frame["state_future_shot"] = frame["future_shot"] | frame["is_shot"]
    frame["state_future_goal"] = frame["future_goal"] | frame["is_goal_event"]
    frame["state_future_xg"] = np.where(frame["is_shot"], shot_xg, frame["future_xg"])
    frame["state_shot_within_5"] = frame["shot_within_5"] | frame["is_shot"]
    frame["state_shot_within_10"] = frame["shot_within_10"] | frame["is_shot"]

    values = (
        frame[frame[state_col].notna() & frame[state_col].ne("Unknown")]
        .groupby(state_col, dropna=False)
        .agg(
            state_events=("event_id", "count"),
            V_shot=("state_future_shot", "mean"),
            V_goal=("state_future_goal", "mean"),
            V_xg=("state_future_xg", "mean"),
            V_shot_5=("state_shot_within_5", "mean"),
            V_shot_10=("state_shot_within_10", "mean"),
        )
        .reset_index()
        .rename(columns={state_col: "state"})
    )
    values["V_goal"] = values["V_goal"].where(values["state_events"] >= min_cases_for_goal, np.nan)
    terminal = pd.DataFrame(
        [
            {
                "state": TERMINAL_STATE,
                "state_events": 0,
                "V_shot": 0.0,
                "V_goal": 0.0,
                "V_xg": 0.0,
                "V_shot_5": 0.0,
                "V_shot_10": 0.0,
            }
        ]
    )
    return pd.concat([values, terminal], ignore_index=True)


def add_possession_value_deltas(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy() if "future_shot" in events.columns else add_possession_future_features(events)
    if frame.empty:
        return frame

    state_values = build_state_values(frame)
    if state_values.empty:
        for column in [
            "state_origin",
            "state_destination",
            "value_state_origin",
            "value_state_destination",
            "visual_zone_origin",
            "visual_zone_destination",
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
            "pass_complete",
            "value_delta_available",
        ]:
            frame[column] = np.nan
        return frame

    value_lookup = state_values.set_index("state").to_dict(orient="index")
    if "value_state" not in frame.columns:
        start_x = pd.to_numeric(frame.get("x", np.nan), errors="coerce")
        start_y = pd.to_numeric(frame.get("y", np.nan), errors="coerce")
        frame["value_state"] = [assign_value_state(x, y) for x, y in zip(start_x, start_y)]

    frame["visual_zone_origin"] = frame["zone"].where(frame["zone"].notna(), "Unknown")
    frame["value_state_origin"] = frame["value_state"].where(frame["value_state"].notna(), "Unknown")
    frame["state_origin"] = frame["value_state_origin"]
    end_x, end_y = _end_coordinates(frame)
    frame["pass_complete"] = np.where(
        frame["action_type"].eq("Pass"),
        _is_complete_pass(frame["pass_outcome"]),
        np.nan,
    )

    value_destination = pd.Series(np.nan, index=frame.index, dtype="object")
    visual_destination = pd.Series(np.nan, index=frame.index, dtype="object")
    pass_complete = frame["action_type"].eq("Pass") & frame["pass_complete"].astype("boolean").fillna(False)
    pass_incomplete = frame["action_type"].eq("Pass") & ~frame["pass_complete"].astype("boolean").fillna(False)
    carries = frame["action_type"].eq("Carry")
    value_destination.loc[pass_complete | carries] = [
        assign_value_state(x, y) for x, y in zip(end_x.loc[pass_complete | carries], end_y.loc[pass_complete | carries])
    ]
    visual_destination.loc[pass_complete | carries] = [
        assign_zone(x, y) for x, y in zip(end_x.loc[pass_complete | carries], end_y.loc[pass_complete | carries])
    ]
    value_destination.loc[pass_incomplete] = TERMINAL_STATE
    visual_destination.loc[pass_incomplete] = TERMINAL_STATE

    dribbles = frame["action_type"].eq("Dribble")
    if dribbles.any():
        grouped = frame.groupby("possession_sequence_id", sort=False)
        next_team = grouped["team_name"].shift(-1)
        next_possession_team = grouped["possession_team_name"].shift(-1) if "possession_team_name" in frame.columns else next_team
        next_x = grouped["x"].shift(-1)
        next_y = grouped["y"].shift(-1)
        reliable_next = (
            dribbles
            & frame["event_team_in_possession"].fillna(False)
            & next_team.eq(frame["team_name"])
            & next_possession_team.eq(frame.get("possession_team_name", next_team))
            & next_x.notna()
            & next_y.notna()
        )
        value_destination.loc[reliable_next] = [assign_value_state(x, y) for x, y in zip(next_x.loc[reliable_next], next_y.loc[reliable_next])]
        visual_destination.loc[reliable_next] = [assign_zone(x, y) for x, y in zip(next_x.loc[reliable_next], next_y.loc[reliable_next])]

    frame["value_state_destination"] = value_destination
    frame["visual_zone_destination"] = visual_destination
    frame["state_destination"] = frame["value_state_destination"]
    frame["value_delta_available"] = (
        frame["event_team_in_possession"].fillna(False)
        & frame["state_origin"].isin(value_lookup)
        & frame["state_destination"].isin(value_lookup)
    )

    for prefix, state_col in [("origin", "state_origin"), ("destination", "state_destination")]:
        frame[f"V_shot_{prefix}"] = frame[state_col].map(lambda state: value_lookup.get(state, {}).get("V_shot", np.nan))
        frame[f"V_goal_{prefix}"] = frame[state_col].map(lambda state: value_lookup.get(state, {}).get("V_goal", np.nan))
        frame[f"V_xg_{prefix}"] = frame[state_col].map(lambda state: value_lookup.get(state, {}).get("V_xg", np.nan))
        frame[f"V_shot_5_{prefix}"] = frame[state_col].map(lambda state: value_lookup.get(state, {}).get("V_shot_5", np.nan))
        frame[f"V_shot_10_{prefix}"] = frame[state_col].map(lambda state: value_lookup.get(state, {}).get("V_shot_10", np.nan))

    frame["delta_chance_finalizacao"] = frame["V_shot_destination"] - frame["V_shot_origin"]
    frame["delta_xg_futuro"] = frame["V_xg_destination"] - frame["V_xg_origin"]
    frame["delta_valor_posse"] = frame["delta_xg_futuro"]
    frame["xt_origin"] = frame["V_xg_origin"]
    frame["xt_destination"] = frame["V_xg_destination"]
    frame["delta_xt"] = frame["delta_valor_posse"]
    frame.loc[
        ~frame["value_delta_available"],
        ["delta_chance_finalizacao", "delta_xg_futuro", "delta_valor_posse", "xt_origin", "xt_destination", "delta_xt"],
    ] = np.nan
    return frame


def summarize_sequence_value(events: pd.DataFrame, group_cols: list[str], include_shots: bool = True) -> pd.DataFrame:
    future_cols = {
        "future_shot",
        "future_goal",
        "future_xg",
        "max_future_xg",
        "sum_future_xg",
        "actions_until_shot",
        "shot_within_3",
        "shot_within_5",
        "shot_within_10",
        "territorial_progression",
        "final_third_entry",
        "box_entry",
        "future_threat",
        "is_shot",
    }
    frame = events.copy() if future_cols.issubset(events.columns) else add_possession_future_features(events)
    if frame.empty:
        return pd.DataFrame()
    if not include_shots:
        frame = frame[~frame["is_shot"]]
    if frame.empty:
        return pd.DataFrame()

    grouped = frame.groupby(group_cols, dropna=False)
    summary = grouped.agg(
        ocorrencias=("event_id", "count"),
        posses_com_finalizacao=("future_shot", "sum"),
        posses_com_gol=("future_goal", "sum"),
        finalizacoes_proprias=("is_shot", "sum"),
        xg_finalizacoes=("shot_xg", "sum"),
        ameaca_futura_media=("future_threat", "mean"),
        xg_futuro_medio=("future_xg", "mean"),
        max_xg_futuro_medio=("max_future_xg", "mean"),
        xg_futuro_total=("sum_future_xg", "sum"),
        acoes_ate_finalizacao_media=("actions_until_shot", "mean"),
        finalizacao_ate_3=("shot_within_3", "mean"),
        finalizacao_ate_5=("shot_within_5", "mean"),
        finalizacao_ate_10=("shot_within_10", "mean"),
        progressao_media=("territorial_progression", "mean"),
        entradas_terco_final=("final_third_entry", "sum"),
        entradas_area=("box_entry", "sum"),
        delta_chance_finalizacao_medio=("delta_chance_finalizacao", "mean") if "delta_chance_finalizacao" in frame.columns else ("future_shot", "mean"),
        delta_xg_futuro_medio=("delta_xg_futuro", "mean") if "delta_xg_futuro" in frame.columns else ("future_xg", "mean"),
        delta_valor_posse_medio=("delta_valor_posse", "mean") if "delta_valor_posse" in frame.columns else ("future_xg", "mean"),
        delta_xt_medio=("delta_xt", "mean") if "delta_xt" in frame.columns else ("future_xg", "mean"),
    ).reset_index()
    summary["chance_finalizacao_futura"] = summary["posses_com_finalizacao"] / summary["ocorrencias"].replace(0, np.nan)
    summary["chance_gol_futuro"] = summary["posses_com_gol"] / summary["ocorrencias"].replace(0, np.nan)
    summary["xg_por_chute"] = summary["xg_finalizacoes"] / summary["finalizacoes_proprias"].replace(0, np.nan)
    summary["entrada_terco_final_pct"] = summary["entradas_terco_final"] / summary["ocorrencias"].replace(0, np.nan)
    summary["entrada_area_pct"] = summary["entradas_area"] / summary["ocorrencias"].replace(0, np.nan)
    return summary.sort_values(["chance_finalizacao_futura", "xg_futuro_medio", "ocorrencias"], ascending=False)


def format_sequence_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    percent_cols = [
        "chance_finalizacao_futura",
        "chance_gol_futuro",
        "finalizacao_ate_3",
        "finalizacao_ate_5",
        "finalizacao_ate_10",
        "entrada_terco_final_pct",
        "entrada_area_pct",
    ]
    for col in percent_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").map(lambda value: "" if pd.isna(value) else f"{value:.1%}")
    for col in [
        "ameaca_futura_media",
        "xg_futuro_medio",
        "max_xg_futuro_medio",
        "xg_futuro_total",
        "delta_chance_finalizacao_medio",
        "delta_xg_futuro_medio",
        "delta_valor_posse_medio",
        "delta_xt_medio",
        "xg_finalizacoes",
        "xg_por_chute",
        "progressao_media",
        "acoes_ate_finalizacao_media",
    ]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
    return result.rename(
        columns={
            "posses_com_finalizacao": "acoes_que_antecedem_finalizacao",
            "posses_com_gol": "acoes_que_antecedem_gol",
            "chance_finalizacao_futura": "chance_posse_terminar_em_finalizacao",
            "chance_gol_futuro": "chance_posse_terminar_em_gol",
            "xg_futuro_medio": "xg_futuro_associado_medio",
            "xg_futuro_total": "xg_futuro_associado_acumulado",
            "ameaca_futura_media": "ameaca_futura_associada_media",
            "delta_chance_finalizacao_medio": "mudanca_media_chance_finalizacao",
            "delta_xg_futuro_medio": "mudanca_media_xg_futuro_esperado",
            "delta_valor_posse_medio": "mudanca_media_valor_posse",
            "delta_xt_medio": "delta_xt_medio_eventos",
            "finalizacao_ate_3": "finalizacao_em_ate_3_acoes",
            "finalizacao_ate_5": "finalizacao_em_ate_5_acoes",
            "finalizacao_ate_10": "finalizacao_em_ate_10_acoes",
        }
    )
