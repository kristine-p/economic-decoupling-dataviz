import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# VISUALIZATION MODULES (Acting as separate scripts)
# ==========================================

def get_tapio_colors():
    """Returns the traffic light color mapping for the Tapio Index."""
    return {
        'absolute_decoupling': '#1a9850',       # Dark Green (Success)
        'relative_decoupling': '#91cf60',       # Light Green (Progress)
        'expansive_coupling': '#fdae61',        # Orange (Warning)
        'expansive_negative_decoupling': '#d73027', # Red (Failure)
        'strong_negative_decoupling': '#a50026',    # Dark Red
        'weak_decoupling': '#d9ef8b',
        'weak_negative_decoupling': '#f46d43',
        'recessive_coupling': '#fee08b',
        'recessive_decoupling': '#1a9850',
        'undefined': '#e0e0e0'                  # Grey for missing data
    }

def get_pm25_colors():
    """Returns the traffic light color mapping for PM2.5 Air Quality."""
    return {
        'Good (<=5 µg/m³)': '#1a9850',         # Dark Green (WHO Guideline)
        'Fair (5.1-10 µg/m³)': '#91cf60',      # Light Green
        'Moderate (10.1-15 µg/m³)': '#fee08b', # Yellow
        'Poor (15.1-25 µg/m³)': '#fdae61',       # Orange
        'Very Poor (>25 µg/m³)': '#d73027',      # Red
        'No Data': '#e0e0e0'                   # Grey
    }

def create_view1_choropleth(year_data):
    """Generates the base View 1 Global Decoupling Map."""
    fig = px.choropleth(
        year_data,
        locations="iso3",
        color="tapio_class_5yr",
        hover_name="country",
        hover_data={
            "iso3": False,
            "gdp_pct_change": ":.2f",
            "ghg_pct_change": ":.2f",
            "tapio_E_5yr": ":.2f",
            "tapio_class_5yr": False
        },
        color_discrete_map=get_tapio_colors(),
        projection="natural earth"
    )

    # Clean up map aesthetics
    fig.update_geos(
        showcoastlines=True, coastlinecolor="rgba(0,0,0,0.2)",
        showland=True, landcolor="#f4f4f4",
        showocean=True, oceancolor="#e0f3f8"
    )

    fig.update_layout(
        margin={"r":0,"t":20,"l":0,"b":0},
        legend_title_text="Decoupling State",
        height=600
    )
    return fig

def create_view2_pm25_map(year_data):
    """Generates the View 2 Air Quality Map using discrete categorical colors."""
    fig = px.choropleth(
        year_data,
        locations="iso3",
        color="pm25_class", # Colored by our new discrete categories
        hover_name="country",
        hover_data={
            "iso3": False,
            "pm25_ugm3": ":.2f",
            "pm25_class": False
        },
        color_discrete_map=get_pm25_colors(), # Using the exact same colors as View 1
        projection="natural earth",
        category_orders={"pm25_class": [
            'Good (<=5 µg/m³)', 'Fair (5.1-10 µg/m³)', 
            'Moderate (10.1-15 µg/m³)', 'Poor (15.1-25 µg/m³)', 
            'Very Poor (>25 µg/m³)', 'No Data'
        ]}
    )

    # Clean up map aesthetics
    fig.update_geos(
        showcoastlines=True, coastlinecolor="rgba(0,0,0,0.2)",
        showland=True, landcolor="#f4f4f4",
        showocean=True, oceancolor="#e0f3f8"
    )

    fig.update_layout(
        margin={"r":0,"t":20,"l":0,"b":0},
        legend_title_text="PM2.5 Exposure",
        height=600
    )
    return fig


# ==========================================
# MAIN STREAMLIT APPLICATION
# ==========================================

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Breaking the Link: Green Growth",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Build robust paths based on the script's location
    # This resolves to ../data/processed/ regardless of where you run the streamlit command
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_path = os.path.join(base_dir, "..", "data", "processed", "merged_panel.csv")
    projections_path = os.path.join(base_dir, "..", "data", "processed", "climate_projections.csv")
    
    historical_df = pd.read_csv(historical_path)
    projections_df = pd.read_csv(projections_path)
    
    # Pre-process PM2.5 into discrete categories for View 2
    def categorize_pm25(val):
        if pd.isna(val): return 'No Data'
        elif val <= 5.0: return 'Good (<=5 µg/m³)'
        elif val <= 10.0: return 'Fair (5.1-10 µg/m³)'
        elif val <= 15.0: return 'Moderate (10.1-15 µg/m³)'
        elif val <= 25.0: return 'Poor (15.1-25 µg/m³)'
        else: return 'Very Poor (>25 µg/m³)'
        
    historical_df['pm25_class'] = historical_df['pm25_ugm3'].apply(categorize_pm25)
    
    return historical_df, projections_df

historical_df, projections_df = load_data()

# Find bounds for View 1
min_year_v1 = int(historical_df['year'].min())
max_year_v1 = int(historical_df['year'].max())

# --- HEADER ---
st.title("Breaking the Link")
st.markdown("### Visualizing the Decoupling of Economic Expansion and Environmental Impact")
st.caption("Can a nation expand its economy while simultaneously shrinking its environmental footprint?")

# --- LAYOUT CONTAINERS ---
tab1, tab2 = st.tabs(["🌍 View 1: Global Decoupling", "🌬️ View 2: Human Breath (PM2.5)"])

# -----------------------------
# TAB 1: GLOBAL DECOUPLING MAP
# -----------------------------
with tab1:
    st.markdown("**Does a country's economic growth rely on emissions?** A green status means GDP is growing while emissions shrink.")
    
    # Independent slider for View 1
    selected_year_v1 = st.slider(
        "⏳ Explore historical decoupling trends:", 
        min_value=min_year_v1, 
        max_value=max_year_v1, 
        value=max_year_v1,
        step=1,
        key="slider_v1" # Unique key prevents Streamlit errors
    )
    
    year_data_v1 = historical_df[historical_df['year'] == selected_year_v1].copy()
    fig1 = create_view1_choropleth(year_data_v1)
    st.plotly_chart(fig1, width='stretch')

    # Data explorer focused specifically on View 1 metrics
    with st.expander(f"📊 View Raw Data for {selected_year_v1}"):
        display_df_v1 = year_data_v1[['country', 'tapio_class_5yr', 'gdp_pc_ppp_usd', 'ghg_per_capita_kg_co2e']].copy()
        display_df_v1.columns = ["Country", "Decoupling State", "GDP per Capita (PPP)", "GHG per Capita (kg CO2e)"]
        st.dataframe(display_df_v1.set_index("Country").dropna(how='all'), width='stretch')


# -----------------------------
# TAB 2: HUMAN BREATH (PM2.5)
# -----------------------------
with tab2:
    st.markdown("**Are citizens breathing cleaner air?** Categorized by WHO fine particulate matter thresholds.")
    
    # Independent slider restricted specifically to PM2.5 data availability (2000-2020)
    selected_year_v2 = st.slider(
        "⏳ Explore historical air quality trends:", 
        min_value=2000, 
        max_value=2020, 
        value=2020,
        step=1,
        key="slider_v2" # Unique key prevents Streamlit errors
    )
    
    year_data_v2 = historical_df[historical_df['year'] == selected_year_v2].copy()
    fig2 = create_view2_pm25_map(year_data_v2)
    st.plotly_chart(fig2, width='stretch')

    # Data explorer focused specifically on View 2 metrics
    with st.expander(f"📊 View Raw Data for {selected_year_v2}"):
        display_df_v2 = year_data_v2[['country', 'pm25_class', 'pm25_ugm3']].copy()
        display_df_v2.columns = ["Country", "Air Quality Category", "PM2.5 Exposure (µg/m³)"]
        st.dataframe(display_df_v2.set_index("Country").dropna(how='all'), width='stretch')