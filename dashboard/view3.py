import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from style import COLORS

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

# the map/compare-map color is driven by % change vs. the 1981-2010 baseline
# (see panel.py step 7) rather than the absolute projected day-count --
# a country with a naturally hot climate and a country with a naturally cold
# one can have wildly different absolute "hot days" counts while both are
# warming at a similar *relative* pace, which the absolute value obscures.
METRIC_COLS = {
    "Hot days":        "hot_days_proj_pct_change_1981_2010",
    "Tropical nights": "trop_nights_proj_pct_change_1981_2010",
    "Icing days":      "icing_days_proj_pct_change_1981_2010",
}
# the matching absolute projection, kept alongside for hover-tooltip context
METRIC_ABS_COLS = {
    "Hot days":        "hot_days_proj",
    "Tropical nights": "trop_nights_proj",
    "Icing days":      "icing_days_proj",
}
METRIC_ABS_UNITS = {
    "Hot days":        "days/yr ≥ 35°C",
    "Tropical nights": "nights/yr ≥ 20°C",
    "Icing days":      "days/yr < 0°C",
}
METRIC_UNITS = {
    "Hot days":        "% vs 1981–2010 avg",
    "Tropical nights": "% vs 1981–2010 avg",
    "Icing days":      "% vs 1981–2010 avg",
}

SCENARIO_ORDER = ["PROJ_SSP126", "PROJ_SSP245", "PROJ_SSP370", "PROJ_SSP585"]
SCENARIO_SHORT = {
    "PROJ_SSP126": "SSP1-2.6",
    "PROJ_SSP245": "SSP2-4.5",
    "PROJ_SSP370": "SSP3-7.0",
    "PROJ_SSP585": "SSP5-8.5",
}
SCENARIO_COLOR = {
    "PROJ_SSP126": "#4FBD8C",   # low emissions — cool green
    "PROJ_SSP245": "#E8C24A",   # middle of the road — amber
    "PROJ_SSP370": "#E8823D",   # high emissions — orange
    "PROJ_SSP585": "#C8483F",   # very high emissions — red
}

# diverging scale centered on 0% change -- cool blue for a decrease vs.
# baseline (e.g. fewer icing days), warm red for an increase (e.g. more hot
# days). Deliberately distinct from the Tapio and PM2.5 palettes used
# elsewhere, and different in *kind* (diverging, not sequential) from the
# old absolute-value map, since a % change can meaningfully go negative.
DIVERGING_SCALE = [
    [0.00, "#1E5C7A"],
    [0.25, "#6FA8C4"],
    [0.50, "#F1EEE8"],
    [0.75, "#E8935F"],
    [1.00, "#A8291F"],
]

LINKED_LABEL = "Current trajectory (linked)"


# ─────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────

def scenario_options():
    return [LINKED_LABEL] + [SCENARIO_SHORT[s] for s in SCENARIO_ORDER]


def _short_to_code(short_label: str) -> str:
    for code, short in SCENARIO_SHORT.items():
        if short == short_label:
            return code
    return None


def slice_for_scenario(climate_df: pd.DataFrame, year: int, scenario_label: str) -> pd.DataFrame:
    """Return one row per country for the given year + scenario selection."""
    year_df = climate_df[climate_df["year"] == year]
    if scenario_label == LINKED_LABEL:
        return year_df[year_df["is_linked_scenario"]].copy()
    code = _short_to_code(scenario_label)
    return year_df[year_df["scenario"] == code].copy()


def _symmetric_range(*series, floor=5.0):
    """Largest absolute value across the given series, so a diverging
    colorscale can be centered exactly on 0. `floor` avoids a degenerate
    (near-zero-width) range when the data barely moves either direction."""
    vals = [s.abs().max() for s in series if len(s.dropna())]
    return max([v for v in vals if pd.notna(v)] + [floor])


# ─────────────────────────────────────────
# MAP
# ─────────────────────────────────────────

def build_single_map(df: pd.DataFrame, metric_col: str, abs_col: str | None = None) -> go.Figure:
    df = df.dropna(subset=[metric_col]).copy()
    zmax = _symmetric_range(df[metric_col]) if len(df) else 5.0

    customdata_cols = ["country", metric_col] + ([abs_col] if abs_col and abs_col in df.columns else [])
    hover = "<b>%{customdata[0]}</b><br>%{customdata[1]:+.1f}% vs 1981–2010"
    if abs_col and abs_col in df.columns:
        hover += "<br>projected: %{customdata[2]:.1f}"
    hover += "<extra></extra>"

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=df["iso3"], z=df[metric_col],
        zmin=-zmax, zmax=zmax, zmid=0,
        colorscale=DIVERGING_SCALE,
        showscale=True,
        colorbar=dict(
            thickness=10, len=0.4, x=0.0, y=0.22, xanchor="left",
            ticksuffix="%",
            tickfont=dict(size=10, color=COLORS["text_dim"], family="JetBrains Mono"),
            outlinewidth=0, bgcolor="rgba(0,0,0,0)",
        ),
        marker_line_color="rgba(15,23,31,0.16)",
        marker_line_width=0.4,
        customdata=df[customdata_cols].values,
        hovertemplate=hover,
    ))
    _style_geo(fig)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def build_compare_map(df_left: pd.DataFrame, df_right: pd.DataFrame, metric_col: str,
                       label_left: str, label_right: str, abs_col: str | None = None) -> go.Figure:
    df_left = df_left.dropna(subset=[metric_col]).copy()
    df_right = df_right.dropna(subset=[metric_col]).copy()

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "choropleth"}, {"type": "choropleth"}]],
        subplot_titles=(label_left, label_right),
        horizontal_spacing=0.02,
    )
    # shared, zero-centered color range across both panels for a fair
    # visual comparison between the two scenarios
    zmax = _symmetric_range(df_left[metric_col], df_right[metric_col])

    customdata_cols = ["country", metric_col] + ([abs_col] if abs_col and abs_col in df_left.columns else [])
    hover = "<b>%{customdata[0]}</b><br>%{customdata[1]:+.1f}% vs 1981–2010"
    if abs_col and abs_col in df_left.columns:
        hover += "<br>projected: %{customdata[2]:.1f}"
    hover += "<extra></extra>"

    for df, c in ((df_left, 1), (df_right, 2)):
        fig.add_trace(
            go.Choropleth(
                locations=df["iso3"], z=df[metric_col],
                zmin=-zmax, zmax=zmax, zmid=0,
                colorscale=DIVERGING_SCALE,
                showscale=(c == 2),
                colorbar=dict(thickness=10, len=0.4, x=1.02, y=0.22,
                               ticksuffix="%",
                               tickfont=dict(size=10, color=COLORS["text_dim"], family="JetBrains Mono"),
                               outlinewidth=0, bgcolor="rgba(0,0,0,0)"),
                marker_line_color="rgba(15,23,31,0.16)", marker_line_width=0.4,
                customdata=df[customdata_cols].values,
                hovertemplate=hover,
            ),
            row=1, col=c,
        )

    geo_style = dict(
        projection_type="miller",
        showcoastlines=True, coastlinecolor=COLORS["land_line"],
        showland=True, landcolor=COLORS["land"],
        showocean=True, oceancolor=COLORS["ocean"],
        showframe=False, bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85], lonaxis_range=[-180, 180],
    )
    fig.update_geos(geo_style)
    fig.update_layout(
        margin={"r": 0, "t": 28, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color=COLORS["text_dim"], size=12),
        hoverlabel=dict(bgcolor=COLORS["panel_solid"], bordercolor=COLORS["hairline"],
                         font=dict(family="Inter", color=COLORS["text"], size=12)),
    )
    return fig


def _style_geo(fig):
    fig.update_geos(
        projection_type="miller",
        showcoastlines=True, coastlinecolor=COLORS["land_line"],
        showland=True, landcolor=COLORS["land"],
        showocean=True, oceancolor=COLORS["ocean"],
        showframe=False, bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85], lonaxis_range=[-180, 180],
    )
    fig.update_layout(
        hoverlabel=dict(bgcolor=COLORS["panel_solid"], bordercolor=COLORS["hairline"],
                         font=dict(family="Inter", color=COLORS["text"], size=12)),
    )


# ─────────────────────────────────────────
# COUNTRY TREND CHART (for the HUD side panel)
# ─────────────────────────────────────────

def build_trend_chart(climate_df: pd.DataFrame, iso3: str, metric_col: str) -> go.Figure:
    sub = climate_df[climate_df["iso3"] == iso3].sort_values("year")
    linked_code = sub.loc[sub["is_linked_scenario"], "scenario"].iloc[0] if sub["is_linked_scenario"].any() else None

    fig = go.Figure()
    fig.add_hline(y=0, line=dict(color=COLORS["text_faint"], width=1, dash="dot"))

    any_data = False
    for code in SCENARIO_ORDER:
        s = sub[sub["scenario"] == code].dropna(subset=[metric_col])
        if s.empty:
            continue
        any_data = True
        is_linked = (code == linked_code)
        fig.add_trace(go.Scatter(
            x=s["year"], y=s[metric_col],
            mode="lines",
            name=SCENARIO_SHORT[code] + (" · current trajectory" if is_linked else ""),
            line=dict(
                color=SCENARIO_COLOR[code],
                width=3 if is_linked else 1.4,
                dash="solid" if is_linked else "dot",
            ),
            opacity=1.0 if is_linked else 0.55,
            hovertemplate=f"{SCENARIO_SHORT[code]}<br>%{{x}}: %{{y:+.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        margin={"r": 8, "t": 8, "l": 8, "b": 8},
        height=190,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=10, color=COLORS["text_dim"]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.55, x=0, font=dict(size=9)),
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="rgba(15,23,31,0.08)", tickfont=dict(size=9), ticksuffix="%"),
        hoverlabel=dict(bgcolor=COLORS["panel_solid"], bordercolor=COLORS["hairline"],
                         font=dict(family="Inter", color=COLORS["text"], size=11)),
    )
    if not any_data:
        fig.add_annotation(
            text="No baseline-comparison data for this country",
            showarrow=False, font=dict(size=10, color=COLORS["text_faint"]),
            xref="paper", yref="paper", x=0.5, y=0.5,
        )
    return fig