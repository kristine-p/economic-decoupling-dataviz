import streamlit as st
import pandas as pd
import plotly.express as px


def get_pm25_colors():
    """Returns the traffic light color mapping for PM2.5 Air Quality."""
    return {
        'Good (<=5 µg/m³)': '#1a9850',
        'Fair (5.1-10 µg/m³)': '#91cf60',
        'Moderate (10.1-15 µg/m³)': '#fee08b',
        'Poor (15.1-25 µg/m³)': '#fdae61',
        'Very Poor (>25 µg/m³)': '#d73027',
        'No Data': '#e0e0e0'
    }


def render(historical_df: pd.DataFrame):
    st.markdown("**Are citizens breathing cleaner air?** Categorized by WHO fine particulate matter thresholds.")

    selected_year_v2 = st.slider(
        "⏳ Explore historical air quality trends:",
        min_value=2000,
        max_value=2020,
        value=2020,
        step=1,
        key="slider_v2"
    )

    year_data_v2 = historical_df[historical_df['year'] == selected_year_v2].copy()

    fig = px.choropleth(
        year_data_v2,
        locations="iso3",
        color="pm25_class",
        hover_name="country",
        hover_data={
            "iso3": False,
            "pm25_ugm3": ":.2f",
            "pm25_class": False
        },
        color_discrete_map=get_pm25_colors(),
        projection="natural earth",
        category_orders={"pm25_class": [
            'Good (<=5 µg/m³)', 'Fair (5.1-10 µg/m³)',
            'Moderate (10.1-15 µg/m³)', 'Poor (15.1-25 µg/m³)',
            'Very Poor (>25 µg/m³)', 'No Data'
        ]}
    )

    fig.update_geos(
        showcoastlines=True, coastlinecolor="rgba(0,0,0,0.2)",
        showland=True, landcolor="#f4f4f4",
        showocean=True, oceancolor="#e0f3f8"
    )

    fig.update_layout(
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        legend_title_text="PM2.5 Exposure",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander(f"📊 View Raw Data for {selected_year_v2}"):
        display_df_v2 = year_data_v2[['country', 'pm25_class', 'pm25_ugm3']].copy()
        display_df_v2.columns = ["Country", "Air Quality Category", "PM2.5 Exposure (µg/m³)"]
        st.dataframe(display_df_v2.set_index("Country").dropna(how='all'), use_container_width=True)