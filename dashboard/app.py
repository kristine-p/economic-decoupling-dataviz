import os
import streamlit as st
import pandas as pd

import view1
import view2
import view3
from style import inject_base_css, hud_kv, COLORS

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Breaking the Link · Green Growth",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_base_css()

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_path = os.path.join(base_dir, "..", "data", "processed", "merged_panel.csv")
    projections_path = os.path.join(base_dir, "..", "data", "processed", "climate_projections.csv")
    regions_path = os.path.join(base_dir, "..", "data", "processed", "pm25_regions_geocoded.csv")

    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)
    regions_df = pd.read_csv(regions_path)

    # give the climate table real country names sourced from the panel
    # (its own "country" field is frequently just the iso3 code)
    name_lookup = historical_df.drop_duplicates("iso3").set_index("iso3")["country"].to_dict()
    projections_df["country"] = projections_df["iso3"].map(name_lookup).fillna(projections_df["country"])

    return historical_df, projections_df, regions_df

historical_df, projections_df, regions_df = load_data()

# ─────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────
st.session_state.setdefault("active_view", "Decoupling Map")

# ─────────────────────────────────────────
# TOP BAR — brand + pill nav
# ─────────────────────────────────────────
with st.container(key="topbar"):
    brand_col, nav_col = st.columns([1, 1])
    with brand_col:
        st.html("""
<div class="brand-wrap">
    <div class="brand-title">🌍 Breaking the Link</div>
    <div class="brand-sub">Green growth &amp; decoupling</div>
</div>
""")
    with nav_col:
        # real nested containers (not a raw div-open/close pair — those don't
        # nest across separate st.html calls) so the CSS flex rule actually
        # wraps the radio widget rendered inside it.
        with st.container(key="navpill_align"):
            with st.container(key="navpill"):
                active_view = st.radio(
                    "view", ["Decoupling Map", "Future Scenarios"],
                    horizontal=True, label_visibility="collapsed", key="active_view",
                )

# ═════════════════════════════════════════
# VIEW: DECOUPLING MAP  (View 1 + toggleable View 2 overlay)
# ═════════════════════════════════════════
if active_view == "Decoupling Map":

    # ---- left HUD panel (controls) ----
    with st.container(key="leftpanel"):
        st.html('<div style="padding:0 0 6px 0;" class="hud-label">MAP CONTROLS</div>')
        smoothing = st.radio(
            "View mode", ["Annual", "5-year rolling average"],
            key="smoothing_v1",
        )
        st.html('<hr class="hud-divider" style="margin:12px 0;">')
        show_pm25 = st.toggle("Air quality layer", value=False, key="show_pm25")

    # ---- bottom timeline dock (slider) ----
    with st.container(key="timeline"):
        min_year, max_year = view1.year_bounds(historical_df, show_pm25)
        default_year = st.session_state.get("slider_v1", max_year)
        default_year = min(max(default_year, min_year), max_year)
        selected_year = st.slider(
            f"Timeline — {min_year} to {max_year}",
            min_value=min_year, max_value=max_year,
            value=default_year, step=1, key="slider_v1", format="%d",
        )
        if show_pm25:
            st.html(
                f'<div style="font-size:0.68rem; color:{COLORS["text_faint"]}; margin-top:-4px;">'
                f'Timeline restricted to 2000–2020 · limited by air-quality data availability</div>'
            )

    fig, year_data, tapio_col = view1.build_view(historical_df, show_pm25, smoothing, selected_year)
    if show_pm25:
        regional_year_data = regions_df[regions_df["year"] == selected_year].copy()
        fig = view2.add_pm25_overlay(fig, regional_year_data)
    fig.update_layout(height=1000)

    # ---- fullbleed map ----
    with st.container(key="mapstage"):
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": True})

    # ---- right HUD panel ----
    with st.container(key="sidepanel"):
        view1.render_country_stat(year_data, tapio_col, selected_year, None)
        view1.render_legend_hud()
        view1.render_data_table(year_data, tapio_col, selected_year)

# ═════════════════════════════════════════
# VIEW: FUTURE SCENARIOS  (View 3)
# ═════════════════════════════════════════
else:
    countries = sorted(projections_df["country"].dropna().unique().tolist())
    default_country = countries[0] if countries else None
    compare_precheck = st.session_state.get("compare_v3", False)
    alt_options = [s for s in view3.scenario_options() if s != view3.LINKED_LABEL]

    # ---- left HUD panel (controls) ----
    with st.container(key="leftpanel"):
        st.html('<div style="padding:0 0 6px 0;" class="hud-label">SCENARIO CONTROLS</div>')
        metric_label = st.radio(
            "Metric", list(view3.METRIC_COLS.keys()),
            key="metric_v3",
        )
        st.html('<hr class="hud-divider" style="margin:12px 0;">')
        scenario_label = st.selectbox(
            "Scenario", view3.scenario_options(), key="scenario_v3",
        )
        st.html('<hr class="hud-divider" style="margin:12px 0;">')
        compare_mode = st.toggle("Compare", value=compare_precheck, key="compare_v3")
        if compare_mode:
            alt_scenario = st.selectbox(
                "Compare against", alt_options, key="alt_scenario_v3",
            )
        else:
            alt_scenario = st.session_state.get("alt_scenario_v3", alt_options[-1])

    # ---- bottom timeline dock (slider) ----
    with st.container(key="timeline"):
        year3 = st.slider(
            "Projection year — 2030 to 2060",
            min_value=2030, max_value=2060,
            value=st.session_state.get("year_v3", 2050), step=1, key="year_v3", format="%d",
        )

    metric_col = view3.METRIC_COLS[metric_label]

    if compare_mode:
        df_left = view3.slice_for_scenario(projections_df, year3, view3.LINKED_LABEL)
        df_right = view3.slice_for_scenario(projections_df, year3, alt_scenario)
        fig3 = view3.build_compare_map(
            df_left, df_right, metric_col,
            "Current trajectory", alt_scenario,
        )
        map_height = 620
    else:
        df_map = view3.slice_for_scenario(projections_df, year3, scenario_label)
        fig3 = view3.build_single_map(df_map, metric_col)
        map_height = 1000

    fig3.update_layout(height=map_height)

    with st.container(key="mapstage"):
        st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False, "scrollZoom": True})

    # ---- right HUD panel: country deep-dive ----
    with st.container(key="sidepanel"):
        st.html('<div style="padding:14px 16px 6px 16px;" class="hud-label">COUNTRY TRAJECTORY</div>')

        with st.container(key="country_select_wrap"):
            sel_country = st.selectbox(
                "Country", countries,
                index=countries.index(default_country) if default_country in countries else 0,
                key="country_v3", label_visibility="collapsed",
            )

        iso3 = projections_df.loc[projections_df["country"] == sel_country, "iso3"].iloc[0]
        sub = projections_df[projections_df["iso3"] == iso3]
        linked_row = sub[sub["is_linked_scenario"]]
        linked_short = view3.SCENARIO_SHORT.get(linked_row["scenario"].iloc[0]) if not linked_row.empty else "—"

        with st.container(key="hud_kv_wrap"):
            hud_kv("Linked scenario", linked_short, accent=True)
            hud_kv("Metric", metric_label)
            hud_kv("Unit", view3.METRIC_UNITS[metric_label])
        st.html('<hr class="hud-divider" style="margin:8px 16px;">')

        trend_fig = view3.build_trend_chart(projections_df, iso3, metric_col)
        st.plotly_chart(trend_fig, width="stretch", config={"displayModeBar": False})

        st.html(f"""
<div style="padding:0 16px 14px 16px; font-size:0.68rem; color:{COLORS['text_faint']}; line-height:1.4;">
    The solid line is the scenario linked to {sel_country}'s current decoupling
    trajectory — its most representative future pathway given present-day
    Tapio elasticity. Dotted lines show the three alternative SSP pathways.
</div>
""")