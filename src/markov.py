from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _prepare_transition_table(
    counts: pd.DataFrame,
    group_cols: list[str],
    next_col: str = "next_action",
) -> pd.DataFrame:
    counts = counts.copy()
    counts["observed_cases"] = counts.groupby(group_cols)["count"].transform("sum")
    counts["probability"] = counts["count"] / counts["observed_cases"]
    counts = counts.sort_values(group_cols + ["probability", "count"], ascending=[True] * len(group_cols) + [False, False])
    return counts


def _add_transition_xg_delta(counts: pd.DataFrame, frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if counts.empty or frame.empty:
        return counts

    working = frame.copy()
    if "current_action" in group_cols and "current_action" not in working.columns and "action_type" in working.columns:
        working["current_action"] = working["action_type"]
    missing_cols = [col for col in group_cols + ["next_action"] if col not in working.columns]
    if missing_cols:
        counts = counts.copy()
        counts["xg_delta_medio"] = 0.0
        counts["xg_proxima_acao"] = 0.0
        counts["chance_finalizacao_futura"] = 0.0
        counts["xg_futuro_medio"] = 0.0
        counts["xg_futuro_total_medio"] = 0.0
        counts["delta_xt_medio"] = 0.0
        counts["delta_valor_posse_medio"] = 0.0
        counts["valor_caminho"] = 0.0
        return counts

    working["current_xg"] = pd.to_numeric(working["shot_xg"], errors="coerce").fillna(0.0)
    next_xg_source = working["next_shot_xg"] if "next_shot_xg" in working.columns else pd.Series(0.0, index=working.index)
    working["next_xg"] = pd.to_numeric(next_xg_source, errors="coerce").fillna(0.0)
    working["xg_delta"] = working["next_xg"] - working["current_xg"]
    if "future_shot" not in working.columns:
        working["future_shot"] = False
    if "future_xg" not in working.columns:
        working["future_xg"] = 0.0
    if "sum_future_xg" not in working.columns:
        working["sum_future_xg"] = 0.0
    if "delta_xt" not in working.columns:
        working["delta_xt"] = 0.0
    if "delta_valor_posse" not in working.columns:
        working["delta_valor_posse"] = working["delta_xt"]
    impact = (
        working.groupby(group_cols + ["next_action"], dropna=False)
        .agg(
            xg_delta_medio=("xg_delta", "mean"),
            xg_proxima_acao=("next_xg", "mean"),
            chance_finalizacao_futura=("future_shot", "mean"),
            xg_futuro_medio=("future_xg", "mean"),
            xg_futuro_total_medio=("sum_future_xg", "mean"),
            delta_xt_medio=("delta_xt", "mean"),
            delta_valor_posse_medio=("delta_valor_posse", "mean"),
        )
        .reset_index()
    )
    result = counts.merge(impact, on=group_cols + ["next_action"], how="left")
    result["valor_caminho"] = result["probability"] * pd.to_numeric(result["delta_xt_medio"], errors="coerce").fillna(0.0)
    result["valor_caminho"] = pd.to_numeric(result["valor_caminho"], errors="coerce").fillna(0.0)
    return result


def _transition_display_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "next_action",
        "count",
        "probability",
        "observed_cases",
        "chance_finalizacao_futura",
        "xg_futuro_medio",
        "xg_futuro_total_medio",
        "delta_xt_medio",
        "delta_valor_posse_medio",
        "valor_caminho",
        "xg_delta_medio",
        "xg_proxima_acao",
    ]
    for column in columns:
        if column not in frame.columns:
            frame[column] = 0.0
    return frame[columns].reset_index(drop=True)


def build_first_order_model(events: pd.DataFrame) -> dict:
    frame = events[(events["action_type"] != "Unknown") & (events["next_action"] != "END")].copy()
    if frame.empty:
        empty = pd.DataFrame()
        return {"transition_counts": empty, "transition_matrix": empty}

    counts = (
        frame.groupby(["action_type", "next_action"])
        .size()
        .reset_index(name="count")
        .rename(columns={"action_type": "current_action"})
    )
    frame["current_action"] = frame["action_type"]
    counts = _prepare_transition_table(counts, ["current_action"])
    counts = _add_transition_xg_delta(counts, frame, ["current_action"])
    matrix = counts.pivot(index="current_action", columns="next_action", values="probability").fillna(0.0)
    return {"transition_counts": counts, "transition_matrix": matrix}


def get_action_rankings(model: dict, selected_action: str) -> pd.DataFrame:
    counts = model["transition_counts"]
    if counts.empty:
        return counts
    result = counts[counts["current_action"] == selected_action].copy()
    return _transition_display_columns(result)


def build_action_zone_model(events: pd.DataFrame) -> dict:
    frame = events[
        (events["action_type"] != "Unknown") & (events["next_action"] != "END") & (events["zone"] != "Unknown")
    ].copy()
    if frame.empty:
        return {"transition_counts": pd.DataFrame()}

    counts = (
        frame.groupby(["action_type", "zone", "next_action"])
        .size()
        .reset_index(name="count")
        .rename(columns={"action_type": "current_action"})
    )
    frame["current_action"] = frame["action_type"]
    counts = _prepare_transition_table(counts, ["current_action", "zone"])
    counts = _add_transition_xg_delta(counts, frame, ["current_action", "zone"])
    return {"transition_counts": counts}


def get_action_zone_rankings(model: dict, selected_action: str, selected_zone: str) -> pd.DataFrame:
    counts = model["transition_counts"]
    if counts.empty:
        return counts
    result = counts[(counts["current_action"] == selected_action) & (counts["zone"] == selected_zone)].copy()
    return _transition_display_columns(result)


def build_second_order_model(events: pd.DataFrame) -> dict:
    frame = events[
        (events["previous_action"] != "START")
        & (events["action_type"] != "Unknown")
        & (events["next_action"] != "END")
    ].copy()
    if frame.empty:
        return {"transition_counts": pd.DataFrame()}

    counts = (
        frame.groupby(["previous_action", "action_type", "next_action"])
        .size()
        .reset_index(name="count")
        .rename(columns={"action_type": "current_action"})
    )
    frame["current_action"] = frame["action_type"]
    counts = _prepare_transition_table(counts, ["previous_action", "current_action"])
    counts = _add_transition_xg_delta(counts, frame, ["previous_action", "current_action"])
    return {"transition_counts": counts}


def get_second_order_rankings(model: dict, previous_action: str, current_action: str) -> pd.DataFrame:
    counts = model["transition_counts"]
    if counts.empty:
        return counts
    result = counts[
        (counts["previous_action"] == previous_action) & (counts["current_action"] == current_action)
    ].copy()
    return _transition_display_columns(result)


def _score_predictions(
    test_frame: pd.DataFrame,
    probability_lookup: dict,
    fallback_lookup: dict,
    context_cols: list[str],
) -> tuple[float, float, float]:
    if test_frame.empty:
        return math.nan, math.nan, math.nan

    top1_hits = 0
    top3_hits = 0
    losses = []

    for row in test_frame.itertuples(index=False):
        context = tuple(getattr(row, col) for col in context_cols)
        if len(context) == 1:
            context = context[0]
        actual = row.next_action
        distribution = probability_lookup.get(context, fallback_lookup)
        ranked = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
        top_actions = [name for name, _ in ranked[:3]]
        top1 = top_actions[0] if top_actions else None

        if top1 == actual:
            top1_hits += 1
        if actual in top_actions:
            top3_hits += 1

        prob = max(distribution.get(actual, 1e-12), 1e-12)
        losses.append(-math.log(prob))

    n = len(test_frame)
    return top1_hits / n, top3_hits / n, float(np.mean(losses))


def evaluate_year_transfer(events: pd.DataFrame, train_year: int = 2018, test_year: int = 2022) -> dict:
    train = events[
        (events["year"] == train_year) & (events["next_action"] != "END") & (events["previous_action"] != "START")
    ].copy()
    test = events[
        (events["year"] == test_year) & (events["next_action"] != "END") & (events["previous_action"] != "START")
    ].copy()

    if train.empty or test.empty:
        return {
            "metrics": pd.DataFrame(),
            "interpretation": "Não foi possível calcular a transferência.",
            "markov_beats_baseline": False,
        }

    second_order = build_second_order_model(train)
    counts = second_order["transition_counts"]
    probability_lookup = {
        (previous_action, current_action): group.set_index("next_action")["probability"].to_dict()
        for (previous_action, current_action), group in counts.groupby(["previous_action", "current_action"])
    }

    baseline_counts = train["next_action"].value_counts(normalize=True)
    baseline_lookup = baseline_counts.to_dict()

    markov_scores = _score_predictions(test, probability_lookup, baseline_lookup, ["previous_action", "action_type"])
    baseline_scores = _score_predictions(test, {}, baseline_lookup, ["previous_action", "action_type"])

    metrics = pd.DataFrame(
        [
            {
                "model": "Baseline 2018",
                "top_1_accuracy": baseline_scores[0],
                "top_3_accuracy": baseline_scores[1],
                "log_loss": baseline_scores[2],
            },
            {
                "model": "Markov 2018",
                "top_1_accuracy": markov_scores[0],
                "top_3_accuracy": markov_scores[1],
                "log_loss": markov_scores[2],
            },
        ]
    )

    markov_beats = (
        markov_scores[0] > baseline_scores[0]
        or markov_scores[1] > baseline_scores[1]
        or markov_scores[2] < baseline_scores[2]
    )
    interpretation = (
        "O modelo com contexto de ação anterior transferiu melhor que a frequência geral."
        if markov_beats
        else "O padrão aprendido em 2018 não melhorou a previsão em relação ao baseline."
    )

    return {
        "metrics": metrics,
        "interpretation": interpretation,
        "markov_beats_baseline": markov_beats,
    }


def build_team_transition_vectors(events: pd.DataFrame) -> pd.DataFrame:
    frame = events[(events["action_type"] != "Unknown") & (events["next_action"] != "END")].copy()
    if frame.empty:
        return pd.DataFrame()

    counts = frame.groupby(["team_name", "action_type", "next_action"]).size().reset_index(name="count")
    counts["feature"] = counts["action_type"] + " -> " + counts["next_action"]
    counts["probability"] = counts.groupby("team_name")["count"].transform(lambda series: series / series.sum())
    vectors = counts.pivot(index="team_name", columns="feature", values="probability").fillna(0.0)
    return vectors


def _cosine_similarity_matrix(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.empty((0, 0))

    numeric = np.asarray(values, dtype=float)
    norms = np.linalg.norm(numeric, axis=1)
    denominator = np.outer(norms, norms)
    numerator = numeric @ numeric.T
    similarity = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator, dtype=float),
        where=denominator != 0,
    )
    return similarity


def compute_similarity_matrix(vectors: pd.DataFrame) -> pd.DataFrame:
    if vectors.empty:
        return pd.DataFrame()

    matrix = _cosine_similarity_matrix(vectors.values)
    return pd.DataFrame(matrix, index=vectors.index, columns=vectors.index)
