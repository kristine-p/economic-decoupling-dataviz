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
    "recessive_decoupling":          "#8FAF8F",
    "recessive_coupling":            "#C4B49A",
    "strong_negative_decoupling":    "#A07060",
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
    "recessive_decoupling":          ["#C5D9C5", "#4A7A4A"],  # light→dark muted green
    "recessive_coupling":            ["#DDD0C0", "#8A7055"],  # light→dark muted beige
    "strong_negative_decoupling":    ["#C4A090", "#5A2A1A"],  # light→dark muted brown
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
                <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:10px;">
                    <div style="min-width:18px; flex-shrink:0; margin-top:3px;">
                        <div style="width:18px; height:40px; border-radius:3px;
                                    background:linear-gradient(to bottom, {dark}, {light});"></div>
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:13px; color:#1a1a1a;">{name}</div>
                        <div style="font-size:11px; color:#555; margin-top:1px;">{desc}</div>
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
        <div style="border:1px solid #d0d0d0; border-radius:8px; padding:16px 18px; background:#fafafa;">
            <div style="font-size:12px; font-weight:700; letter-spacing:0.06em;
                        text-transform:uppercase; color:#333; margin-bottom:14px;">
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

        label = next(
            (name for items in LEGEND_ITEMS.values()
             for k, name, _ in items if k == class_key),
            class_key
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
        lataxis_range=[-45, 85],
        lonaxis_range=[-180, 180],
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=550,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )

    return fig


# ─────────────────────────────────────────
# RENDER CONTROLS & RETURN COMPONENTS
# ─────────────────────────────────────────
def build_view(historical_df: pd.DataFrame, show_pm25: bool):
    """Renders UI controls and builds the base figure, passing it back to app.py"""
    st.markdown(
        "**Does a country's economic growth rely on emissions?** "
        "Green means GDP is growing while emissions shrink. "
        "Muted tones indicate a contracting economy — interpret with caution."
    )

    mode_col, caption_col = st.columns([1, 2])
    with mode_col:
        smoothing = st.radio(
            "View mode:",
            options=["Annual", "5-year rolling average"],
            horizontal=True,
            key="smoothing_v1",
        )
    with caption_col:
        if smoothing == "5-year rolling average":
            caption = "📊 Smooths short-term shocks like COVID-2020, showing each country's underlying long-term trend."
        else:
            caption = "📊 Raw year-by-year classification — useful for spotting specific events but more sensitive to short-term shocks."
        st.markdown(f"<p style='font-size:0.8rem; color:#999; margin-top:1.8rem;'>{caption}</p>", unsafe_allow_html=True)

    tapio_col = "tapio_class" if smoothing == "Annual" else "tapio_class_5yr"
    
    # Dynamically restrict slider range if the PM2.5 layer is toggled ON
    if show_pm25:
        min_year = max(2000, int(historical_df["year"].min()))
        max_year = min(2020, int(historical_df["year"].max()))
        st.caption("⏳ *Timeline restricted to 2000-2020 due to Air Quality data availability.*")
    else:
        min_year = int(historical_df["year"].min())
        max_year = int(historical_df["year"].max())

    st.markdown("""
        <style>
        [data-testid="stSlider"] .st-emotion-cache-1xp7nia { color: #2D5A27; }
        [data-testid="stSlider"] [role="slider"] { background-color: #2D5A27; }
        [data-testid="stSlider"] .st-bq { background-color: #2D5A27; }
        </style>
    """, unsafe_allow_html=True)
    
    selected_year = st.slider(
        f"Timeline: {min_year} – {max_year}",
        min_value=min_year,
        max_value=max_year,
        value=max_year,
        step=1,
        key="slider_v1",
        format="%d",
    )
    
    year_data = historical_df[historical_df["year"] == selected_year].copy()
    
    # Pass 'fogged' parameter to map builder
    fig = build_map(year_data, tapio_col, fogged=show_pm25)
    
    return fig, year_data, tapio_col, selected_year


# ─────────────────────────────────────────
# HELPER RENDERERS FOR APP.PY LAYOUT
# ─────────────────────────────────────────
def render_legend():
    """Renders the HTML legend so app.py can place it in the correct column."""
    components.html(build_legend_html(), height=620, scrolling=False)


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