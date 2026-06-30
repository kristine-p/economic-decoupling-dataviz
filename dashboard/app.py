import os
import streamlit as st
import pandas as pd
import view1
import view2

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Breaking the Link: Green Growth",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 0.4rem;
        max-width: 100%;
    }
    header[data-testid="stHeader"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_path = os.path.join(base_dir, "..", "data", "processed", "merged_panel.csv")
    projections_path = os.path.join(base_dir, "..", "data", "processed", "climate_projections.csv")
    
    # Load the newly GEOCODED regional dataset!
    regions_path = os.path.join(base_dir, "..", "data", "processed", "pm25_regions_geocoded.csv")

    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)
    regions_df = pd.read_csv(regions_path)
    
    return historical_df, projections_df, regions_df

historical_df, projections_df, regions_df = load_data()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
    <div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:0.3rem; border-bottom: 1px solid #e0ddd8; padding-bottom: 0.25rem;">
        <h2 style="margin:0; font-size:1.1rem; color:#2C2C2C; flex-shrink:0;">Breaking the Link</h2>
        <p style="margin:0; color:#999; font-size:0.75rem; padding-left:1rem;">
            Visualizing the Decoupling of Economic Expansion and Environmental Impact
        </p>
    </div>
""", unsafe_allow_html=True)

# Read toggle state early (widget itself now renders inside the floating panel)
show_pm25 = st.session_state.get("pm25_toggle", False)

# ─────────────────────────────────────────
# BUILD & COMPILE FIGURE
# ─────────────────────────────────────────
# 1. Ask View 1 to build the base map (controls not rendered yet)
fig, year_data, tapio_col, selected_year, min_year, max_year = view1.build_view(historical_df, show_pm25=show_pm25)

# 2. Ask View 2 to modify the figure if toggled ON (Using Regional Data)
if show_pm25:
    # Filter the regional data down to the selected year
    regional_year_data = regions_df[regions_df["year"] == selected_year].copy()
    fig = view2.add_pm25_overlay(fig, regional_year_data)

# ─────────────────────────────────────────
# LAYOUT & RENDER (full-width map, floating controls)
# ─────────────────────────────────────────
view1.render_map_frame_css()

with st.container(key="v1_map_frame"):
    st.plotly_chart(fig, width="stretch")
    show_pm25 = view1.render_floating_controls(min_year, max_year, show_pm25)
    view1.render_legend()

# Ask View 1 to output the raw data table below the map
# view1.render_data_table(year_data, tapio_col, selected_year)