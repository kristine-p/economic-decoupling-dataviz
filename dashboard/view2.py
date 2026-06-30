import pandas as pd
import plotly.graph_objects as go

def add_pm25_overlay(fig: go.Figure, regional_year_data: pd.DataFrame) -> go.Figure:
    """Takes View 1's figure and overlays regional PM2.5 bubbles on top of it."""
    
    # Filter out missing data
    pm25_data = regional_year_data.dropna(subset=['pm25_ugm3'])
    
    if pm25_data.empty:
        return fig
        
    # Grey scale gradient for smog/haze
    grey_colorscale = [
        [0.0, "#E0E0E0"],  # Lightest grey (good air quality)
        [0.25, "#BDBDBD"],
        [0.5, "#757575"],
        [0.75, "#424242"],
        [1.0, "#212121"]   # Darkest grey (poor air quality)
    ]
        
    fig.add_trace(
        go.Scattergeo(
            locations=pm25_data['iso3'],
            marker=dict(
                size=pm25_data['pm25_ugm3'],
                sizemode='area',
                sizeref=2. * 40 / (40. ** 2), # Smooth scaling math for PM2.5 values
                sizemin=4,
                color=pm25_data['pm25_ugm3'],
                colorscale=grey_colorscale,
                cmin=0,
                cmax=35, # Cap color scaling to make the worst polluters pop
                showscale=True,
                colorbar=dict(
                    title="PM2.5<br>(µg/m³)",
                    thickness=12,
                    len=0.45,
                    x=0.02, # Place colorbar neatly inside the map box
                    y=0.45
                ),
                line=dict(color='rgba(255, 255, 255, 0.7)', width=0.5),
                opacity=0.65 # Make slightly transparent so overlapping regional bubbles are visible
            ),
            name='Regional PM2.5',
            # Include region name in the hover text
            hovertext=pm25_data['region_name'] + ' (' + pm25_data['country'] + ')<br>PM2.5: ' + pm25_data['pm25_ugm3'].round(1).astype(str) + ' µg/m³',
            hoverinfo='text'
        )
    )
    
    return fig