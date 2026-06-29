#!/usr/bin/env python3
"""
Preprocess raw OECD and World Bank data into a single panel for the decoupling dataviz
It's the second version so note that it's still WiP and feedbacks are encouraged.
"""

import os
import argparse
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--raw-dir", default="data/raw")
parser.add_argument("--out-dir", default="data/processed")
args = parser.parse_args()

RAW = args.raw_dir
OUT = args.out_dir
os.makedirs(OUT, exist_ok=True)

FILES = {
    "ghg_all":  "GHG_all.csv",         
    "ghg_pc":   "GHGpercapita.csv",    
    "gdp":      "GDP_PPPadjusted.csv", 
    "pm25":     "PM2.5.csv",           
    "climate":  "CLIM_PROJ_all.csv",   
}

EXCLUDE_AGGREGATES = {"OECD", "OECDA", "OECDE", "OECDSO", "EU27_2020"}

# Correct display names for encoding-broken country strings in OECD files
DISPLAY_NAMES = {
    "TUR": "Turkiye",
    "CHN": "China (People's Republic of)",
    "CIV": "Cote d'Ivoire",
    "KOR": "Korea",
    "CZE": "Czechia",
}


# =============================================================================
# STEP 1 -- GHG TOTAL EMISSIONS
# =============================================================================
print("\n[1/6] Loading GHG total emissions...")

ghg = pd.read_csv(
    os.path.join(RAW, FILES["ghg_all"]),
    usecols=["REF_AREA", "Reference area", "POLLUTANT",
             "MEASURE", "UNIT_MEASURE", "TIME_PERIOD", "OBS_VALUE"],
    encoding="utf-8-sig",
    low_memory=False,
)

# KEY FILTER -- must apply all three conditions together:
#   MEASURE=_T      : total excl. LULUCF (not sector breakdown)
#   UNIT=T_CO2E     : tonnes CO2-equivalent (not index or per-capita)
#   POLLUTANT=GHG   : greenhouse gases total
# Without POLLUTANT=GHG, the file also has CO2-only rows for MEASURE=_T,
# creating two rows per country-year with different values and breaking pct_change().
ghg = ghg[
    (ghg["MEASURE"]      == "_T")     &
    (ghg["UNIT_MEASURE"] == "T_CO2E") &
    (ghg["POLLUTANT"]    == "GHG")
].copy()

ghg = ghg.rename(columns={
    "REF_AREA":       "iso3",
    "Reference area": "country",
    "TIME_PERIOD":    "year",
    "OBS_VALUE":      "ghg_total_t_co2e",
})
ghg = ghg[~ghg["iso3"].isin(EXCLUDE_AGGREGATES)]
ghg["year"] = ghg["year"].astype(int)
ghg = ghg[["iso3", "country", "year", "ghg_total_t_co2e"]].dropna(subset=["ghg_total_t_co2e"])

dups = ghg.duplicated(subset=["iso3", "year"]).sum()
assert dups == 0, f"GHG has {dups} duplicate country-year pairs after filtering -- check source file"

print(f"    {len(ghg):,} rows | {ghg['iso3'].nunique()} countries | "
      f"{ghg['year'].min()}-{ghg['year'].max()}")


# =============================================================================
# STEP 2 -- GHG PER CAPITA (tooltip layer for View 1, not used in Tapio calc)
# =============================================================================
print("[2/6] Loading GHG per capita (tooltip layer)...")

ghg_pc = pd.read_csv(
    os.path.join(RAW, FILES["ghg_pc"]),
    usecols=["REF_AREA", "TIME_PERIOD", "OBS_VALUE"],
    encoding="utf-8-sig",
)
ghg_pc = ghg_pc.rename(columns={
    "REF_AREA":    "iso3",
    "TIME_PERIOD": "year",
    "OBS_VALUE":   "ghg_per_capita_kg_co2e",
})
ghg_pc = ghg_pc[~ghg_pc["iso3"].isin(EXCLUDE_AGGREGATES)]
ghg_pc["year"] = ghg_pc["year"].astype(int)
ghg_pc = ghg_pc.dropna(subset=["ghg_per_capita_kg_co2e"])

print(f"    {len(ghg_pc):,} rows | {ghg_pc['iso3'].nunique()} countries")


# =============================================================================
# STEP 3 -- GDP PER CAPITA PPP (World Bank)
# =============================================================================
print("[3/6] Loading GDP per capita PPP (World Bank)...")

gdp_raw = pd.read_csv(os.path.join(RAW, FILES["gdp"]), skiprows=4, encoding="utf-8-sig")

year_cols = [c for c in gdp_raw.columns if c.isdigit() and 1990 <= int(c) <= 2023]
gdp = gdp_raw[["Country Name", "Country Code"] + year_cols].melt(
    id_vars=["Country Name", "Country Code"],
    var_name="year",
    value_name="gdp_pc_ppp_usd",
)
gdp = gdp.rename(columns={"Country Name": "country_wb", "Country Code": "iso3"})
gdp["year"] = gdp["year"].astype(int)
gdp = gdp.dropna(subset=["gdp_pc_ppp_usd"])

print(f"    {len(gdp):,} rows | {gdp['iso3'].nunique()} entities")


# =============================================================================
# STEP 4 -- PM2.5 MEAN CONCENTRATION (ug/m3)
# =============================================================================
print("[4/6] Loading PM2.5 mean concentration...")

# The PM2.5 file has 11 rows per country-year:
#   MEASURE=MEAN_POP + EXPOSURE_LEVEL=_Z  ->  mean concentration in ug/m3  (USE THIS)
#   MEASURE=POP_EXP_POL at 10 WHO threshold bands                           (IGNORE)
#
# Without this filter, the join creates 11x duplicate rows. pct_change() on
# duplicates returns 0.0, which triggers the near-zero GDP guard and marks
# every row as tapio_class='undefined'. This was the root cause of 88% undefined.

pm25_raw = pd.read_csv(
    os.path.join(RAW, FILES["pm25"]),
    usecols=["REF_AREA", "ISO", "TIME_PERIOD", "OBS_VALUE", "MEASURE", "EXPOSURE_LEVEL"],
    encoding="utf-8-sig",
    low_memory=False,
)

pm25 = pm25_raw[
    (pm25_raw["REF_AREA"]       == pm25_raw["ISO"]) &  # country aggregate, not sub-regions
    (pm25_raw["MEASURE"]        == "MEAN_POP")       &  # mean concentration
    (pm25_raw["EXPOSURE_LEVEL"] == "_Z")                # no threshold filter (aggregate)
].copy()

pm25 = pm25.rename(columns={
    "REF_AREA":    "iso3",
    "TIME_PERIOD": "year",
    "OBS_VALUE":   "pm25_ugm3",
})
pm25 = pm25[["iso3", "year", "pm25_ugm3"]].dropna(subset=["year"])
pm25["year"] = pm25["year"].astype(int)

dups = pm25.duplicated(subset=["iso3", "year"]).sum()
assert dups == 0, f"PM2.5 has {dups} duplicate country-year pairs -- filter is wrong"

print(f"    {len(pm25):,} rows | {pm25['iso3'].nunique()} countries | "
      f"{pm25['year'].min()}-{pm25['year'].max()}")
print(f"    Note: 1990 and 1995 only before 2001; no data 2021-2023 (show 2020 in UI)")


# =============================================================================
# STEP 5 -- MERGE PANEL
# =============================================================================
print("[5/6] Building merged panel...")

panel = pd.merge(
    ghg,
    gdp[["iso3", "year", "gdp_pc_ppp_usd"]],
    on=["iso3", "year"],
    how="inner",   # inner: only countries with both GHG and GDP
)
panel = pd.merge(
    panel,
    ghg_pc[["iso3", "year", "ghg_per_capita_kg_co2e"]],
    on=["iso3", "year"],
    how="left",
)
panel = pd.merge(
    panel,
    pm25,
    on=["iso3", "year"],
    how="left",    # left: PM2.5 only 1990-2020 so 2021-2023 will be NaN intentionally
)

# Fix display names for encoding-broken strings
panel["country"] = panel.apply(
    lambda r: DISPLAY_NAMES.get(r["iso3"], r["country"]), axis=1
)

assert panel.duplicated(subset=["iso3", "year"]).sum() == 0, \
    "Panel has duplicates after merge -- all source datasets must be 1 row per country-year"

print(f"    {len(panel):,} rows | {panel['iso3'].nunique()} countries | "
      f"{panel['year'].min()}-{panel['year'].max()}")
print(f"    PM2.5 coverage: {panel['pm25_ugm3'].notna().sum():,} rows "
      f"({panel['pm25_ugm3'].notna().mean()*100:.1f}%)")


# =============================================================================
# STEP 6 -- TAPIO ELASTICITY INDEX
# =============================================================================
print("[6/6] Computing Tapio Elasticity Index...")

panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

# Year-over-year % changes, grouped by country (never diff across country borders)
panel["ghg_pct_change"] = panel.groupby("iso3")["ghg_total_t_co2e"].pct_change() * 100
panel["gdp_pct_change"] = panel.groupby("iso3")["gdp_pc_ppp_usd"].pct_change() * 100

# Annual Tapio E = delta%GHG / delta%GDP
# Undefined only when: (a) first year of series -> NaN, or (b) near-zero GDP growth
panel["tapio_E"] = np.where(
    panel["gdp_pct_change"].abs() < 0.01,
    np.nan,
    panel["ghg_pct_change"] / panel["gdp_pct_change"],
)

# 5-year rolling mean of E -- use for the choropleth to smooth COVID outliers
# min_periods=3 so early years in the series still get a value
panel["tapio_E_5yr"] = (
    panel.groupby("iso3")["tapio_E"]
    .transform(lambda x: x.rolling(5, min_periods=3).mean())
)


def classify_tapio(e, gdp):
    """Tapio (2005) 8-class typology."""
    if pd.isna(e) or pd.isna(gdp):
        return "undefined"
    if gdp > 0:
        if e <= 0:    return "absolute_decoupling"
        elif e < 0.8: return "relative_decoupling"
        elif e < 1.2: return "expansive_coupling"
        else:         return "expansive_negative_decoupling"
    else:  # GDP contracting
        if e > 1.2:   return "recessive_decoupling"
        elif e > 0:   return "recessive_coupling"
        else:         return "strong_negative_decoupling"


panel["tapio_class"]     = panel.apply(lambda r: classify_tapio(r["tapio_E"],     r["gdp_pct_change"]), axis=1)
panel["tapio_class_5yr"] = panel.apply(lambda r: classify_tapio(r["tapio_E_5yr"], r["gdp_pct_change"]), axis=1)

undef = (panel["tapio_class"] == "undefined").sum()
first_yr = panel["ghg_pct_change"].isna().sum()
print(f"    Tapio distribution (annual):")
for cls, n in panel["tapio_class"].value_counts().items():
    print(f"      {cls:<40} {n:>5} rows ({n/len(panel)*100:.1f}%)")
print(f"    Breakdown of {undef} undefined: {first_yr} first-year NaN + "
      f"{undef - first_yr} genuine near-zero GDP growth")


# =============================================================================
# STEP 7 -- CLIMATE PROJECTIONS (chunked read for 1.5GB file)
# =============================================================================
print("[7/7] Loading climate projections...")

CLIM_PATH = os.path.join(RAW, FILES["climate"])

MEASURES_KEEP  = {"HOT_DAYS_PROJ", "TROP_NIGHTS_PROJ", "ICING_DAYS_PROJ"}
SCENARIOS_KEEP = {"PROJ_SSP126", "PROJ_SSP245", "PROJ_SSP370", "PROJ_SSP585"}
COLS_KEEP      = ["TERRITORIAL_LEVEL", "REF_AREA", "COUNTRY",
                  "MEASURE", "PROJ_SCENARIO", "TIME_PERIOD", "OBS_VALUE"]

SCENARIO_LABELS = {
    "PROJ_SSP126": "SSP1-2.6 (low emissions)",
    "PROJ_SSP245": "SSP2-4.5 (middle of the road)",
    "PROJ_SSP370": "SSP3-7.0 (high emissions)",
    "PROJ_SSP585": "SSP5-8.5 (very high emissions)",
}

# Mapping: current Tapio class -> most plausible SSP future (used in View 3)
TAPIO_TO_SSP = {
    "absolute_decoupling":            "PROJ_SSP126",
    "relative_decoupling":            "PROJ_SSP245",
    "expansive_coupling":             "PROJ_SSP370",
    "expansive_negative_decoupling":  "PROJ_SSP585",
    "recessive_decoupling":           "PROJ_SSP245",
    "recessive_coupling":             "PROJ_SSP370",
    "strong_negative_decoupling":     "PROJ_SSP585",
    "undefined":                      "PROJ_SSP245",
}

if not os.path.exists(CLIM_PATH):
    print(f"    Climate file not found at {CLIM_PATH}")
    print(f"    Skipping. Re-run once file is renamed to {FILES['climate']} in {RAW}/")
else:
    chunks = []
    rows_read = rows_kept = 0

    for chunk in pd.read_csv(
        CLIM_PATH,
        usecols=COLS_KEEP,
        encoding="utf-8-sig",
        chunksize=100_000,
        low_memory=False,
    ):
        rows_read += len(chunk)

        # Keep country-level rows only (drops all sub-national/regional rows)
        chunk = chunk[chunk["TERRITORIAL_LEVEL"] == "CTRY"]
        chunk = chunk[
            chunk["MEASURE"].isin(MEASURES_KEEP) &
            chunk["PROJ_SCENARIO"].isin(SCENARIOS_KEEP)
        ]

        if len(chunk) > 0:
            chunks.append(chunk)
            rows_kept += len(chunk)

        if rows_read % 500_000 == 0:
            print(f"    ... {rows_read:,} rows read, {rows_kept:,} kept")

    climate = pd.concat(chunks, ignore_index=True)
    climate = climate.rename(columns={
        "REF_AREA":      "iso3",
        "COUNTRY":       "country",
        "MEASURE":       "measure",
        "PROJ_SCENARIO": "scenario",
        "TIME_PERIOD":   "year",
        "OBS_VALUE":     "projected_days",
    })
    climate["country"] = climate.apply(
        lambda r: DISPLAY_NAMES.get(r["iso3"], r["country"]), axis=1
    )

    # Pivot: one row per (country, year, scenario), one column per measure
    climate_wide = climate.pivot_table(
        index=["iso3", "country", "year", "scenario"],
        columns="measure",
        values="projected_days",
        aggfunc="mean",
    ).reset_index()
    climate_wide.columns.name = None
    climate_wide = climate_wide.rename(columns={
        "HOT_DAYS_PROJ":    "hot_days_proj",
        "TROP_NIGHTS_PROJ": "trop_nights_proj",
        "ICING_DAYS_PROJ":  "icing_days_proj",
    })
    climate_wide["scenario_label"] = climate_wide["scenario"].map(SCENARIO_LABELS)

    # Link each country's latest Tapio class to its natural SSP scenario
    tapio_latest = (
        panel[panel["year"] == panel["year"].max()]
        [["iso3", "tapio_class"]]
        .copy()
    )
    tapio_latest["linked_ssp"] = tapio_latest["tapio_class"].map(TAPIO_TO_SSP)
    climate_wide = climate_wide.merge(tapio_latest[["iso3", "linked_ssp"]], on="iso3", how="left")
    climate_wide["is_linked_scenario"] = (climate_wide["scenario"] == climate_wide["linked_ssp"])

    print(f"    Read {rows_read:,} total rows, kept {rows_kept:,} country-level rows")
    print(f"    Climate table: {len(climate_wide):,} rows | "
          f"{climate_wide['iso3'].nunique()} countries | "
          f"{int(climate_wide['year'].min())}-{int(climate_wide['year'].max())}")

    clim_path = os.path.join(OUT, "climate_projections.csv")
    climate_wide.to_csv(clim_path, index=False)
    print(f"    Saved {clim_path}")


# =============================================================================
# SAVE PANEL
# =============================================================================
panel_path = os.path.join(OUT, "merged_panel.csv")
panel.to_csv(panel_path, index=False)

print(f"\nDone.")
print(f"  merged_panel.csv    -> {len(panel):,} rows, {panel['iso3'].nunique()} countries")
print(f"  Columns: {list(panel.columns)}")