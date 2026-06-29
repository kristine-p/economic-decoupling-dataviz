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
st.title("Breaking the Link")
st.markdown("### Visualizing the Decoupling of Economic Expansion and Environmental Impact")
st.caption("Can a nation expand its economy while simultaneously shrinking its environmental footprint?")

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2 = st.tabs(["🌍 View 1: Global Decoupling", "🌬️ View 2: Human Breath (PM2.5)"])

with tab1:
    view1.render(historical_df)

with tab2:
    view2.render(historical_df)