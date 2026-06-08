from __future__ import annotations

import numpy as np
import pandas as pd


PROGRESSION_ACTIONS = {"Pass", "Carry"}


def pitch_value(x: pd.Series, y: pd.Series) -> pd.Series:
    x_norm = (pd.to_numeric(x, errors="coerce").fillna(0.0) / 120.0).clip(0.0, 1.0)
    y_num = pd.to_numeric(y, errors="coerce").fillna(40.0)
    centrality = (1.0 - (y_num - 40.0).abs() / 40.0).clip(0.0, 1.0)
    box_bonus = ((x_norm > 0.85) & (centrality > 0.45)).astype(float) * 0.08
    value = 0.01 + 0.24 * (x_norm**2) + 0.09 * x_norm * centrality + box_bonus
    return value.clip(0.0, 0.55)


def add_threat_features(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events.copy()

    frame = events.copy()
    frame["start_value"] = pitch_value(frame["x"], frame["y"])

    end_x = frame["pass_end_x"].where(frame["action_type"].eq("Pass"), frame["carry_end_x"])
    end_y = frame["pass_end_y"].where(frame["action_type"].eq("Pass"), frame["carry_end_y"])
    frame["end_x_for_threat"] = pd.to_numeric(end_x, errors="coerce")
    frame["end_y_for_threat"] = pd.to_numeric(end_y, errors="coerce")
    frame["end_value"] = pitch_value(frame["end_x_for_threat"], frame["end_y_for_threat"])

    has_end = frame["end_x_for_threat"].notna() & frame["end_y_for_threat"].notna()
    is_progression_action = frame["action_type"].isin(PROGRESSION_ACTIONS)
    frame["threat_delta"] = np.where(has_end & is_progression_action, frame["end_value"] - frame["start_value"], 0.0)
    frame["threat_added"] = pd.Series(frame["threat_delta"], index=frame.index).clip(lower=0.0)
    frame["threat_lost"] = pd.Series(frame["threat_delta"], index=frame.index).clip(upper=0.0)
    frame["progressive_distance"] = np.where(has_end & is_progression_action, frame["end_x_for_threat"] - frame["x"], 0.0)
    frame["is_progressive_event"] = (frame["progressive_distance"] >= 10.0) | (frame["threat_added"] >= 0.025)
    frame["is_shot"] = frame["action_type"].eq("Shot")
    return frame


def build_team_threat_summary(events: pd.DataFrame) -> pd.DataFrame:
    frame = add_threat_features(events)
    if frame.empty:
        return pd.DataFrame()

    grouped = frame.groupby("team_name", dropna=False)
    summary = grouped.agg(
        eventos=("event_id", "count"),
        ameaca_adicionada=("threat_added", "sum"),
        ameaca_liquida=("threat_delta", "sum"),
        acoes_progressivas=("is_progressive_event", "sum"),
        finalizacoes=("is_shot", "sum"),
        xg_finalizacoes=("shot_xg", "sum"),
    ).reset_index()
    summary["xg_por_finalizacao"] = summary["xg_finalizacoes"] / summary["finalizacoes"].replace(0, np.nan)
    summary["ameaca_por_100_eventos"] = summary["ameaca_adicionada"] / summary["eventos"].replace(0, np.nan) * 100
    return summary.sort_values("ameaca_adicionada", ascending=False)


def build_zone_threat_summary(events: pd.DataFrame) -> pd.DataFrame:
    frame = add_threat_features(events)
    if frame.empty:
        return pd.DataFrame()

    return (
        frame.groupby("zone", dropna=False)
        .agg(
            eventos=("event_id", "count"),
            ameaca_adicionada=("threat_added", "sum"),
            ameaca_liquida=("threat_delta", "sum"),
            acoes_progressivas=("is_progressive_event", "sum"),
            finalizacoes=("is_shot", "sum"),
            xg_finalizacoes=("shot_xg", "sum"),
        )
        .reset_index()
        .sort_values("ameaca_adicionada", ascending=False)
    )


def build_player_threat_summary(events: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    frame = add_threat_features(events)
    frame = frame[frame["player_name"].ne("Unknown")]
    if frame.empty:
        return pd.DataFrame()

    summary = (
        frame.groupby("player_name", dropna=False)
        .agg(
            eventos=("event_id", "count"),
            ameaca_adicionada=("threat_added", "sum"),
            acoes_progressivas=("is_progressive_event", "sum"),
            finalizacoes=("is_shot", "sum"),
            xg_finalizacoes=("shot_xg", "sum"),
        )
        .reset_index()
        .sort_values("ameaca_adicionada", ascending=False)
        .head(limit)
    )
    return summary
