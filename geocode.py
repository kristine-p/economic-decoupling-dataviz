import pandas as pd
from geopy.geocoders import Nominatim
import time

# 1. Load your existing data
df = pd.read_csv("data/processed/pm25_regions.csv")

# 2. Extract unique regions so we don't query the same place twice
unique_regions = df[['region_name', 'country']].drop_duplicates()

geolocator = Nominatim(user_agent="green_growth_dashboard")
latitudes = {}
longitudes = {}

print("Fetching coordinates... (this takes a moment to respect API rate limits)")

# 3. Look up each region
for index, row in unique_regions.iterrows():
    # --- CLEAN THE COUNTRY NAME FOR THE GEOCODER ---
    clean_country = row['country']
    if "China" in clean_country:
        clean_country = "China"
    elif "Korea" in clean_country:
        clean_country = "South Korea"
        
    # --- CLEAN REGION NAMES FOR SPECIFIC COUNTRIES ---
    clean_region = row['region_name']
    if clean_country == "Costa Rica":
        if clean_region == "Central Pacific":
            clean_region = "Pacífico Central"
        elif clean_region == "Huetar Caribbean":
            clean_region = "Huetar Caribe"
        elif clean_region == "North Huetar":
            clean_region = "Huetar Norte"
            
    query = f"{clean_region}, {clean_country}"
    
    try:
        location = geolocator.geocode(query, timeout=10)
        if location:
            latitudes[row['region_name']] = location.latitude
            longitudes[row['region_name']] = location.longitude
            print(f"Found: {query}")
        else:
            print(f"Could not find: {query}")
        time.sleep(1.2) # Sleep to prevent being blocked by the free API
    except Exception as e:
        print(f"Error finding {query}: {e}")
        time.sleep(2)

# 4. Map the coordinates back to the main dataset
df['lat'] = df['region_name'].map(latitudes)
df['lon'] = df['region_name'].map(longitudes)

# 5. Save the new file
output_path = "data/processed/pm25_regions_geocoded.csv"
df.to_csv(output_path, index=False)
print(f"\nSuccess! Saved to {output_path}")