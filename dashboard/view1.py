import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_float import float_init, float_parent

MAP_HEIGHT = 700

# ─────────────────────────────────────────
# COLOR SCHEME
# ─────────────────────────────────────────

TAPIO_COLORS = {
    # GDP Growing — vivid
    "absolute_decoupling":           "#2D5A27",
    "relative_decoupling":           "#A8C5A0",
    "expansive_coupling":            "#E8A87C",
    "expansive_negative_decoupling": "#C4623A",
    # GDP Contracting — muted
    "recessive_decoupling":          "#A8C5A0",  # matches relative_decoupling
    "recessive_coupling":            "#E8A87C",  # matches expansive_coupling
    "strong_negative_decoupling":    "#C4623A",  # matches expansive_negative_decoupling
    # No data
    "undefined":                     "#D9D9D9",
}

# Per-category colorscales: [light_color, dark_color]
# Direction: "higher E = lighter" for growth categories (worse = washed out)
#            follows same logic for contraction categories
TAPIO_COLORSCALES = {
    "absolute_decoupling":           ["#4A8A42", "#1A3D15"],  # light→dark green (more negative = darker)
    "relative_decoupling":           ["#D4EAD0", "#6B9E65"],  # light→dark sage
    "expansive_coupling":            ["#F5CBA7", "#C47B30"],  # light→dark orange
    "expansive_negative_decoupling": ["#E8A07A", "#7A2010"],  # light→dark terracotta
    "recessive_decoupling":          ["#CFE3CB", "#6B9E65"],  # own range, sage family (visually paired with relative_decoupling)
    "recessive_coupling":            ["#F0C295", "#C47B30"],  # own range, orange family (visually paired with expansive_coupling)
    "strong_negative_decoupling":    ["#E29B76", "#7A2010"],  # own range, terracotta family (visually paired with expansive_negative_decoupling)
    "undefined":                     ["#D9D9D9", "#D9D9D9"],
}

# Clamp ranges for E values (p5/p95 based to avoid outliers)
# Format: (min_e, max_e) — value is normalized 0→1 within this range
TAPIO_CLAMP = {
    "absolute_decoupling":           (-5.0,  0.0),   # more negative = more decoupled
    "relative_decoupling":           ( 0.0,  0.8),
    "expansive_coupling":            ( 0.8,  1.2),
    "expansive_negative_decoupling": ( 1.2, 10.0),
    "recessive_decoupling":          ( 1.2, 23.0),
    "recessive_coupling":            ( 0.0,  1.2),
    "strong_negative_decoupling":    (-20.0, 0.0),
    "undefined":                     ( 0.0,  1.0),
}

CATEGORY_ORDER = [
    "absolute_decoupling", "relative_decoupling", "expansive_coupling",
    "expansive_negative_decoupling", "recessive_decoupling", 
    "recessive_coupling", "strong_negative_decoupling", "undefined",
]

LEGEND_ITEMS = {
    "GDP GROWING": [
        ("absolute_decoupling",           "Absolute Decoupling",           "GDP↑, emissions↓ (best case)"),
        ("relative_decoupling",           "Relative Decoupling",           "GDP↑, emissions↑ but slower than GDP"),
        ("expansive_coupling",            "Expansive Coupling",            "GDP↑, emissions↑ at same rate"),
        ("expansive_negative_decoupling", "Expansive Negative Decoupling", "GDP↑, emissions↑ faster than GDP"),
    ],
    "GDP CONTRACTING": [
        ("recessive_decoupling",          "Recessive Decoupling",          "GDP↓, emissions↓ even faster — interpret with caution"),
        ("recessive_coupling",            "Recessive Coupling",            "GDP↓, emissions↓ at same rate"),
        ("strong_negative_decoupling",    "Strong Negative Decoupling",    "GDP↓, emissions↑ (worst case)"),
    ],
    "OTHER": [
        ("undefined",                     "No Data",                       "Insufficient data to classify"),
    ],
}

def build_legend_html() -> str:
    sections = []
    for section_title, items in LEGEND_ITEMS.items():
        rows = []
        for key, name, desc in items:
            light, dark = TAPIO_COLORSCALES[key]
            # No indentation here: keeps Streamlit from rendering it as a <pre> block
            rows.append(f"""<div style="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px;">
<div style="min-width:14px; flex-shrink:0; margin-top:2px;">
<div style="width:14px; height:32px; border-radius:3px; background:linear-gradient(to bottom, {dark}, {light});"></div>
</div>
<div>
<div style="font-weight:600; font-size:12px; color:#1a1a1a;">{name}</div>
<div style="font-size:10px; color:#555; margin-top:1px; line-height:1.2;">{desc}</div>
</div>
</div>""")

        sections.append(f"""<div style="margin-bottom:16px;">
<div style="font-size:11px; font-weight:700; letter-spacing:0.08em; color:#888; text-transform:uppercase; margin-bottom:10px;">
{section_title}
</div>
{"".join(rows)}
</div>""")

    divider = '<hr style="border:none; border-top:1px solid #e0e0e0; margin:14px 0;">'
    return f"""<div style="font-family:sans-serif; height: 100%;">
<div style="font-size:12px; font-weight:800; letter-spacing:0.06em; text-transform:uppercase; color:#333; margin-bottom:14px;">
DECOUPLING STATUS
</div>
{divider.join(sections)}
</div>"""

def build_map(year_data: pd.DataFrame, tapio_col: str = "tapio_class", fogged: bool = False) -> go.Figure:
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"
    fig = go.Figure()

    base_opacity = 0.25 if fogged else 1.0

    for class_key in CATEGORY_ORDER:
        subset = year_data[year_data[tapio_col] == class_key].copy()
        if subset.empty:
            continue

        label, description = next(
            ((name, desc) for items in LEGEND_ITEMS.values()
             for k, name, desc in items if k == class_key),
            (class_key, "")
        )

        e_min, e_max = TAPIO_CLAMP[class_key]
        e_vals = subset[e_col].fillna((e_min + e_max) / 2).clip(e_min, e_max)
        if e_max != e_min:
            z_vals = (e_vals - e_min) / (e_max - e_min)
        else:
            z_vals = pd.Series([0.5] * len(subset))

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
                "<span style='font-size:11px; color:#666;'>%{customdata[5]}</span><br>"
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
                description=description,
            )[["country", "tapio_class_label", "gdp_pct_change", "ghg_pct_change", "e_val", "description"]].values,
            marker_line_color="rgba(0, 0, 0, 0.5)",
            marker_line_width=0.5,
            marker_opacity=base_opacity
        ))

    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True, coastlinecolor="rgba(0,0,0,0.3)",
        showcountries=True,  countrycolor="rgba(0,0,0,0.3)",
        showland=True,       landcolor="#f0ede8",
        showocean=True,      oceancolor="#eef7fa",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-55, 85],
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=MAP_HEIGHT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )

    return fig

def build_view(historical_df: pd.DataFrame, show_pm25: bool):
    smoothing = st.session_state.get("smoothing_v1", "Annual")
    tapio_col = "tapio_class" if smoothing == "Annual" else "tapio_class_5yr"

    if show_pm25:
        min_year = max(2000, int(historical_df["year"].min()))
        max_year = min(2020, int(historical_df["year"].max()))
    else:
        min_year = int(historical_df["year"].min())
        max_year = int(historical_df["year"].max())

    selected_year = st.session_state.get("slider_v1", max_year)
    selected_year = min(max(selected_year, min_year), max_year)

    year_data = historical_df[historical_df["year"] == selected_year].copy()
    fig = build_map(year_data, tapio_col, fogged=show_pm25)

    return fig, year_data, tapio_col, selected_year, min_year, max_year

def render_floating_controls(min_year: int, max_year: int, show_pm25: bool) -> bool:
    
    # Initialize the javascript float logic
    float_init()

    # 1. Top Left Control Panel
    controls_panel = st.container(key="v1_controls_panel")
    with controls_panel:
        toggle_col1, toggle_col2 = st.columns([3, 1])
        with toggle_col1:
            st.markdown("<p style='font-size:14px; margin:6px 0 0; font-weight: 500;'>Air Quality</p>", unsafe_allow_html=True)
        with toggle_col2:
            new_show_pm25 = st.toggle("Air Quality", key="pm25_toggle", label_visibility="collapsed")
        
        st.markdown("<p style='font-size:12px; font-weight:600; margin:12px 0 4px;'>View mode</p>", unsafe_allow_html=True)
        st.radio(
            "View mode:",
            options=["Annual", "5-year rolling average"],
            key="smoothing_v1",
            label_visibility="collapsed",
        )
        if new_show_pm25:
            st.markdown(
                "<p style='font-size:0.75rem; color:#888; margin-top:8px;'>⏳ Timeline restricted to 2000–2020</p>",
                unsafe_allow_html=True
            )
        
    # Floating with background color and borders directly applied
    controls_panel.float("position: absolute; top: 20px; left: 20px; width: 220px; background: rgba(255,255,255,0.95); border: 1px solid #d0d0d0; border-radius: 12px; padding: 14px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 999999;")

    # 2. Bottom Center Timeline Panel
    timeline_panel = st.container(key="v1_timeline_panel")
    with timeline_panel:
        st.slider(
            f"Timeline: {min_year} – {max_year}",
            min_value=min_year,
            max_value=max_year,
            value=min(st.session_state.get("slider_v1", max_year), max_year),
            step=1,
            key="slider_v1",
            format="%d",
            label_visibility="visible",
        )
        
    # Floating with background color and borders directly applied
    timeline_panel.float("position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); width: 50%; min-width: 320px; background: rgba(255,255,255,0.95); border: 1px solid #d0d0d0; border-radius: 12px; padding: 10px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 999999;")

    return new_show_pm25

def render_legend():
    """Renders the markdown legend cleanly in a floating container."""
    legend_panel = st.container(key="v1_legend_panel")
    with legend_panel:
        st.markdown(build_legend_html(), unsafe_allow_html=True)
        
    # Floating with background color and borders directly applied
    legend_panel.float("position: absolute; top: 20px; right: 20px; width: 260px; background: rgba(255,255,255,0.95); border: 1px solid #d0d0d0; border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 999999;")

def render_map_frame_css():
    """Injects CSS to set the map's boundary, with a robust fallback for the floating elements."""
    st.markdown(f"""
        <style>
        /* Map frame styling: position relative anchors the floating children! */
        div.st-key-v1_map_frame {{
            position: relative !important;
            height: {MAP_HEIGHT}px !important;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #d0d0d0;
            background: #eef7fa;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }}
        
        div.st-key-v1_map_frame > div {{ gap: 0 !important; padding: 0 !important; }}

        /* Clean up slider styling */
        [data-testid="stSlider"] .st-emotion-cache-1xp7nia {{ color: #2D5A27; }}
        [data-testid="stSlider"] [role="slider"] {{ background-color: #2D5A27; box-shadow: 0 0 0 0.2rem rgba(45,90,39,0.2); }}
        [data-testid="stSlider"] .st-bq {{ background-color: #2D5A27; }}
        </style>
    """, unsafe_allow_html=True)