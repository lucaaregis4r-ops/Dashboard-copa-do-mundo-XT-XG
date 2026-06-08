from __future__ import annotations

import pandas as pd


ATTACKING_ZONES = ["ataque esquerda", "ataque centro", "ataque direita"]


def format_number(value: float) -> str:
    if pd.isna(value):
        return "0"
    if float(value).is_integer():
        return f"{int(value):,}".replace(",", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_entity_summary(events: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    frame = events.copy()
    for column, default in {
        "delta_xt": 0.0,
        "delta_valor_posse": 0.0,
        "future_xg": 0.0,
        "future_shot": False,
        "final_third_entry": False,
        "box_entry": False,
        "is_progressive_event": False,
        "threat_added": 0.0,
    }.items():
        if column not in frame.columns:
            frame[column] = default
    if entity_col == "player_name":
        frame = frame[frame["player_name"].ne("Unknown")]
    if frame.empty:
        return pd.DataFrame()

    action_counts = frame.groupby([entity_col, "action_type"]).size().unstack(fill_value=0).rename_axis(None, axis=1)
    summary = pd.DataFrame(index=action_counts.index)
    summary["total_actions"] = action_counts.sum(axis=1)
    summary["passes"] = action_counts.get("Pass", 0)
    summary["shots"] = action_counts.get("Shot", 0)
    summary["carries"] = action_counts.get("Carry", 0)
    summary["pressures"] = action_counts.get("Pressure", 0)
    summary["recoveries"] = action_counts.get("Ball Recovery", 0)

    grouped = frame.groupby(entity_col)
    summary["matches"] = grouped["match_id"].nunique()
    summary["xg"] = grouped["shot_xg"].sum(min_count=1).fillna(0.0)
    if "is_goal_event" in frame.columns:
        summary["goals"] = grouped["is_goal_event"].sum().fillna(0).astype(int)
    else:
        summary["goals"] = grouped["shot_outcome"].apply(lambda series: series.eq("Goal").sum()).fillna(0).astype(int)
    summary["assists"] = grouped["pass_goal_assist"].sum().fillna(0).astype(int) if "pass_goal_assist" in frame.columns else 0
    summary["under_pressure_rate"] = grouped["under_pressure"].mean().fillna(0.0)
    summary["attacking_zone_rate"] = grouped.apply(lambda g: g["zone"].isin(ATTACKING_ZONES).mean()).fillna(0.0)
    summary["action_variety"] = grouped["action_type"].nunique()
    summary["avg_actions_per_match"] = summary["total_actions"] / summary["matches"].replace(0, 1)
    summary["delta_xt_total"] = grouped["delta_xt"].sum().fillna(0.0)
    summary["delta_xt_mean"] = grouped["delta_xt"].mean().fillna(0.0)
    summary["delta_valor_posse_mean"] = grouped["delta_valor_posse"].mean().fillna(0.0)
    summary["future_xg_associated"] = grouped["future_xg"].sum().fillna(0.0)
    summary["future_shot_rate"] = grouped["future_shot"].mean().fillna(0.0)
    summary["final_third_entries"] = grouped["final_third_entry"].sum().fillna(0).astype(int)
    summary["box_entries"] = grouped["box_entry"].sum().fillna(0).astype(int)
    summary["progressive_events"] = grouped["is_progressive_event"].sum().fillna(0).astype(int)
    summary["threat_added"] = grouped["threat_added"].sum().fillna(0.0)

    return summary.reset_index()


def comparison_long(summary: pd.DataFrame, entity_col: str, first: str, second: str, metrics: list[str]) -> pd.DataFrame:
    base = summary[summary[entity_col].isin([first, second])][[entity_col] + metrics].copy()
    if base.empty:
        return pd.DataFrame()
    return base.melt(id_vars=[entity_col], value_vars=metrics, var_name="metric", value_name="value")


def format_comparison_table(
    summary: pd.DataFrame,
    entity_col: str,
    first: str,
    second: str,
    metrics: list[str],
) -> pd.DataFrame:
    summary = summary.copy()
    for metric in metrics:
        if metric not in summary.columns:
            summary[metric] = 0

    subset = summary[summary[entity_col].isin([first, second])][[entity_col] + metrics].copy()
    if subset.empty:
        return subset
    for metric in metrics:
        subset[metric] = subset[metric].map(format_number)
    return subset
