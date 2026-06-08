from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.labels import action_color, action_label, team_label
from src.preprocess import FIELD_THIRDS, FIELD_ZONES


def _vertical_value_formats(values: pd.Series) -> tuple[str, str]:
    numeric = pd.to_numeric(values, errors="coerce").abs().dropna()
    if numeric.empty:
        return "%{y:.2f}", ".2f"
    max_abs = float(numeric.max())
    if max_abs and max_abs < 0.01:
        return "%{y:.4f}", ".4f"
    if max_abs < 0.1:
        return "%{y:.3f}", ".3f"
    if max_abs < 1:
        return "%{y:.2f}", ".2f"
    if max_abs < 10:
        return "%{y:.1f}", ".1f"
    return "%{y:,.0f}", ",.0f"


def _pad_vertical_axis(fig: go.Figure, values: pd.Series, pad: float = 1.22) -> go.Figure:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return fig
    max_value = float(numeric.max())
    min_value = float(numeric.min())
    max_abs = max(abs(max_value), abs(min_value))
    min_visible = 0.01 if max_abs <= 0.01 else 0.0
    lower = min(0.0, min_value * pad)
    upper = max(max_value * pad if max_value > 0 else 0.0, min_visible)
    if upper > lower:
        fig.update_yaxes(range=[lower, upper])
    return fig


def _base_pitch_figure(title: str) -> go.Figure:
    fig = go.Figure()

    line_color = "#f7f3e9"
    pitch_color = "#127a4f"

    shape_base = {"layer": "below"}
    shapes = [
        dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color=line_color, width=2), fillcolor="rgba(0,0,0,0)", **shape_base),
        dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color=line_color, width=2), **shape_base),
        dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color=line_color, width=2), **shape_base),
        dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color=line_color, width=2), **shape_base),
        dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color=line_color, width=2), **shape_base),
        dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color=line_color, width=2), **shape_base),
        dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color=line_color, width=2), **shape_base),
    ]

    fig.update_layout(
        title=dict(text=title, font=dict(color="#111827", size=18)),
        shapes=shapes,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=pitch_color,
        margin=dict(l=10, r=10, t=44, b=18),
        height=540,
        xaxis=dict(range=[0, 120], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[80, 0], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        showlegend=False,
        legend=dict(title="", bgcolor="rgba(255,255,255,0)", font=dict(color="#111827", size=11), orientation="h", y=-0.14, x=0),
        font=dict(color="#111827", size=13),
    )
    return fig


def create_pitch_scatter(
    events: pd.DataFrame,
    color_by_action: bool = True,
    title: str = "Mapa de eventos no campo",
    max_points: int = 6000,
) -> go.Figure:
    frame = events.dropna(subset=["x", "y"]).copy()
    if len(frame) > max_points:
        frame = frame.sample(max_points, random_state=7)
    fig = _base_pitch_figure(title)

    if frame.empty:
        fig.add_annotation(text="Sem eventos com coordenadas para os filtros atuais.", x=60, y=40, showarrow=False)
        return fig

    if color_by_action:
        for action, group in frame.groupby("action_type"):
            fig.add_trace(
                go.Scatter(
                    x=group["x"],
                    y=group["y"],
                    mode="markers",
                    name=action_label(action),
                    marker=dict(
                        size=7,
                        color=action_color(action),
                        opacity=0.86,
                        line=dict(color="#ffffff", width=0.9),
                    ),
                    showlegend=False,
                    customdata=np.stack([group["team_name"].map(team_label), group["player_name"]], axis=1),
                    hovertemplate="Acao: %{fullData.name}<br>Time: %{customdata[0]}<br>Jogador: %{customdata[1]}<br>x=%{x:.1f} y=%{y:.1f}<extra></extra>",
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=frame["x"],
                y=frame["y"],
                mode="markers",
                name="Eventos",
                marker=dict(size=7, color="#ffdd57", opacity=0.9, line=dict(color="#ffffff", width=0.9)),
                showlegend=False,
                customdata=np.stack([frame["action_type"].map(action_label), frame["team_name"].map(team_label)], axis=1),
                hovertemplate="Acao: %{customdata[0]}<br>Time: %{customdata[1]}<br>x=%{x:.1f} y=%{y:.1f}<extra></extra>",
            )
        )

    return fig


def create_zone_heatmap(zone_counts: pd.DataFrame, title: str = "Mapa agregado por zonas") -> go.Figure:
    heatmap_data = []
    for zone_name, bounds in FIELD_ZONES.items():
        x0, x1, y0, y1 = bounds
        count_row = zone_counts.loc[zone_counts["zone"] == zone_name, "event_count"]
        count = int(count_row.iloc[0]) if not count_row.empty else 0
        heatmap_data.append({"zone": zone_name, "x_center": (x0 + x1) / 2, "y_center": (y0 + y1) / 2, "count": count})

    heatmap_df = pd.DataFrame(heatmap_data)
    fig = _base_pitch_figure(title)
    fig.add_trace(
        go.Scatter(
            x=heatmap_df["x_center"],
            y=heatmap_df["y_center"],
            mode="markers+text",
            text=heatmap_df["count"].astype(str),
            textposition="middle center",
            marker=dict(
                size=42,
                color=heatmap_df["count"],
                colorscale="YlOrRd",
                opacity=0.9,
                colorbar=dict(title="Eventos"),
                line=dict(color="#111111", width=1),
            ),
            customdata=heatmap_df["zone"],
            hovertemplate="Zona: %{customdata}<br>Eventos: %{text}<extra></extra>",
        )
    )
    return fig


def create_zone_metric_heatmap(
    zone_values: pd.DataFrame,
    value_col: str,
    title: str,
    colorbar_title: str = "Valor",
    value_format: str = "decimal2",
) -> go.Figure:
    heatmap_data = []
    for zone_name, bounds in FIELD_ZONES.items():
        x0, x1, y0, y1 = bounds
        value_row = zone_values.loc[zone_values["zone"] == zone_name, value_col]
        value = float(value_row.iloc[0]) if not value_row.empty and pd.notna(value_row.iloc[0]) else 0.0
        heatmap_data.append(
            {"zone": zone_name, "x_center": (x0 + x1) / 2, "y_center": (y0 + y1) / 2, "value": value}
        )

    heatmap_df = pd.DataFrame(heatmap_data)
    if value_format == "percent":
        text_values = heatmap_df["value"].map(lambda value: f"{value:.1%}")
    elif value_format == "decimal4":
        text_values = heatmap_df["value"].map(lambda value: f"{value:.4f}")
    elif value_format == "integer":
        text_values = heatmap_df["value"].map(lambda value: f"{value:.0f}")
    else:
        text_values = heatmap_df["value"].map(lambda value: f"{value:.2f}")
    fig = _base_pitch_figure(title)
    fig.add_trace(
        go.Scatter(
            x=heatmap_df["x_center"],
            y=heatmap_df["y_center"],
            mode="markers+text",
            text=text_values,
            textposition="middle center",
            marker=dict(
                size=48,
                color=heatmap_df["value"],
                colorscale="Viridis",
                opacity=0.92,
                colorbar=dict(title=colorbar_title),
                line=dict(color="#111111", width=1),
            ),
            customdata=heatmap_df["zone"],
            hovertemplate="Zona: %{customdata}<br>Valor: %{text}<extra></extra>",
        )
    )
    return fig


def create_thirds_probability_pitch(third_summary: pd.DataFrame, title: str = "Campo por tercos") -> go.Figure:
    fig = _base_pitch_figure(title)
    colors = {"Defesa": "rgba(56, 189, 248, 0.33)", "Meio": "rgba(245, 158, 11, 0.33)", "Ataque": "rgba(0, 194, 122, 0.33)"}

    for third_name, (x0, x1) in FIELD_THIRDS.items():
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=0,
            y1=80,
            fillcolor=colors.get(third_name, "rgba(255,255,255,0.12)"),
            line=dict(color="#f7f3e9", width=2, dash="dot"),
            layer="below",
        )
        row = third_summary[third_summary["field_third"] == third_name]
        if row.empty:
            text = f"<b>{third_name}</b><br>Sem dados"
            hover = text
        else:
            item = row.iloc[0]
            text = (
                f"<b>{third_name}</b><br>"
                f"{item['current_action']} -> {item['next_action']}<br>"
                f"{item['probability']:.1%}<br>"
                f"Var. xG evento seg. {item['xg_delta_medio']:+.3f}"
            )
            hover = (
                f"Tercio: {third_name}<br>Acao mais provavel: {item['current_action']} -> {item['next_action']}"
                f"<br>Probabilidade: {item['probability']:.1%}<br>Variacao xG evento seguinte: {item['xg_delta_medio']:+.3f}"
            )
        fig.add_trace(
            go.Scatter(
                x=[(x0 + x1) / 2],
                y=[40],
                mode="markers+text",
                marker=dict(size=34, color="#111827", opacity=0.72, line=dict(color="#f7f3e9", width=1)),
                text=[text],
                textposition="middle center",
                hovertemplate=hover + "<extra></extra>",
                showlegend=False,
            )
        )
    return fig


def create_transition_heatmap(matrix: pd.DataFrame, title: str) -> go.Figure:
    if matrix.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="YlGnBu",
        labels=dict(x="Proxima acao", y="Acao atual", color="Prob."),
        title=title,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#111827", size=13),
        title=dict(font=dict(color="#111827", size=18)),
        xaxis=dict(tickangle=-20, automargin=True),
        yaxis=dict(automargin=True),
        height=max(520, min(900, 28 * len(matrix.index) + 180)),
    )
    return fig


def create_action_bar_chart(frame: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    text_template, tick_format = _vertical_value_formats(frame[y_col]) if y_col in frame.columns else ("%{y:.2f}", ".2f")
    fig = px.bar(
        frame,
        x=x_col,
        y=y_col,
        title=title,
        color=y_col,
        color_continuous_scale="Tealgrn",
        text=y_col,
    )
    fig.update_traces(texttemplate=text_template, textposition="outside", cliponaxis=False)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=36, r=28, t=56, b=28),
        coloraxis_showscale=False,
        font=dict(color="#111827", size=13),
        title=dict(font=dict(color="#111827", size=18)),
        xaxis=dict(tickangle=-20, automargin=True),
        yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#9ca3af", zerolinewidth=2, tickformat=tick_format, automargin=True),
        height=500,
    )
    if y_col in frame.columns:
        _pad_vertical_axis(fig, frame[y_col])
    return fig


def create_similarity_heatmap(similarity: pd.DataFrame) -> go.Figure:
    if similarity.empty:
        return go.Figure()

    fig = px.imshow(
        similarity,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        zmin=0,
        zmax=1,
        labels=dict(x="Selecao", y="Selecao", color="Similaridade"),
        title="Similaridade de cosseno entre selecoes",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#111827", size=13),
        title=dict(font=dict(color="#111827", size=18)),
    )
    return fig


def create_comparison_bar_chart(frame: pd.DataFrame, color_col: str, value_col: str, facet_col: str, title: str) -> go.Figure:
    if frame.empty:
        return go.Figure()

    text_template, tick_format = _vertical_value_formats(frame[value_col]) if value_col in frame.columns else ("%{y:.2f}", ".2f")
    fig = px.bar(
        frame,
        x=facet_col,
        y=value_col,
        color=color_col,
        barmode="group",
        title=title,
        color_discrete_sequence=["#ff6b1a", "#00c27a", "#38bdf8"],
        text=value_col,
    )
    fig.update_traces(texttemplate=text_template, textposition="outside", cliponaxis=False)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(bgcolor="rgba(255,255,255,0)", font=dict(color="#111827", size=12)),
        font=dict(color="#111827", size=13),
        title=dict(font=dict(color="#111827", size=18)),
        xaxis_title="",
        yaxis_title="Valor",
        xaxis=dict(tickangle=-20, automargin=True),
        yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#9ca3af", zerolinewidth=2, tickformat=tick_format),
        height=500,
    )
    if value_col in frame.columns:
        _pad_vertical_axis(fig, frame[value_col])
    return fig


def create_metric_strip(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return go.Figure()

    text_template, tick_format = _vertical_value_formats(frame["value"])
    fig = go.Figure(
        go.Bar(
            x=frame["label"],
            y=frame["value"],
            marker=dict(color=["#ff6b1a", "#f59e0b", "#00c27a", "#38bdf8", "#ef4444"]),
            text=frame["value"],
            textposition="outside",
            texttemplate=text_template,
            cliponaxis=False,
        )
    )
    fig.update_layout(
        title=dict(text="Painel rapido da base", font=dict(color="#111827", size=18)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=36, r=28, t=56, b=28),
        xaxis_title="",
        yaxis_title="Volume",
        yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#9ca3af", zerolinewidth=2, tickformat=tick_format, automargin=True),
        font=dict(color="#111827", size=13),
        height=500,
    )
    _pad_vertical_axis(fig, frame["value"])
    return fig


def style_metric_delta(value: float) -> str:
    return f"{value:+.2%}"
