import pandas as pd
from geopy.geocoders import Nominatim
import time
import os

input_path = "data/processed/pm25_regions.csv"
output_path = "data/processed/pm25_regions_geocoded.csv"

# 1. Load existing progress if available to prevent re-running everything
if os.path.exists(output_path):
    print(f"Found existing {output_path}. Resuming where we left off...")
    df = pd.read_csv(output_path)
else:
    print("Starting fresh...")
    df = pd.read_csv(input_path)
    df['lat'] = None
    df['lon'] = None

# 2. Extract ONLY the regions that STILL need coordinates
regions_to_fetch = df[df['lat'].isnull()][['region_name', 'country']].drop_duplicates()

if regions_to_fetch.empty:
    print("All regions already have coordinates! Nothing to fetch.")
else:
    geolocator = Nominatim(user_agent="green_growth_dashboard")
    print(f"Fetching coordinates for {len(regions_to_fetch)} remaining regions... (respecting API limits)")

    # 3. Look up remaining regions
    for index, row in regions_to_fetch.iterrows():
        # --- CLEAN THE COUNTRY NAME FOR THE GEOCODER ---
        clean_country = row['country']
        if "China" in clean_country:
            clean_country = "China"
        elif "Korea" in clean_country:
            clean_country = "South Korea"
        elif "Türkiye" in clean_country:
            clean_country = "Turkey"
        elif "Slovak Republic" in clean_country:
            clean_country = "Slovakia"
            
        # --- CLEAN REGION NAMES FOR SPECIFIC COUNTRIES ---
        # First, cleanly strip away OECD bureaucratic tags
        clean_region = str(row['region_name']).replace("(TL2021)", "").replace("(TL2016)", "").strip()
        clean_region = clean_region.replace(" Province", "").replace(" region", "")
        
        # Hardcoded overrides for the specific failed regions you found
        override_map = {
            "North West": "Severozapaden",
            "North Central": "Severen Tsentralen",
            "Severentsentralen": "Severen Tsentralen", # Catch for previous run
            "South East": "Yugoiztochen",
            "South West": "Sofia",
            "Yugozapaden": "Sofia", # Catch for previous run
            "Eastern Switzerland": "Ostschweiz",
            "City of Zagreb": "Zagreb",
            "DKI Jakarta": "Jakarta",
            "D.I. Yogyakarta": "Special Region of Yogyakarta",
            "Bangka Belitung": "Bangka Belitung Islands",
            "Middle Kalimantan": "Central Kalimantan",
            "Middle Sulawesi": "Central Sulawesi",
            "South East Sulawesi": "Southeast Sulawesi",
            "Western Lesser Sundas": "West Nusa Tenggara",
            "Eastern Lesser Sundas": "East Nusa Tenggara",
            "Other Regions": "Iceland", # Fallback map to center of country
            "Autonomous prov. Bolzano": "South Tyrol",
            "Autonomous prov. Trento": "Trentino",
            "Northern-Kanto, Koshin": "Kanto",
            "Southern-Kanto": "Kanto",
            "Kansai": "Kansai",
            "Western Norway": "Vestlandet",
            "Oslo and Viken": "Oslo",
            "Agder and Sør-Østlandet": "Agder",
            "Prov. const. del Callao": "Callao",
            "Opole": "Opole Voivodeship",
            "Lublin": "Lublin Voivodeship",
            "Mazowiecki": "Masovian Voivodeship",
            "Metropolitan area of Lisbon": "Lisbon",
            "Autonomous Region of the Azores": "Azores",
            "Autonomous Region of Madeira": "Madeira",
            "South - Muntenia": "Sud-Muntenia",
            "The region of Šumadija and Western Serbia": "Šumadija and Western Serbia",
            "The of Šumadija and Western Serbia": "Šumadija and Western Serbia", # Fixes the replace bug
            "Region of Southern and Eastern Serbia": "Southern and Eastern Serbia",
            "Federal City of Saint Petersburg": "Saint Petersburg",
            "Karachay-Cherkhess Republic": "Karachay-Cherkessia",
            "Republic of Bashkorstostan": "Bashkortostan",
            "Republic of Altai": "Altai Republic",
            "Småland with Islands": "Småland",
            "Central Norrland": "Mellersta Norrland",
            "West Slovakia": "Západné Slovensko",
            "East Slovakia": "Východné Slovensko",
            "Western Slovakia": "Západné Slovensko",
            "Eastern Slovakia": "Východné Slovensko",
            "Southern Marmara - West": "Balikesir",
            "Eastern Marmara - South": "Bursa",
            "Eastern Marmara - North": "Kocaeli",
            "Central Anatolia - West and South": "Konya",
            "Mediterranean region - West": "Antalya",
            "Mediterranean - West": "Antalya",
            "Mediterranean region - Middle": "Mersin",
            "Mediterranean - Middle": "Mersin",
            "Mediterranean region - East": "Hatay",
            "Mediterranean - East": "Hatay",
            "Central Anatolia - Middle": "Kayseri",
            "Central Anatolia - East": "Kirikkale",
            "Western Black Sea - West": "Zonguldak",
            "Western Black Sea - Middle and East": "Kastamonu",
            "Middle Black Sea": "Samsun",
            "Northeastern Anatolia - West": "Erzurum",
            "Northeastern Anatolia - East": "Kars",
            "Eastern Anatolia - West": "Malatya",
            "Eastern Anatolia - East": "Van",
            "Southeastern Anatolia - West": "Gaziantep",
            "Southeastern Anatolia - Middle": "Sanliurfa",
            "Southeastern Anatolia - East": "Mardin"
        }
        
        if clean_country == "Costa Rica":
            if clean_region == "Central Pacific":
                clean_region = "Pacífico Central"
            elif clean_region == "Huetar Caribbean":
                clean_region = "Huetar Caribe"
            elif clean_region == "North Huetar":
                clean_region = "Huetar Norte"
        else:
            if clean_region in override_map:
                clean_region = override_map[clean_region]
                
        query = f"{clean_region}, {clean_country}"
        
        try:
            location = geolocator.geocode(query, timeout=10)
            if location:
                # Update the dataframe directly for this specific region
                df.loc[df['region_name'] == row['region_name'], 'lat'] = location.latitude
                df.loc[df['region_name'] == row['region_name'], 'lon'] = location.longitude
                print(f"Found: {query}")
            else:
                print(f"Could not find: {query}")
            time.sleep(1.2) # Sleep to prevent being blocked by the free API
        except Exception as e:
            print(f"Error finding {query}: {e}")
            time.sleep(2)
            
        # 4. Save progress incrementally so you never lose data if it stops!
        df.to_csv(output_path, index=False)

    print(f"\nFinished processing! Saved to {output_path}")