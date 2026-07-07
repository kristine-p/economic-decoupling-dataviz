import pandas as pd
import plotly.graph_objects as go

from style import COLORS

# WHO-style air-quality progression: clean → hazardous.
# Deliberately distinct from the Tapio (green/orange/terracotta) palette so
# the two data layers never get visually confused when both are on screen.
HAZE_COLORSCALE = [
    [0.00, "#F4E9C1"],   # clean
    [0.25, "#F2C879"],
    [0.50, "#E8934A"],
    [0.75, "#C85A3E"],
    [1.00, "#7A2033"],   # hazardous
]

WHO_THRESHOLD = 5.0   # µg/m³ guideline
CMAX = 35.0            # clamp so a few extreme outliers don't wash out the scale


def add_pm25_overlay(fig: go.Figure, regional_year_data: pd.DataFrame) -> go.Figure:
    """Overlay regional PM2.5 as a soft, layered haze of bubbles on View 1's map."""

    pm25_data = regional_year_data.dropna(subset=["pm25_ugm3", "lat", "lon"]).copy()
    if pm25_data.empty:
        return fig

    pm25_data["pm25_clamped"] = pm25_data["pm25_ugm3"].clip(upper=CMAX)

    # ---- soft outer glow pass (wide, translucent, no border) ----
    fig.add_trace(go.Scattergeo(
        lat=pm25_data["lat"], lon=pm25_data["lon"],
        mode="markers",
        marker=dict(
            size=pm25_data["pm25_clamped"],
            sizemode="area",
            sizeref=2. * 90 / (40. ** 2),
            sizemin=8,
            color=pm25_data["pm25_clamped"],
            colorscale=HAZE_COLORSCALE,
            cmin=0, cmax=CMAX,
            showscale=False,
            opacity=0.16,
            line=dict(width=0),
        ),
        hoverinfo="skip",
        showlegend=False,
        name="",
    ))

    # ---- solid core pass (the readable data point) ----
    fig.add_trace(go.Scattergeo(
        lat=pm25_data["lat"], lon=pm25_data["lon"],
        mode="markers",
        marker=dict(
            size=pm25_data["pm25_clamped"],
            sizemode="area",
            sizeref=2. * 40 / (40. ** 2),
            sizemin=4,
            color=pm25_data["pm25_clamped"],
            colorscale=HAZE_COLORSCALE,
            cmin=0, cmax=CMAX,
            showscale=True,
            colorbar=dict(
                title=dict(text="PM2.5<br>µg/m³", font=dict(size=11, color=COLORS["text_dim"], family="Inter")),
                thickness=10,
                len=0.34,
                x=0.015, y=0.22,
                xanchor="left",
                tickfont=dict(size=10, color=COLORS["text_dim"], family="JetBrains Mono"),
                outlinewidth=0,
                bgcolor="rgba(0,0,0,0)",
                tickvals=[0, WHO_THRESHOLD, 15, 25, 35],
                ticktext=["0", "WHO 5", "15", "25", "35+"],
            ),
            line=dict(color="rgba(8,10,12,0.55)", width=0.6),
            opacity=0.92,
        ),
        name="Regional PM2.5",
        customdata=pm25_data[["region_name", "country", "pm25_ugm3"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}<br>"
            "PM2.5: %{customdata[2]:.1f} µg/m³"
            "<extra></extra>"
        ),
    ))

    return fig