import os
import streamlit as st
import pandas as pd
import view1
import view2

st.set_page_config(
    page_title="Breaking the Link: Green Growth",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_path = os.path.join(base_dir, "..", "data", "processed", "merged_panel.csv")
    projections_path = os.path.join(base_dir, "..", "data", "processed", "climate_projections.csv")
    regions_path = os.path.join(base_dir, "..", "data", "processed", "pm25_regions_geocoded.csv")

    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)
    regions_df = pd.read_csv(regions_path)
    
    return historical_df, projections_df, regions_df

historical_df, projections_df, regions_df = load_data()

st.markdown("""
    <div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:1rem; border-bottom: 1px solid #e0ddd8; padding-bottom: 0.5rem;">
        <h2 style="margin:0; font-size:1.6rem; color:#2C2C2C; flex-shrink:0;">Breaking the Link</h2>
        <p style="margin:0; color:#888; font-size:0.9rem; padding-left:1rem; font-weight:500;">
            Visualizing the Decoupling of Economic Expansion and Environmental Impact
        </p>
    </div>
""", unsafe_allow_html=True)

show_pm25 = st.session_state.get("pm25_toggle", False)
fig, year_data, tapio_col, selected_year, min_year, max_year = view1.build_view(historical_df, show_pm25=show_pm25)

if show_pm25:
    regional_year_data = regions_df[regions_df["year"] == selected_year].copy()
    fig = view2.add_pm25_overlay(fig, regional_year_data)

view1.render_map_frame_css()

# Now using the native key support
with st.container(key="v1_map_frame"):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    view1.render_floating_controls(min_year, max_year, show_pm25)
    view1.render_legend()