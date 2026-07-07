import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from style import COLORS, FONT_MONO

# ─────────────────────────────────────────
# COLOR SCHEME (Tapio decoupling palette — tuned to read against a dark map)
# ─────────────────────────────────────────

TAPIO_COLORS = {
    "absolute_decoupling":           "#3FA843",
    "relative_decoupling":           "#9ECB92",
    "expansive_coupling":            "#E8A87C",
    "expansive_negative_decoupling": "#D2603E",
    "recessive_decoupling":          "#7FAE8A",
    "recessive_coupling":            "#C7B18F",
    "strong_negative_decoupling":    "#B0715A",
    "undefined":                     "#C7CCD0",
}

TAPIO_COLORSCALES = {
    "absolute_decoupling":           ["#5FCB63", "#1F5A23"],
    "relative_decoupling":           ["#CFEAC7", "#6FA466"],
    "expansive_coupling":            ["#F6CBA0", "#C87A3B"],
    "expansive_negative_decoupling": ["#EE9270", "#8A2A14"],
    "recessive_decoupling":          ["#B9D6BF", "#4F7F5C"],
    "recessive_coupling":            ["#E1D3B4", "#8E7048"],
    "strong_negative_decoupling":    ["#CC9A80", "#5C2A1B"],
    "undefined":                     ["#C7CCD0", "#C7CCD0"],
}

TAPIO_CLAMP = {
    "absolute_decoupling":           (-5.0,  0.0),
    "relative_decoupling":           ( 0.0,  0.8),
    "expansive_coupling":            ( 0.8,  1.2),
    "expansive_negative_decoupling": ( 1.2, 10.0),
    "recessive_decoupling":          ( 1.2, 23.0),
    "recessive_coupling":            ( 0.0,  1.2),
    "strong_negative_decoupling":    (-20.0, 0.0),
    "undefined":                     ( 0.0,  1.0),
}

CATEGORY_ORDER = [
    "absolute_decoupling",
    "relative_decoupling",
    "expansive_coupling",
    "expansive_negative_decoupling",
    "recessive_decoupling",
    "recessive_coupling",
    "strong_negative_decoupling",
    "undefined",
]

LEGEND_ITEMS = {
    "GDP GROWING": [
        ("absolute_decoupling",           "Absolute decoupling",           "GDP ↑, emissions ↓ — the best case"),
        ("relative_decoupling",           "Relative decoupling",           "GDP ↑, emissions ↑ slower than GDP"),
        ("expansive_coupling",            "Expansive coupling",            "GDP ↑, emissions ↑ at the same rate"),
        ("expansive_negative_decoupling", "Expansive negative decoupling", "GDP ↑, emissions ↑ faster than GDP"),
    ],
    "GDP CONTRACTING": [
        ("recessive_decoupling",          "Recessive decoupling",          "GDP ↓, emissions ↓ even faster"),
        ("recessive_coupling",            "Recessive coupling",            "GDP ↓, emissions ↓ at the same rate"),
        ("strong_negative_decoupling",    "Strong negative decoupling",    "GDP ↓, emissions ↑ — the worst case"),
    ],
    "OTHER": [
        ("undefined", "No data", "Insufficient data to classify"),
    ],
}


# ─────────────────────────────────────────
# MAP
# ─────────────────────────────────────────

def build_map(year_data: pd.DataFrame, tapio_col: str = "tapio_class", fogged: bool = False) -> go.Figure:
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"
    fig = go.Figure()
    base_opacity = 0.32 if fogged else 1.0

    for class_key in CATEGORY_ORDER:
        subset = year_data[year_data[tapio_col] == class_key].copy()
        if subset.empty:
            continue

        label = next(
            (name for items in LEGEND_ITEMS.values()
             for k, name, _ in items if k == class_key),
            class_key
        )

        e_min, e_max = TAPIO_CLAMP[class_key]
        e_vals = subset[e_col].fillna((e_min + e_max) / 2).clip(e_min, e_max)
        z_vals = (e_vals - e_min) / (e_max - e_min) if e_max != e_min else pd.Series([0.5] * len(subset))
        if class_key in ("absolute_decoupling", "strong_negative_decoupling"):
            z_vals = 1 - z_vals

        colorscale = [
            [0.0, TAPIO_COLORSCALES[class_key][0]],
            [1.0, TAPIO_COLORSCALES[class_key][1]],
        ]

        fig.add_trace(go.Choropleth(
            locations=subset["iso3"],
            z=z_vals.values,
            zmin=0, zmax=1,
            colorscale=colorscale,
            showscale=False,
            showlegend=False,
            name=label,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Status: %{customdata[1]}<br>"
                "GDP change: %{customdata[2]}%<br>"
                "GHG change: %{customdata[3]}%<br>"
                f"{'Tapio E (5yr avg)' if tapio_col == 'tapio_class_5yr' else 'Tapio E (annual)'}: %{{customdata[4]}}<br>"
                "<extra></extra>"
            ),
            customdata=subset.assign(
                tapio_class_label=subset[tapio_col].str.replace("_", " ").str.title(),
                gdp_pct_change=subset["gdp_pct_change"].round(2),
                ghg_pct_change=subset["ghg_pct_change"].round(2),
                e_val=subset[e_col].round(3),
            )[["country", "tapio_class_label", "gdp_pct_change", "ghg_pct_change", "e_val"]].values,
            marker_line_color="rgba(15,23,31,0.18)",
            marker_line_width=0.4,
            marker_opacity=base_opacity,
        ))

    fig.update_geos(
        projection_type="miller",
        showcoastlines=True, coastlinecolor=COLORS["land_line"],
        showland=True,       landcolor=COLORS["land"],
        showocean=True,      oceancolor=COLORS["ocean"],
        showlakes=False,
        showcountries=True, countrycolor="rgba(15,23,31,0.07)",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85],
        lonaxis_range=[-180, 180],
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(
            bgcolor=COLORS["panel_solid"],
            bordercolor=COLORS["hairline"],
            font=dict(family="Inter", color=COLORS["text"], size=12),
        ),
        dragmode="pan",
    )

    return fig


# ─────────────────────────────────────────
# CONTROLS (return state only — rendering happens in app.py's HUD docks)
# ─────────────────────────────────────────

def build_view(historical_df: pd.DataFrame, show_pm25: bool, smoothing_label: str, selected_year: int):
    """Pure function: given current control state, build the figure + filtered slice."""
    tapio_col = "tapio_class" if smoothing_label == "Annual" else "tapio_class_5yr"
    year_data = historical_df[historical_df["year"] == selected_year].copy()
    fig = build_map(year_data, tapio_col, fogged=show_pm25)
    return fig, year_data, tapio_col


def year_bounds(historical_df: pd.DataFrame, show_pm25: bool):
    if show_pm25:
        min_year = max(2000, int(historical_df["year"].min()))
        max_year = min(2020, int(historical_df["year"].max()))
    else:
        min_year = int(historical_df["year"].min())
        max_year = int(historical_df["year"].max())
    return min_year, max_year


def default_analysis_year(historical_df: pd.DataFrame, coverage_floor: float = 0.8) -> int:
    """Pick a sensible default year for the initial map view.

    The absolute latest year in the panel is usually the *worst* default:
    GDP figures (World Bank) commonly lag 1-2 years behind for many
    countries, so the final year or two often has far fewer countries
    reporting than the panel's peak coverage -- which is exactly what makes
    a freshly-loaded map look like "half the world is missing". This picks
    the most recent year whose row count is still at least
    `coverage_floor` (default 80%) of the panel's best year, so the initial
    view is both recent and actually populated. The person can still drag
    the slider to any year, including the sparser recent ones.
    """
    counts = historical_df.groupby("year").size()
    if counts.empty:
        return int(historical_df["year"].max())
    threshold = counts.max() * coverage_floor
    well_covered_years = counts[counts >= threshold].index
    return int(well_covered_years.max())


# ─────────────────────────────────────────
# HUD RENDERERS
# ─────────────────────────────────────────

def render_legend_hud():
    """Compact legend rendered inline inside the floating right HUD panel."""
    rows_html = []
    for section_title, items in LEGEND_ITEMS.items():
        rows = []
        for key, name, desc in items:
            light, dark = TAPIO_COLORSCALES[key]
            rows.append(f"""
                <div style="display:flex; align-items:flex-start; gap:9px; margin-bottom:8px;">
                    <div style="width:13px; height:30px; border-radius:3px; flex-shrink:0; margin-top:1px;
                                background:linear-gradient(to bottom, {dark}, {light});
                                border:1px solid rgba(15,23,31,0.10);"></div>
                    <div>
                        <div style="font-size:0.76rem; font-weight:600; color:{COLORS['text']};">{name}</div>
                        <div style="font-size:0.66rem; color:{COLORS['text_dim']}; margin-top:1px; line-height:1.3;">{desc}</div>
                    </div>
                </div>
            """)
        rows_html.append(f"""
            <div class="hud-label" style="margin-bottom:6px;">{section_title}</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px 10px; margin-bottom:10px;">
                {''.join(cells)}
            </div>
            <hr class="hud-divider" style="margin:6px 0;">
        """)

    st.html(f"""
        <div style="padding:14px 16px 2px 16px;">
        {''.join(rows_html)}
        </div>
    """)


def render_country_stat(year_data: pd.DataFrame, tapio_col: str, selected_year: int, iso3: str | None):
    """Small stat readout for a single hovered/selected country — falls back to a global summary."""
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"

    if iso3 and iso3 in year_data["iso3"].values:
        row = year_data[year_data["iso3"] == iso3].iloc[0]
        st.html(f"""
            <div style="padding:14px 16px;">
                <div class="hud-label">SELECTED</div>
                <div style="font-family:'Space Grotesk'; font-size:1.05rem; font-weight:600; color:{COLORS['text']}; margin:2px 0 10px 0;">
                    {row['country']}
                </div>
            </div>
        """)
    else:
        counts = year_data[tapio_col].value_counts()
        n_decoupled = int(counts.get("absolute_decoupling", 0) + counts.get("relative_decoupling", 0))
        n_total = int(year_data[tapio_col].notna().sum())
        pct = (n_decoupled / n_total * 100) if n_total else 0
        st.html(f"""
            <div style="padding:14px 16px 4px 16px;">
                <div class="hud-label">{selected_year} SNAPSHOT</div>
                <div style="font-family:'Space Grotesk'; font-size:1.6rem; font-weight:700; color:{COLORS['accent']}; margin:4px 0 0 0;">
                    {pct:.0f}%
                </div>
                <div style="font-size:0.72rem; color:{COLORS['text_dim']}; margin-bottom:10px;">
                    of tracked countries are decoupling growth from emissions
                </div>
            </div>
            <hr class="hud-divider" style="margin:0 16px 8px 16px;">
        """)


def render_data_table(year_data: pd.DataFrame, tapio_col: str, selected_year: int):
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"
    e_label = "Tapio E (annual)" if tapio_col == "tapio_class" else "Tapio E (5yr avg)"

    with st.expander(f"Full country table — {selected_year}", icon=":material/table_rows:"):
        display_df = year_data[["country", tapio_col, "gdp_pct_change", "ghg_pct_change", e_col]].copy()
        display_df.columns = ["Country", "Decoupling status", "GDP % change", "GHG % change", e_label]
        display_df["Decoupling status"] = display_df["Decoupling status"].astype(str).str.replace("_", " ").str.title()
        st.dataframe(display_df.set_index("Country").dropna(how="all"), width="stretch")