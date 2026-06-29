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

    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)

    def categorize_pm25(val):
        if pd.isna(val):   return 'No Data'
        elif val <= 5.0:   return 'Good (<=5 µg/m³)'
        elif val <= 10.0:  return 'Fair (5.1-10 µg/m³)'
        elif val <= 15.0:  return 'Moderate (10.1-15 µg/m³)'
        elif val <= 25.0:  return 'Poor (15.1-25 µg/m³)'
        else:              return 'Very Poor (>25 µg/m³)'

    historical_df["pm25_class"] = historical_df["pm25_ugm3"].apply(categorize_pm25)
    return historical_df, projections_df

historical_df, projections_df = load_data()

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

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2 = st.tabs(["🌍 View 1: Global Decoupling", "🌬️ View 2: Human Breath (PM2.5)"])

with tab1:
    view1.render(historical_df)

with tab2:
    view2.render(historical_df)