from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.preprocess import assign_zone, get_period_label


DEFAULT_YEARS = (2018, 2022)


def _read_json_file(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def _extract_event_record(event: dict, match_id: int, year: int) -> dict:
    x, y = _extract_xy(event.get("location"))
    pass_data = event.get("pass") if isinstance(event.get("pass"), dict) else {}
    carry_data = event.get("carry") if isinstance(event.get("carry"), dict) else {}
    shot_data = event.get("shot") if isinstance(event.get("shot"), dict) else {}

    pass_end_location = pass_data.get("end_location")
    carry_end_location = carry_data.get("end_location")
    pass_end_x, pass_end_y = _extract_xy(pass_end_location)
    carry_end_x, carry_end_y = _extract_xy(carry_end_location)

    return {
        "match_id": match_id,
        "year": year,
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
        "pass_end_location": pass_end_location,
        "pass_end_x": pass_end_x,
        "pass_end_y": pass_end_y,
        "carry_end_location": carry_end_location,
        "carry_end_x": carry_end_x,
        "carry_end_y": carry_end_y,
        "shot_xg": shot_data.get("statsbomb_xg", np.nan),
        "shot_outcome": _nested_get(shot_data, ["outcome", "name"]),
        "pass_outcome": _nested_get(pass_data, ["outcome", "name"]),
        "pass_goal_assist": bool(pass_data.get("goal_assist", False)),
        "shot_assist": bool(pass_data.get("shot_assist", False)),
        "under_pressure": bool(event.get("under_pressure", False)),
        "play_pattern": _nested_get(event, ["play_pattern", "name"]),
    }


def check_data_availability(base_dir: Path) -> dict:
    matches_dir = base_dir / "matches"
    events_dir = base_dir / "events"
    three_sixty_dir = base_dir / "three-sixty"

    return {
        "matches_available": matches_dir.exists(),
        "events_available": events_dir.exists(),
        "three_sixty_available": three_sixty_dir.exists()
        and any((three_sixty_dir / str(year)).exists() for year in DEFAULT_YEARS),
    }


def load_matches(base_dir: Path, years: Iterable[int] = DEFAULT_YEARS) -> pd.DataFrame:
    matches_dir = base_dir / "matches"
    records = []

    for year in years:
        file_path = matches_dir / f"world_cup_{year}.json"
        if not file_path.exists():
            continue

        try:
            payload = _read_json_file(file_path)
        except (OSError, json.JSONDecodeError):
            continue

        for match in payload:
            records.append(
                {
                    "match_id": match.get("match_id"),
                    "year": year,
                    "match_date": match.get("match_date"),
                    "kick_off": match.get("kick_off"),
                    "home_team": ((match.get("home_team") or {}).get("home_team_name")) or "Unknown",
                    "away_team": ((match.get("away_team") or {}).get("away_team_name")) or "Unknown",
                    "home_score": match.get("home_score"),
                    "away_score": match.get("away_score"),
                    "stage": ((match.get("competition_stage") or {}).get("name")) or "Unknown",
                    "stadium": ((match.get("stadium") or {}).get("name")) or "Unknown",
                }
            )

    matches = pd.DataFrame.from_records(records)
    if matches.empty:
        return matches

    matches["match_date"] = pd.to_datetime(matches["match_date"], errors="coerce")
    return matches.sort_values(["year", "match_date", "match_id"]).reset_index(drop=True)


def load_events(base_dir: Path, years: Iterable[int] = DEFAULT_YEARS) -> pd.DataFrame:
    events_dir = base_dir / "events"
    records = []

    for year in years:
        year_dir = events_dir / str(year)
        if not year_dir.exists():
            continue

        for file_path in sorted(year_dir.glob("*.json")):
            try:
                payload = _read_json_file(file_path)
            except (OSError, json.JSONDecodeError):
                continue

            match_id = int(file_path.stem)
            for event in payload:
                records.append(_extract_event_record(event, match_id, year))

    return pd.DataFrame.from_records(records)
