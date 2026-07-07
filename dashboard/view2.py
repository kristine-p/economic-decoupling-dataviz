import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
            showscale=False,
            line=dict(color="rgba(8,10,12,0.55)", width=0.6),
            opacity=0.92,
        ),
        showlegend=False,
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

def render_pm25_legend():
    """Custom HTML legend for the PM2.5 overlay layer, rendered in the left HUD."""
    gradient = ", ".join([f"{color} {pos*100}%" for pos, color in HAZE_COLORSCALE])
    st.html(f"""
        <div style="margin-top:24px;">
            <div class="hud-label" style="margin-bottom:8px;">PM2.5 (µg/m³)</div>
            <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono', monospace; font-size:0.65rem; color:{{COLORS['text_dim']}}; margin-bottom:4px;">
                <span>0</span>
                <span>{WHO_THRESHOLD} (WHO guideline)</span>
                <span>{CMAX}+</span>
            </div>
            <div style="height:12px; border-radius:4px; background:linear-gradient(to right, {gradient}); border:1px solid rgba(15,23,31,0.10);"></div>
        </div>
    """)