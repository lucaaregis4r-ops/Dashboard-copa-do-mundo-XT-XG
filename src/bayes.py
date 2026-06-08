from __future__ import annotations

import pandas as pd


def add_dirichlet_posterior(rankings: pd.DataFrame, alpha: float = 1.0) -> pd.DataFrame:
    if rankings.empty:
        return rankings

    frame = rankings.copy()
    k = frame["next_action"].nunique()
    total = float(frame["count"].sum())
    frame["raw_probability"] = frame["probability"]
    frame["posterior_probability"] = (frame["count"] + alpha) / (total + alpha * k)
    frame["difference"] = frame["posterior_probability"] - frame["raw_probability"]
    columns = [
        "next_action",
        "count",
        "raw_probability",
        "posterior_probability",
        "difference",
        "observed_cases",
    ]
    columns += [
        column
        for column in [
            "delta_xt_medio",
            "delta_valor_posse_medio",
            "valor_caminho",
            "chance_finalizacao_futura",
            "xg_futuro_medio",
            "xg_futuro_total_medio",
            "xg_delta_medio",
            "xg_proxima_acao",
        ]
        if column in frame.columns
    ]
    return frame[columns].sort_values(["posterior_probability", "count"], ascending=[False, False]).reset_index(drop=True)


def confidence_label(observed_cases: int) -> str:
    if observed_cases < 30:
        return "baixa"
    if observed_cases < 100:
        return "media"
    return "alta"
