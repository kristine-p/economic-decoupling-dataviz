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

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_path = os.path.join(base_dir, "..", "data", "processed", "merged_panel.csv")
    projections_path = os.path.join(base_dir, "..", "data", "processed", "climate_projections.csv")
    
    # Load the new regional dataset
    regions_path = os.path.join(base_dir, "..", "data", "processed", "pm25_regions.csv")

    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)
    regions_df = pd.read_csv(regions_path)
    
    return historical_df, projections_df, regions_df

historical_df, projections_df, regions_df = load_data()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2rem; border-bottom: 1px solid #e0ddd8; padding-bottom: 0.8rem;">
        <h2 style="margin:0; font-size:1.8rem; color:#2C2C2C; flex-shrink:0;">Breaking the Link</h2>
        <div style="text-align:right; padding-left:2rem;">
            <p style="margin:0 0 0.2rem 0; font-weight:500; color:#555; font-size:0.9rem;">
                Visualizing the Decoupling of Economic Expansion and Environmental Impact
            </p>
            <p style="margin:0; color:#999; font-size:0.82rem;">
                Can a nation expand its economy while simultaneously shrinking its environmental footprint?
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Toggle to trigger View 2 logic
show_pm25 = st.toggle("🌬️ Show Air Quality Layer (PM2.5)", value=False)

# ─────────────────────────────────────────
# BUILD & COMPILE FIGURE
# ─────────────────────────────────────────
# 1. Ask View 1 to build the controls and base map (no rendering yet)
fig, year_data, tapio_col, selected_year = view1.build_view(historical_df, show_pm25=show_pm25)

# 2. Ask View 2 to modify the figure if toggled ON (Using Regional Data)
if show_pm25:
    # Filter the regional data down to the selected year
    regional_year_data = regions_df[regions_df["year"] == selected_year].copy()
    fig = view2.add_pm25_overlay(fig, regional_year_data)

# ─────────────────────────────────────────
# LAYOUT & RENDER
# ─────────────────────────────────────────
map_col, legend_col = st.columns([3, 1])

with map_col:
    # Use width="stretch" to resolve recent Streamlit deprecation warnings
    st.plotly_chart(fig, width="stretch")

with legend_col:
    # Ask View 1 to output the HTML legend
    view1.render_legend()

# Ask View 1 to output the raw data table below the map
view1.render_data_table(year_data, tapio_col, selected_year)