import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

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


# ─────────────────────────────────────────
# LEGEND HTML
# ─────────────────────────────────────────

def build_legend_html() -> str:
    sections = []
    for section_title, items in LEGEND_ITEMS.items():
        rows = []
        for key, name, desc in items:
            color = TAPIO_COLORS[key]
            light, dark = TAPIO_COLORSCALES[key]
            rows.append(f"""
                <div style="display:flex; align-items:flex-start; gap:6px; margin-bottom:6px;">
                    <div style="min-width:11px; flex-shrink:0; margin-top:2px;">
                        <div style="width:11px; height:26px; border-radius:2px;
                                    background:linear-gradient(to bottom, {dark}, {light});"></div>
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:11px; color:#1a1a1a;">{name}</div>
                        <div style="font-size:9px; color:#555; margin-top:1px; line-height:1.3;">{desc}</div>
                    </div>
                </div>
            """)

        sections.append(f"""
            <div style="margin-bottom:14px;">
                <div style="font-size:10px; font-weight:700; letter-spacing:0.08em;
                            color:#888; text-transform:uppercase; margin-bottom:10px;">
                    {section_title}
                </div>
                {"".join(rows)}
            </div>
        """)

    divider = '<hr style="border:none; border-top:1px solid #e0e0e0; margin:12px 0;">'

    return f"""
        <html>
        <body style="margin:0; padding:0; background:transparent; font-family:sans-serif;">
        <div style="border:1px solid #d0d0d0; border-radius:8px; padding:12px 14px; background:rgba(255,255,255,0.92); height: calc(100vh - 90px); max-height: 432px; overflow-y: auto; box-sizing: border-box;">
            <div style="font-size:11px; font-weight:700; letter-spacing:0.06em;
                        text-transform:uppercase; color:#333; margin-bottom:11px;">
                DECOUPLING STATUS
            </div>
            {divider.join(sections)}
        </div>
        </body>
        </html>
    """


# ─────────────────────────────────────────
# MAP
# ─────────────────────────────────────────

def build_map(year_data: pd.DataFrame, tapio_col: str = "tapio_class", fogged: bool = False) -> go.Figure:
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"
    fig = go.Figure()

    # If toggled ON, drop choropleth opacity to 30% to create the "fog" effect
    base_opacity = 0.3 if fogged else 1.0

    for class_key in CATEGORY_ORDER:
        subset = year_data[year_data[tapio_col] == class_key].copy()
        if subset.empty:
            continue

        label, description = next(
            ((name, desc) for items in LEGEND_ITEMS.values()
             for k, name, desc in items if k == class_key),
            (class_key, "")
        )

        # Normalize E values to 0→1 within clamped range
        e_min, e_max = TAPIO_CLAMP[class_key]
        e_vals = subset[e_col].fillna((e_min + e_max) / 2).clip(e_min, e_max)
        if e_max != e_min:
            z_vals = (e_vals - e_min) / (e_max - e_min)
        else:
            z_vals = pd.Series([0.5] * len(subset))

        # For absolute decoupling: more negative E = darker = better, so invert
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
            marker_line_color="rgba(255,255,255,0.4)",
            marker_line_width=0.5,
        ))

    fig.update_geos(
        projection_type="miller",
        showcoastlines=True, coastlinecolor="rgba(0,0,0,0.15)",
        showland=True,       landcolor="#f0ede8",
        showocean=True,      oceancolor="#ddeef5",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-58, 85],
        lonaxis_range=[-180, 180],
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=MAP_HEIGHT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )

    return fig


# ─────────────────────────────────────────
# RENDER CONTROLS & RETURN COMPONENTS
# ─────────────────────────────────────────
def build_view(historical_df: pd.DataFrame, show_pm25: bool):
    """Builds the base figure and returns it along with state; UI controls are rendered separately via render_floating_controls()."""

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

    # Pass 'fogged' parameter to map builder
    fig = build_map(year_data, tapio_col, fogged=show_pm25)

    return fig, year_data, tapio_col, selected_year, min_year, max_year


MAP_HEIGHT = 460


def render_floating_controls(min_year: int, max_year: int, show_pm25: bool) -> bool:
    """Renders the toggle/view-mode panel (top-left) and timeline (bottom-center),
    anchored via inset positioning against the .v1-map-frame wrapper so it stays
    correct regardless of map height."""

    with st.container(key="v1_controls_panel"):
        toggle_col1, toggle_col2 = st.columns([3, 1])
        with toggle_col1:
            st.markdown("<p style='font-size:13px; margin:6px 0 0;'>Air Quality</p>", unsafe_allow_html=True)
        with toggle_col2:
            new_show_pm25 = st.toggle("Air Quality", key="pm25_toggle", label_visibility="collapsed")
        st.markdown("<p style='font-size:11px; font-weight:600; margin:10px 0 4px;'>View mode</p>", unsafe_allow_html=True)
        st.radio(
            "View mode:",
            options=["Annual", "5-year rolling average"],
            key="smoothing_v1",
            label_visibility="collapsed",
        )
        if new_show_pm25:
            st.markdown(
                "<p style='font-size:0.7rem; color:#999; margin-top:6px;'>⏳ Timeline restricted to 2000–2020 (Air Quality data)</p>",
                unsafe_allow_html=True
            )

    with st.container(key="v1_timeline_panel"):
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

    return new_show_pm25


def render_legend():
    """Renders the HTML legend, anchored bottom-right via inset positioning."""
    with st.container(key="v1_legend_panel"):
        components.html(build_legend_html(), height=432, scrolling=False)


def render_map_frame_css():
    """Single CSS block defining the .v1-map-frame anchor and all floating panel
    positions as inset offsets. Call this once before rendering the frame contents."""
    st.markdown(f"""
        <style>
        .st-key-v1_map_frame {{
            position: relative;
            height: {MAP_HEIGHT}px;
        }}
        .st-key-v1_map_frame > div {{
            padding: 0 !important;
            margin: 0 !important;
            gap: 0 !important;
        }}
        .st-key-v1_controls_panel {{
            position: absolute;
            top: 14px;
            left: 14px;
            z-index: 10;
            width: 180px;
            max-height: 70%;
            overflow-y: auto;
            background: rgba(255,255,255,0.92);
            border: 1px solid #d0d0d0;
            border-radius: 10px;
            padding: 10px 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .st-key-v1_timeline_panel {{
            position: absolute;
            bottom: 14px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            width: 50%;
            min-width: 280px;
            background: #fff;
            border: 1px solid #d0d0d0;
            border-radius: 10px;
            padding: 8px 18px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .st-key-v1_legend_panel {{
            position: absolute;
            top: 14px;
            bottom: 14px;
            right: 14px;
            z-index: 10;
            width: 220px;
            max-height: calc(100% - 28px);
            overflow: hidden;
        }}
        .st-key-v1_legend_panel iframe {{
            border-radius: 10px;
        }}
        [data-testid="stSlider"] .st-emotion-cache-1xp7nia {{ color: #2D5A27; }}
        [data-testid="stSlider"] [role="slider"] {{ background-color: #2D5A27; }}
        [data-testid="stSlider"] .st-bq {{ background-color: #2D5A27; }}
        </style>
    """, unsafe_allow_html=True)


def render_data_table(year_data: pd.DataFrame, tapio_col: str, selected_year: int):
    """Renders the raw data table at the bottom of the page."""
    e_col = "tapio_E" if tapio_col == "tapio_class" else "tapio_E_5yr"
    e_label = "Tapio E (annual)" if tapio_col == "tapio_class" else "Tapio E (5yr avg)"
    
    with st.expander(f"📊 View Raw Data for {selected_year}"):
        display_df = year_data[["country", tapio_col, "gdp_pct_change", "ghg_pct_change", e_col]].copy()
        display_df.columns = ["Country", "Decoupling Status", "GDP % Change", "GHG % Change", e_label]
        display_df["Decoupling Status"] = display_df["Decoupling Status"].astype(str).str.replace("_", " ").str.title()
        st.dataframe(
            display_df.set_index("Country").dropna(how="all"),
            width="stretch"
        )