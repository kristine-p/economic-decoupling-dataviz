import os
import streamlit as st
import pandas as pd

import view1
import view2
import view3
from style import inject_base_css, hud_kv, pin_sidepanel_scroll, COLORS

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
# INFO DIALOG
# ─────────────────────────────────────────
@st.dialog("About This Dashboard", width="large")
def show_info_dialog():
    st.markdown(f"""
### Demo Video
https://www.youtube.com/watch?v=h6miKoq9yLs
### Key Terms

| Abbreviation | Meaning |
|---|---|
| **GDP** | **Gross Domestic Product** — the total monetary value of all goods and services produced within a country in a given year. Used here as the primary indicator of economic growth. |
| **GHG** | **Greenhouse Gas Emissions** — the total CO₂-equivalent emissions produced by a country, covering carbon dioxide, methane, nitrous oxide, and fluorinated gases. |

---

### The Tapio Decoupling Index

The **Tapio elasticity index** measures the relationship between economic growth and emissions growth. It is calculated as:

$$E = \\frac{{\\%\\Delta GHG}}{{\\%\\Delta GDP}}$$

Where **%ΔGHG** is the percentage change in greenhouse gas emissions and **%ΔGDP** is the percentage change in GDP over the same period.

Based on the value of **E**, countries are classified into one of seven decoupling states:

| State | Condition | Meaning |
|---|---|---|
| **Absolute decoupling** | GDP ↑, GHG ↓ | The best case — growth with falling emissions |
| **Relative decoupling** | GDP ↑, GHG ↑ slower than GDP | Emissions still rising, but slower than growth |
| **Expansive coupling** | GDP ↑, GHG ↑ at the same rate | No progress — emissions track growth 1:1 |
| **Expansive negative decoupling** | GDP ↑, GHG ↑ faster than GDP | Worst growing case — emissions outpace growth |
| **Recessive decoupling** | GDP ↓, GHG ↓ even faster | Emissions falling, but so is the economy |
| **Recessive coupling** | GDP ↓, GHG ↓ at the same rate | Both declining together |
| **Strong negative decoupling** | GDP ↓, GHG ↑ | The worst case — shrinking economy, rising emissions |

The **5-year rolling average** option smooths annual volatility to reveal longer-term structural trends.

---

### Future Scenarios (Climate Projections)

The **Future Scenarios** view shows projected changes in extreme weather indicators (hot days, tropical nights, icing days) under different **SSP** (Shared Socioeconomic Pathway) scenarios:

- **SSP1-2.6** — Sustainability pathway (low emissions)
- **SSP2-4.5** — Middle of the road
- **SSP3-7.0** — Regional rivalry (high emissions)
- **SSP5-8.5** — Fossil-fueled development (very high emissions)

Values show the **absolute difference** in days/year compared to the 1981–2010 historical baseline.

---

### Contact

| Name | Email | GitHub |
|---|---|---|
| *Kristine Paegle* | *kristine.paegle@studenti.unitn.it* | https://github.com/kristine-p |
| *Giuseppe Pio Mangiacotti* | *giuseppe.mangiacotti@studenti.unitn.it* | https://github.com/givmangi |
| *Martin Krisak* | *martin.krisak@studenti.unitn.it* | https://github.com/martin-kri |

---

### Datasets

| Source | Dataset | Link |
|---|---|---|
| **OECD** | Air and GHG Emissions | https://data-explorer.oecd.org/vis?lc=en&tm=%22Air%20emissions%20-%20Greenhouse%20gas%20emissions%20Inventories%22&pg=0&snb=1&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_AIR_GHG%40DF_AIR_GHG&df[ag]=OECD.ENV.EPI&df[vs]=1.0&dq=.A.GHG._T.KG_CO2E_PS&pd=2014,&to[TIME_PERIOD]=false |
| **World Bank** | GDP per capita, PPP | https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.CD |
| **OECD** | Exposure to Air Pollution | https://data-explorer.oecd.org/vis?tm=DF_AIR_POLL&pg=0&snb=1&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_AIR_POL%40DF_AIR_POLL&df[ag]=OECD.ENV.EPI&df[vs]=&pd=%2C&dq=.A.MEAN_POP....&to[TIME_PERIOD]=false |
| **OECD** | Climate Projections | https://data-explorer.oecd.org/vis?lc=en&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_REG_CLIM%40DF_CLIM_PROJ&df[ag]=OECD.CFE.EDS&dq=A.CTRY.BEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA%2BAUS%2BAUT..HOT_DAYS_PROJ...PROJ_SSP585%2BPROJ_SSP370%2BPROJ_SSP245%2BPROJ_SSP126..D_Y&pd=2030%2C2060&to[TIME_PERIOD]=false&vw=ov |

""")
    st.caption("Built with Streamlit · Data sources: World Bank, OECD")

# ─────────────────────────────────────────
# TOP BAR — brand + pill nav
# ─────────────────────────────────────────
with st.container(key="topbar"):
    brand_col, nav_col, spacer_col = st.columns([1, 1, 1])
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
        # wraps the radio widget rendered inside it. Centered within an
        # equal-width middle column (with an equal-width empty spacer column
        # on the right balancing the brand column on the left) so the pill
        # lands at the true center of the viewport, not just the center of
        # whatever space is left after the brand.
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

    # ---- left panel (controls) ----
    with st.container(key="leftpanel"):
        st.html('<div class="hud-label" style="margin-bottom:8px;">CONTROLS</div>')
        smoothing = st.radio(
            "View mode", ["Annual", "5-year rolling average"],
            key="smoothing_v1"
        )
        st.html('<div style="height:12px;"></div>')
        show_pm25 = st.toggle("Air quality layer", value=False, key="show_pm25")
        if show_pm25:
            st.html(
                f'<div style="font-size:0.68rem; color:{COLORS["text_faint"]}; margin-top:4px;">'
                f'Timeline restricted to 2000–2020</div>'
            )
            view2.render_pm25_legend()

    # ---- bottom timeline dock (controls) ----
    with st.container(key="timeline"):
        min_year, max_year = view1.year_bounds(historical_df, show_pm25)
        fallback_year = view1.default_analysis_year(historical_df)
        default_year = st.session_state.get("slider_v1", fallback_year)
        default_year = min(max(default_year, min_year), max_year)
        selected_year = st.slider(
            f"Timeline — {min_year} to {max_year}",
            min_value=min_year, max_value=max_year,
            value=default_year, step=1, key="slider_v1", format="%d",
            label_visibility="collapsed"
        )

    fig, year_data, tapio_col = view1.build_view(historical_df, show_pm25, smoothing, selected_year)
    if show_pm25:
        regional_year_data = regions_df[regions_df["year"] == selected_year].copy()
        fig = view2.add_pm25_overlay(fig, regional_year_data)
    fig.update_layout(height=1000)

    # ---- fullbleed map ----
    with st.container(key="mapstage"):
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": True}, key="map_v1")

    # ---- right HUD panel ----
    with st.container(key="sidepanel"):
        view1.render_country_stat(year_data, tapio_col, selected_year, None)
        view1.render_legend_hud()
    pin_sidepanel_scroll()

# ═════════════════════════════════════════
# VIEW: FUTURE SCENARIOS  (View 3)
# ═════════════════════════════════════════
else:
    countries = sorted(projections_df["country"].dropna().unique().tolist())

    # ── build iso3 ↔ country lookup tables used by click handler ──
    iso3_to_country = (
        projections_df[["iso3", "country"]]
        .drop_duplicates("iso3")
        .set_index("iso3")["country"]
        .to_dict()
    )

    # ---- bottom timeline dock ----
    with st.container(key="timeline"):
        year3 = st.slider(
            "Projection year — 2030 to 2060",
            min_value=2030, max_value=2060,
            value=st.session_state.get("year_v3", 2050), step=1, key="year_v3", format="%d",
            label_visibility="collapsed"
        )

    # ---- left panel (controls) ----
    with st.container(key="leftpanel"):
        st.html('<div class="hud-label" style="margin-bottom:8px;">CONTROLS</div>')
        metric_label = st.radio(
            "Metric", list(view3.METRIC_COLS.keys()),
            key="metric_v3"
        )
        st.html('<div style="height:12px;"></div>')
        scenario_label = st.selectbox(
            "Scenario", view3.scenario_options(), key="scenario_v3"
        )

        metric_col = view3.METRIC_COLS[metric_label]
        abs_col = view3.METRIC_ABS_COLS[metric_label]
        df_map = view3.slice_for_scenario(projections_df, year3, scenario_label)
        zmax = view3._symmetric_range(df_map[metric_col]) if len(df_map.dropna(subset=[metric_col])) else 5.0

        view3.render_legend_hud(zmax)

    fig3 = view3.build_single_map(df_map, metric_col, abs_col=abs_col, unit_label=view3.METRIC_ABS_UNITS[metric_label])
    fig3.update_layout(height=1000)

    # ── map with click-to-select ──────────────────────────────────────────
    # on_select="rerun" makes Streamlit re-run the script whenever the user
    # clicks a country; the return value carries the clicked iso3 code.
    with st.container(key="mapstage"):
        map_selection = st.plotly_chart(
            fig3, width="stretch",
            config={"displayModeBar": False, "scrollZoom": True},
            key="map_v3",
            on_select="rerun",
            selection_mode="points",
        )

    # Handle map clicks and selection clearing
    if map_selection and hasattr(map_selection, "selection"):
        current_points = map_selection.selection.points
        current_locations = [p.get("location") for p in current_points if "location" in p]
        
        last_locations = st.session_state.get("last_map_locations_v3", None)
        if current_locations != last_locations:
            # Map selection actually changed via user interaction
            st.session_state["last_map_locations_v3"] = current_locations
            if current_locations:
                # User selected a specific country
                clicked_iso3 = current_locations[0]
                if clicked_iso3 in iso3_to_country:
                    clicked_country = iso3_to_country[clicked_iso3]
                    if clicked_country in countries:
                        st.session_state["country_v3"] = clicked_country
            else:
                # User clicked empty space (ocean) clearing the selection.
                # Only reset if we previously had a selection (not on initial load).
                if last_locations is not None:
                    if countries:
                        st.session_state["country_v3"] = countries[0]

    # ---- right HUD panel: country deep-dive ----
    with st.container(key="sidepanel"):
        st.html('<div style="padding:14px 16px 6px 16px;" class="hud-label">COUNTRY TRAJECTORY</div>')

        with st.container(key="country_select_wrap"):
            # The selectbox value is driven by session_state["country_v3"];
            # clicking the map updates that key before this widget renders,
            # so the dropdown and the trend chart always stay in sync.
            sel_country = st.selectbox(
                "Country", countries,
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
    Click any country on the map to explore its trajectory, or use the
    dropdown above. The solid line is the scenario linked to {sel_country}'s
    current decoupling trajectory. Dotted lines show the three alternative
    SSP pathways.
</div>
""")
    pin_sidepanel_scroll()

# ─────────────────────────────────────────
# FLOATING INFO BUTTON (bottom-left)
# ─────────────────────────────────────────
with st.container(key="info_btn_wrap"):
    if st.button("ℹ", key="info_btn", help="About this dashboard"):
        show_info_dialog()
