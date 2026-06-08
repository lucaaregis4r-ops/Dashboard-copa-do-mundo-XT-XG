from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


FIELD_ZONES = {
    "defesa esquerda": (0, 40, 0, 26.6667),
    "defesa centro": (0, 40, 26.6667, 53.3333),
    "defesa direita": (0, 40, 53.3333, 80),
    "meio esquerda": (40, 80, 0, 26.6667),
    "meio centro": (40, 80, 26.6667, 53.3333),
    "meio direita": (40, 80, 53.3333, 80),
    "ataque esquerda": (80, 120, 0, 26.6667),
    "ataque centro": (80, 120, 26.6667, 53.3333),
    "ataque direita": (80, 120, 53.3333, 80),
}

FIELD_THIRDS = {
    "Defesa": (0, 40),
    "Meio": (40, 80),
    "Ataque": (80, 120),
}

PERIOD_LABELS = {
    1: "1º tempo",
    2: "2º tempo",
    3: "Prorrogação 1",
    4: "Prorrogação 2",
    5: "Pênaltis",
}

PERIOD_LABELS = {
    1: "1o tempo",
    2: "2o tempo",
    3: "Prorrogacao 1",
    4: "Prorrogacao 2",
    5: "Penaltis",
}

MATCH_STATE_ORDER = ["Ganhando", "Empatando", "Perdendo", "Desconhecido"]
TIME_BUCKET_ORDER = [
    "0-15 min restantes",
    "16-30 min restantes",
    "31-45 min restantes",
    "46-60 min restantes",
    "Mais de 60 min",
]


def _nested_get(data: dict, keys: Iterable[str], default="Unknown"):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def _extract_xy(location):
    if isinstance(location, list) and len(location) >= 2:
        return float(location[0]), float(location[1])
    return np.nan, np.nan


def assign_zone(x: float, y: float) -> str:
    if pd.isna(x) or pd.isna(y):
        return "Unknown"

    for zone_name, (x_min, x_max, y_min, y_max) in FIELD_ZONES.items():
        x_ok = x_min <= x < x_max if x_max < 120 else x_min <= x <= x_max
        y_ok = y_min <= y < y_max if y_max < 80 else y_min <= y <= y_max
        if x_ok and y_ok:
            return zone_name

    return "Unknown"


def assign_field_third(x: float) -> str:
    if pd.isna(x):
        return "Desconhecido"

    for third_name, (x_min, x_max) in FIELD_THIRDS.items():
        x_ok = x_min <= x < x_max if x_max < 120 else x_min <= x <= x_max
        if x_ok:
            return third_name

    return "Desconhecido"


def get_period_label(period: int) -> str:
    return PERIOD_LABELS.get(period, f"Período {period}")


def estimate_total_match_seconds(period: float, minute: float) -> int:
    if pd.isna(period):
        return 90 * 60

    period_value = int(period)
    minute_value = float(minute) if pd.notna(minute) else 0.0

    if period_value <= 2:
        return 90 * 60
    if period_value <= 4:
        return 120 * 60
    if period_value == 5:
        return max(int(minute_value * 60), 120 * 60)
    return max(int(minute_value * 60), 90 * 60)


def time_remaining_bucket(minutes_remaining: float) -> str:
    if pd.isna(minutes_remaining):
        return "Desconhecido"
    if minutes_remaining <= 15:
        return "0-15 min restantes"
    if minutes_remaining <= 30:
        return "16-30 min restantes"
    if minutes_remaining <= 45:
        return "31-45 min restantes"
    if minutes_remaining <= 60:
        return "46-60 min restantes"
    return "Mais de 60 min"


def preprocess_events(raw_events: pd.DataFrame) -> pd.DataFrame:
    if raw_events.empty:
        return raw_events

    flat_columns = {"action_type", "team_name", "player_name", "x", "y", "zone"}
    if flat_columns.issubset(raw_events.columns):
        events = raw_events.copy()
    else:
        rows = []
        for event in raw_events.to_dict(orient="records"):
            x, y = _extract_xy(event.get("location"))
            pass_end_location = event.get("pass", {}).get("end_location") if isinstance(event.get("pass"), dict) else None
            carry_end_location = event.get("carry", {}).get("end_location") if isinstance(event.get("carry"), dict) else None
            pass_end_x, pass_end_y = _extract_xy(pass_end_location)
            carry_end_x, carry_end_y = _extract_xy(carry_end_location)

            rows.append(
                {
                    "match_id": event.get("match_id"),
                    "year": event.get("year"),
                    "event_id": event.get("id", "Unknown"),
                    "index": event.get("index"),
                    "period": event.get("period"),
                    "period_label": get_period_label(event.get("period")),
                    "timestamp": event.get("timestamp", "Unknown"),
                    "minute": event.get("minute"),
                    "second": event.get("second"),
                    "team_name": _nested_get(event, ["team", "name"]),
                    "player_name": _nested_get(event, ["player", "name"]),
                    "action_type": _nested_get(event, ["type", "name"]),
                    "possession": event.get("possession"),
                    "possession_team_name": _nested_get(event, ["possession_team", "name"]),
                    "location": event.get("location"),
                    "x": x,
                    "y": y,
                    "zone": assign_zone(x, y),
                    "field_third": assign_field_third(x),
                    "pass_end_location": pass_end_location,
                    "pass_end_x": pass_end_x,
                    "pass_end_y": pass_end_y,
                    "carry_end_location": carry_end_location,
                    "carry_end_x": carry_end_x,
                    "carry_end_y": carry_end_y,
                    "shot_xg": event.get("shot", {}).get("statsbomb_xg") if isinstance(event.get("shot"), dict) else np.nan,
                    "shot_outcome": _nested_get(event.get("shot", {}) if isinstance(event.get("shot"), dict) else {}, ["outcome", "name"]),
                    "pass_outcome": _nested_get(event.get("pass", {}) if isinstance(event.get("pass"), dict) else {}, ["outcome", "name"]),
                    "pass_goal_assist": bool(event.get("pass", {}).get("goal_assist", False)) if isinstance(event.get("pass"), dict) else False,
                    "shot_assist": bool(event.get("pass", {}).get("shot_assist", False)) if isinstance(event.get("pass"), dict) else False,
                    "under_pressure": bool(event.get("under_pressure", False)),
                    "play_pattern": _nested_get(event, ["play_pattern", "name"]),
                }
            )

        events = pd.DataFrame(rows)
    if "pass_goal_assist" not in events.columns:
        events["pass_goal_assist"] = False
    if "shot_assist" not in events.columns:
        events["shot_assist"] = False
    events["team_name"] = events["team_name"].fillna("Unknown")
    events["player_name"] = events["player_name"].fillna("Unknown")
    events["action_type"] = events["action_type"].fillna("Unknown")
    events["possession_team_name"] = events["possession_team_name"].fillna("Unknown")
    events["shot_outcome"] = events["shot_outcome"].fillna("Unknown")
    events["pass_outcome"] = events["pass_outcome"].fillna("Unknown")
    events["pass_goal_assist"] = events["pass_goal_assist"].fillna(False).astype(bool)
    events["shot_assist"] = events["shot_assist"].fillna(False).astype(bool)
    events["play_pattern"] = events["play_pattern"].fillna("Unknown")
    events["field_third"] = events["x"].map(assign_field_third)
    events["elapsed_seconds"] = (
        pd.to_numeric(events["minute"], errors="coerce").fillna(0).mul(60)
        + pd.to_numeric(events["second"], errors="coerce").fillna(0)
    )
    events["estimated_total_seconds"] = events.apply(
        lambda row: estimate_total_match_seconds(row["period"], row["minute"]),
        axis=1,
    )
    events["seconds_remaining"] = (events["estimated_total_seconds"] - events["elapsed_seconds"]).clip(lower=0)
    events["minutes_remaining"] = events["seconds_remaining"] / 60.0
    events["time_remaining_bucket"] = events["minutes_remaining"].map(time_remaining_bucket)

    return events.sort_values(["year", "match_id", "period", "index"]).reset_index(drop=True)


def add_sequence_features(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events

    ordered = events.sort_values(["match_id", "period", "index"]).copy()
    grouped = ordered.groupby("match_id", sort=False)

    ordered["previous_action"] = grouped["action_type"].shift(1).fillna("START")
    ordered["next_action"] = grouped["action_type"].shift(-1).fillna("END")
    ordered["previous_zone"] = grouped["zone"].shift(1).fillna("Unknown")
    ordered["next_zone"] = grouped["zone"].shift(-1).fillna("Unknown")
    ordered["next_field_third"] = grouped["field_third"].shift(-1).fillna("Desconhecido")
    ordered["next_shot_xg"] = grouped["shot_xg"].shift(-1).fillna(0.0)
    ordered["previous_team_name"] = grouped["team_name"].shift(1).fillna("Unknown")
    ordered["possession_change"] = grouped["possession"].diff().fillna(0).ne(0)

    return ordered.reset_index(drop=True)


def filter_events(
    events: pd.DataFrame,
    years=None,
    teams=None,
    match_ids=None,
    action_types=None,
    period_labels=None,
    zones=None,
) -> pd.DataFrame:
    filtered = events.copy()

    if years is not None:
        filtered = filtered[filtered["year"].isin(years)]
    if teams is not None:
        filtered = filtered[filtered["team_name"].isin(teams)]
    if match_ids is not None:
        filtered = filtered[filtered["match_id"].isin(match_ids)]
    if action_types is not None:
        filtered = filtered[filtered["action_type"].isin(action_types)]
    if period_labels is not None:
        filtered = filtered[filtered["period_label"].isin(period_labels)]
    if zones is not None:
        filtered = filtered[filtered["zone"].isin(zones)]

    return filtered


def format_match_label(row: pd.Series) -> str:
    date_label = row["match_date"].strftime("%Y-%m-%d") if pd.notna(row["match_date"]) else "Unknown date"
    return f"{row['year']} | {row['home_team']} {row['home_score']}-{row['away_score']} {row['away_team']} | {date_label}"
