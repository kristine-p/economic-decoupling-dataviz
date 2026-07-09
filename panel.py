#!/usr/bin/env python3
"""
Preprocess raw OECD and World Bank data into a single panel for the decoupling dataviz
v4 -- adds region-level PM2.5 output and 5-year rolling PM2.5 averages.
v5 -- climate projections now also carry each measure's change vs. the
      1981-2010 baseline (as published directly in the OECD file, e.g.
      MEASURE=HOT_DAYS_PROJ_DIFF_1981_2010), plus a derived percentage-change
      column computed from that diff and the absolute projected value.
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

DISPLAY_NAMES = {
    "TUR": "Turkiye",
    "CHN": "China (People's Republic of)",
    "CIV": "Cote d'Ivoire",
    "KOR": "Korea",
    "CZE": "Czechia",
}



print("\n[1/7] Loading GHG total emissions...")

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

print("[2/7] Loading GHG per capita (tooltip layer)...")

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


print("[3/7] Loading GDP per capita PPP (World Bank)...")

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


print("[4/7] Loading PM2.5 mean concentration (country + region level)...")

# The PM2.5 file has 11 rows per country/region-year:
#   MEASURE=MEAN_POP + EXPOSURE_LEVEL=_Z  ->  mean concentration in ug/m3  (USE THIS)
#   MEASURE=POP_EXP_POL at 10 WHO threshold bands                           (IGNORE)
#
# Without this filter, the join creates 11x duplicate rows. pct_change() on
# duplicates returns 0.0, which triggers the near-zero GDP guard and marks
# every row as tapio_class='undefined'. This was the root cause of 88% undefined.
#
# The file also encodes BOTH country aggregates AND sub-national regions:
#   REF_AREA == ISO  ->  the row IS the country aggregate
#   REF_AREA != ISO  ->  the row is a sub-national region (e.g. FR1 = Ile-de-France,
#                        parent ISO = FRA). Previously these region rows were
#                        silently dropped -- v4 keeps them as a separate output table.

pm25_raw = pd.read_csv(
    os.path.join(RAW, FILES["pm25"]),
    usecols=["REF_AREA", "Reference area", "ISO", "ISO.1",
             "TIME_PERIOD", "OBS_VALUE", "MEASURE", "EXPOSURE_LEVEL"],
    encoding="utf-8-sig",
    low_memory=False,
)

pm25_clean = pm25_raw[
    (pm25_raw["MEASURE"]        == "MEAN_POP") &  # mean concentration
    (pm25_raw["EXPOSURE_LEVEL"] == "_Z")           # no threshold filter (aggregate)
].copy()

# --- 4a. Country level ---
pm25 = pm25_clean[pm25_clean["REF_AREA"] == pm25_clean["ISO"]].copy()
pm25 = pm25.rename(columns={
    "REF_AREA":    "iso3",
    "TIME_PERIOD": "year",
    "OBS_VALUE":   "pm25_ugm3",
})
pm25 = pm25[["iso3", "year", "pm25_ugm3"]].dropna(subset=["year"])
pm25["year"] = pm25["year"].astype(int)
pm25 = pm25.sort_values(["iso3", "year"])

# 5-year rolling mean, same pattern used for tapio_E_5yr below (min_periods=3)
pm25["pm25_ugm3_5yr"] = (
    pm25.groupby("iso3")["pm25_ugm3"]
    .transform(lambda x: x.rolling(5, min_periods=3).mean())
)

dups = pm25.duplicated(subset=["iso3", "year"]).sum()
assert dups == 0, f"PM2.5 has {dups} duplicate country-year pairs -- filter is wrong"

print(f"    Country level: {len(pm25):,} rows | {pm25['iso3'].nunique()} countries | "
      f"{pm25['year'].min()}-{pm25['year'].max()}")

# --- 4b. Region level (new) ---
pm25_region = pm25_clean[pm25_clean["REF_AREA"] != pm25_clean["ISO"]].copy()
pm25_region = pm25_region.rename(columns={
    "REF_AREA":      "region_code",
    "Reference area":"region_name",
    "ISO":           "iso3",
    "ISO.1":         "country",
    "TIME_PERIOD":   "year",
    "OBS_VALUE":     "pm25_ugm3",
})
pm25_region = pm25_region[
    ["region_code", "region_name", "iso3", "country", "year", "pm25_ugm3"]
].dropna(subset=["year"])
pm25_region["year"] = pm25_region["year"].astype(int)
pm25_region = pm25_region.sort_values(["region_code", "year"])

pm25_region["pm25_ugm3_5yr"] = (
    pm25_region.groupby("region_code")["pm25_ugm3"]
    .transform(lambda x: x.rolling(5, min_periods=3).mean())
)

dups = pm25_region.duplicated(subset=["region_code", "year"]).sum()
assert dups == 0, f"PM2.5 regions has {dups} duplicate region-year pairs -- filter is wrong"

print(f"    Region level:  {len(pm25_region):,} rows | {pm25_region['region_code'].nunique()} regions "
      f"across {pm25_region['iso3'].nunique()} countries")
print(f"    Note: 1990 and 1995 only before 2001; no data 2021-2023 (show 2020 in UI)")


print("[5/7] Building merged panel...")

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
print(f"    PM2.5 5yr coverage: {panel['pm25_ugm3_5yr'].notna().sum():,} rows "
      f"({panel['pm25_ugm3_5yr'].notna().mean()*100:.1f}%)")


print("[6/7] Computing Tapio Elasticity Index...")

panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

# Year-over-year % changes, grouped by country (never diff across country borders)
panel["ghg_pct_change"] = panel.groupby("iso3")["ghg_total_t_co2e"].pct_change() * 100
panel["gdp_pct_change"] = panel.groupby("iso3")["gdp_pc_ppp_usd"].pct_change() * 100

# Annual Tapio E = delta%GHG / delta%GDP
# Undefined only when:
#   first year of series == NaN
#   or 
#   near-zero GDP growth
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

# Final column order
panel = panel[[
    "iso3", "country", "year",
    "ghg_total_t_co2e", "gdp_pc_ppp_usd", "ghg_per_capita_kg_co2e",
    "pm25_ugm3", "pm25_ugm3_5yr",
    "ghg_pct_change", "gdp_pct_change",
    "tapio_E", "tapio_E_5yr", "tapio_class", "tapio_class_5yr",
]]


print("[7/7] Loading climate projections...")

CLIM_PATH = os.path.join(RAW, FILES["climate"])

# Absolute projected-day measures (as before)...
BASE_MEASURES = {"HOT_DAYS_PROJ", "TROP_NIGHTS_PROJ", "ICING_DAYS_PROJ"}

# ...and each one's published change vs. the 1981-2010 historical baseline,
# e.g. MEASURE=HOT_DAYS_PROJ_DIFF_1981_2010, OBS_VALUE in days/year. We keep
# both the absolute projection and the baseline diff, then derive a
# percentage-change column from the two (see below).
DIFF_SUFFIX = "_DIFF_1981_2010"
DIFF_MEASURES = {f"{m}{DIFF_SUFFIX}" for m in BASE_MEASURES}
MEASURES_KEEP = BASE_MEASURES | DIFF_MEASURES

SCENARIOS_KEEP = {"PROJ_SSP126", "PROJ_SSP245", "PROJ_SSP370", "PROJ_SSP585"}
COLS_KEEP      = ["TERRITORIAL_LEVEL", "REF_AREA", "COUNTRY",
                  "MEASURE", "PROJ_SCENARIO", "TIME_PERIOD", "OBS_VALUE"]

SCENARIO_LABELS = {
    "PROJ_SSP126": "SSP1-2.6 (low emissions)",
    "PROJ_SSP245": "SSP2-4.5 (middle of the road)",
    "PROJ_SSP370": "SSP3-7.0 (high emissions)",
    "PROJ_SSP585": "SSP5-8.5 (very high emissions)",
}

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

# Suppress pct-change only when the 1981-2010 historical baseline is truly
# indistinguishable from zero (floating-point rounding artifact, e.g. a
# country with literally zero hot days or zero icing days historically).
# Using 1.0 was too aggressive: cold-climate countries often have a valid
# but small baseline -- e.g. Austria's hot-days average is ~0.2 days/yr --
# and were being silently dropped, causing them to show 'no baseline' in
# view3.  0.01 keeps only the genuine divide-by-zero cases.
BASELINE_EPS_DAYS = 0.01

if not os.path.exists(CLIM_PATH):
    print(f"    Climate file not found at {CLIM_PATH}")
    print(f"    Skipping. Re-run once file is renamed to {FILES['climate']} in {RAW}/")
    climate_wide = None
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

        chunk = chunk[chunk["TERRITORIAL_LEVEL"] == "CTRY"]
        chunk = chunk[
            chunk["MEASURE"].isin(MEASURES_KEEP) &
            chunk["PROJ_SCENARIO"].isin(SCENARIOS_KEEP)
        ]
        # guard against stray non-numeric rows (e.g. a duplicated header line
        # embedded in the data) silently turning OBS_VALUE into a string
        # column for the whole file once chunks are concatenated
        bad_before = len(chunk)
        chunk = chunk.copy()
        chunk["OBS_VALUE"] = pd.to_numeric(chunk["OBS_VALUE"], errors="coerce")
        chunk = chunk.dropna(subset=["OBS_VALUE"])
        if len(chunk) < bad_before and bad_before > 0:
            print(f"    ... dropped {bad_before - len(chunk)} row(s) with non-numeric OBS_VALUE")

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

    climate_wide = climate.pivot_table(
        index=["iso3", "country", "year", "scenario"],
        columns="measure",
        values="projected_days",
        aggfunc="mean",
    ).reset_index()
    climate_wide.columns.name = None

    # rename whichever absolute/diff measure columns actually came back from
    # the source file -- don't assume every base metric has a matching diff
    # column, some regions/metrics may not publish one.
    rename_map = {}
    for m in BASE_MEASURES:
        if m in climate_wide.columns:
            rename_map[m] = m.lower()
        diff_col = f"{m}{DIFF_SUFFIX}"
        if diff_col in climate_wide.columns:
            rename_map[diff_col] = f"{m.lower()}_diff_1981_2010"
    climate_wide = climate_wide.rename(columns=rename_map)

    # derive % change vs. the 1981-2010 baseline for every metric that has
    # both its absolute projection and its diff column present:
    #   baseline   = projected - diff       (diff is defined as projected - baseline)
    #   pct_change = diff / baseline * 100, undefined (NaN) when the baseline
    #                is too close to zero to make a percentage meaningful
    pct_change_cols = []
    for m in BASE_MEASURES:
        abs_col  = m.lower()
        diff_col = f"{m.lower()}_diff_1981_2010"
        pct_col  = f"{m.lower()}_pct_change_1981_2010"
        if abs_col in climate_wide.columns and diff_col in climate_wide.columns:
            baseline = climate_wide[abs_col] - climate_wide[diff_col]
            climate_wide[pct_col] = np.where(
                baseline.abs() < BASELINE_EPS_DAYS,
                np.nan,
                climate_wide[diff_col] / baseline * 100,
            )
            pct_change_cols.append(pct_col)
        else:
            print(f"    Note: no {DIFF_SUFFIX} measure found for {m} -- "
                  f"skipping its percentage-change column")

    climate_wide["scenario_label"] = climate_wide["scenario"].map(SCENARIO_LABELS)

    # Per-country tapio lookup: for each country use their own latest year in
    # the panel, not a single global reference year.  A single global year
    # fails for countries whose panel data ends before that year (e.g. CHN,
    # COL, CRI, IND, PER whose GDP series ends at 2021), leaving them with
    # linked_ssp = NaN and hiding them from the "Current trajectory" view.
    #
    # Strategy:
    #   1. For each country keep only the rows where tapio_class is not
    #      'undefined' (first-year NaN, near-zero GDP, genuine undefined).
    #   2. From those, take the most recent year per country.
    #   3. Fall back to any year (even 'undefined') if no non-undefined row
    #      exists, so at least the country gets SOME linked_ssp.
    panel_defined = panel[panel["tapio_class"] != "undefined"].copy()
    tapio_per_country = (
        panel_defined
        .sort_values("year")
        .groupby("iso3", as_index=False)
        .last()[["iso3", "tapio_class"]]
    )
    # Fallback: countries where every year is 'undefined' -- use absolute
    # latest year regardless
    all_countries_latest = (
        panel
        .sort_values("year")
        .groupby("iso3", as_index=False)
        .last()[["iso3", "tapio_class"]]
    )
    tapio_per_country = pd.concat(
        [tapio_per_country,
         all_countries_latest[~all_countries_latest["iso3"].isin(tapio_per_country["iso3"])]],
        ignore_index=True,
    )

    tapio_per_country["linked_ssp"] = tapio_per_country["tapio_class"].map(TAPIO_TO_SSP)
    climate_wide = climate_wide.merge(
        tapio_per_country[["iso3", "linked_ssp"]], on="iso3", how="left"
    )
    climate_wide["is_linked_scenario"] = (
        climate_wide["linked_ssp"].notna() &
        (climate_wide["scenario"] == climate_wide["linked_ssp"])
    )

    n_linked = climate_wide[climate_wide["is_linked_scenario"]].groupby("iso3").ngroups
    print(f"    Per-country latest tapio used for linked SSP -- "
          f"{n_linked}/{climate_wide['iso3'].nunique()} countries have a valid linked scenario")

    print(f"    Read {rows_read:,} total rows, kept {rows_kept:,} country-level rows")
    print(f"    Climate table: {len(climate_wide):,} rows | "
          f"{climate_wide['iso3'].nunique()} countries | "
          f"{int(climate_wide['year'].min())}-{int(climate_wide['year'].max())}")
    for pct_col in pct_change_cols:
        cov = climate_wide[pct_col].notna().mean() * 100
        print(f"    {pct_col}: {cov:.1f}% coverage "
              f"(rest undefined -- baseline within +/-{BASELINE_EPS_DAYS:g} days of zero)")

    clim_path = os.path.join(OUT, "climate_projections.csv")
    climate_wide.to_csv(clim_path, index=False)
    print(f"    Saved {clim_path}")


panel_path = os.path.join(OUT, "merged_panel.csv")
panel.to_csv(panel_path, index=False)

region_path = os.path.join(OUT, "pm25_regions.csv")
pm25_region.to_csv(region_path, index=False)

print(f"\nDone.")
print(f"  merged_panel.csv  -> {len(panel):,} rows, {panel['iso3'].nunique()} countries")
print(f"  pm25_regions.csv  -> {len(pm25_region):,} rows, {pm25_region['region_code'].nunique()} regions")
print(f"  Panel columns: {list(panel.columns)}")