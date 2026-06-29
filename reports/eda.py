"""
EDA script for the technical report.
Generates all figures saved to reports/figures/.
Run from the project root: python reports/eda.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "merged_panel.csv")
df = pd.read_csv(DATA_PATH)

# Color palette matching the dashboard
TAPIO_COLORS = {
    "absolute_decoupling":           "#2D5A27",
    "relative_decoupling":           "#A8C5A0",
    "expansive_coupling":            "#E8A87C",
    "expansive_negative_decoupling": "#C4623A",
    "recessive_decoupling":          "#8FAF8F",
    "recessive_coupling":            "#C4B49A",
    "strong_negative_decoupling":    "#A07060",
    "undefined":                     "#D9D9D9",
}

TAPIO_LABELS = {
    "absolute_decoupling":           "Absolute Decoupling",
    "relative_decoupling":           "Relative Decoupling",
    "expansive_coupling":            "Expansive Coupling",
    "expansive_negative_decoupling": "Expansive Negative Decoupling",
    "recessive_decoupling":          "Recessive Decoupling",
    "recessive_coupling":            "Recessive Coupling",
    "strong_negative_decoupling":    "Strong Negative Decoupling",
    "undefined":                     "Undefined",
}

plt.rcParams.update({
    "font.family":     "sans-serif",
    "font.size":       10,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.dpi":      150,
})


# ─────────────────────────────────────────
# FIGURE 1: MISSING VALUES HEATMAP
# ─────────────────────────────────────────

print("Generating Figure 1: Missing values heatmap...")

# Focus on key variables and years 2000–2023 for clarity
df_heat = df[df["year"] >= 2000].copy()

# For each country-year, mark which variables are missing
vars_to_check = {
    "GHG Total":   "ghg_total_t_co2e",
    "GDP per Cap": "gdp_pc_ppp_usd",
    "GHG per Cap": "ghg_per_capita_kg_co2e",
    "PM2.5":       "pm25_ugm3",
    "Tapio E":     "tapio_E",
}

# Build a pivot: rows = variable, cols = year, value = % countries with data
coverage = {}
for label, col in vars_to_check.items():
    yearly = df_heat.groupby("year")[col].apply(lambda x: x.notna().mean() * 100)
    coverage[label] = yearly

coverage_df = pd.DataFrame(coverage).T

fig, ax = plt.subplots(figsize=(12, 3.5))
sns.heatmap(
    coverage_df,
    ax=ax,
    cmap="YlGn",
    vmin=0, vmax=100,
    linewidths=0.4,
    linecolor="#e0e0e0",
    annot=False,
    cbar_kws={"label": "% Countries with Data", "shrink": 0.8},
)
ax.set_title("Data Coverage by Variable and Year (2000–2023)", fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=45, labelsize=8)
ax.tick_params(axis="y", rotation=0, labelsize=9)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig1_missing_values.png"), bbox_inches="tight")
plt.close()
print("  Saved fig1_missing_values.png")


# ─────────────────────────────────────────
# FIGURE 2: TAPIO DISTRIBUTION OVER TIME
# ─────────────────────────────────────────

print("Generating Figure 2: Tapio distribution over time...")

# Count countries per class per year (annual, not 5yr)
category_order = [
    "absolute_decoupling",
    "relative_decoupling",
    "expansive_coupling",
    "expansive_negative_decoupling",
    "recessive_decoupling",
    "recessive_coupling",
    "strong_negative_decoupling",
    "undefined",
]

df_plot = df[df["year"] >= 1991].copy()  # exclude first year (all undefined)
tapio_by_year = (
    df_plot.groupby(["year", "tapio_class"])
    .size()
    .unstack(fill_value=0)
)

# Reorder columns
tapio_by_year = tapio_by_year.reindex(columns=category_order, fill_value=0)

fig, ax = plt.subplots(figsize=(12, 5))
bottom = np.zeros(len(tapio_by_year))

for cat in category_order:
    if cat not in tapio_by_year.columns:
        continue
    values = tapio_by_year[cat].values
    ax.bar(
        tapio_by_year.index,
        values,
        bottom=bottom,
        color=TAPIO_COLORS[cat],
        label=TAPIO_LABELS[cat],
        width=0.8,
    )
    bottom += values

ax.set_title("Tapio Classification Distribution Across Countries (1991–2023)",
             fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Number of Countries", fontsize=10)
ax.tick_params(axis="x", rotation=45, labelsize=8)

# Highlight COVID year
ax.axvline(x=2020, color="#888", linestyle="--", linewidth=1, alpha=0.7)
ax.text(2020.2, ax.get_ylim()[1] * 0.95, "COVID-19", fontsize=8, color="#888")

# Legend outside
handles = [
    mpatches.Patch(color=TAPIO_COLORS[cat], label=TAPIO_LABELS[cat])
    for cat in category_order
]
ax.legend(handles=handles, bbox_to_anchor=(1.01, 1), loc="upper left",
          fontsize=8, frameon=False)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig2_tapio_distribution.png"), bbox_inches="tight")
plt.close()
print("  Saved fig2_tapio_distribution.png")


# ─────────────────────────────────────────
# FIGURE 3: GHG VS GDP SCATTER
# ─────────────────────────────────────────

print("Generating Figure 3: GHG vs GDP scatter...")

# Use 2000 and 2023 to show the shift
df_2000 = df[df["year"] == 2000].dropna(subset=["gdp_pc_ppp_usd", "ghg_per_capita_kg_co2e"])
df_2023 = df[df["year"] == 2023].dropna(subset=["gdp_pc_ppp_usd", "ghg_per_capita_kg_co2e"])

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

for ax, data, year in zip(axes, [df_2000, df_2023], [2000, 2023]):
    colors = [TAPIO_COLORS.get(c, "#D9D9D9") for c in data["tapio_class"]]
    ax.scatter(
        data["gdp_pc_ppp_usd"] / 1000,
        data["ghg_per_capita_kg_co2e"] / 1000,
        c=colors,
        alpha=0.8,
        s=60,
        edgecolors="white",
        linewidths=0.5,
    )

    # Label a few notable countries
    for _, row in data[data["iso3"].isin(["USA", "DEU", "CHN", "IND", "NOR", "AUS"])].iterrows():
        ax.annotate(
            row["iso3"],
            (row["gdp_pc_ppp_usd"] / 1000, row["ghg_per_capita_kg_co2e"] / 1000),
            fontsize=7, color="#444",
            xytext=(4, 4), textcoords="offset points",
        )

    ax.set_title(f"{year}", fontsize=11, fontweight="bold")
    ax.set_xlabel("GDP per Capita PPP (thousands USD)", fontsize=9)
    ax.set_ylabel("GHG per Capita (tonnes CO₂e)", fontsize=9)

fig.suptitle("GDP per Capita vs GHG Emissions per Capita: 2000 vs 2023",
             fontsize=12, fontweight="bold", y=1.02)

# Shared legend
handles = [
    mpatches.Patch(color=TAPIO_COLORS[cat], label=TAPIO_LABELS[cat])
    for cat in ["absolute_decoupling", "relative_decoupling",
                "expansive_coupling", "expansive_negative_decoupling"]
]
fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8,
           frameon=False, bbox_to_anchor=(0.5, -0.08))

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig3_ghg_gdp_scatter.png"), bbox_inches="tight")
plt.close()
print("  Saved fig3_ghg_gdp_scatter.png")


# ─────────────────────────────────────────
# FIGURE 4: PM2.5 TIME SERIES
# ─────────────────────────────────────────

print("Generating Figure 4: PM2.5 time series...")

# Select a few representative countries across regions
selected = {
    "DEU": "Germany",
    "USA": "United States",
    "POL": "Poland",
    "JPN": "Japan",
    "IND": "India",
    "CHN": "China",
}

line_colors = ["#2D5A27", "#C4623A", "#A8C5A0", "#E8A87C", "#8FAF8F", "#A07060"]

df_pm25 = df[
    df["iso3"].isin(selected.keys()) &
    df["pm25_ugm3"].notna()
].copy()

fig, ax = plt.subplots(figsize=(11, 5))

for (iso, name), color in zip(selected.items(), line_colors):
    country_data = df_pm25[df_pm25["iso3"] == iso].sort_values("year")
    if country_data.empty:
        continue
    ax.plot(
        country_data["year"],
        country_data["pm25_ugm3"],
        label=name,
        color=color,
        linewidth=2,
        marker="o",
        markersize=3,
    )

# WHO guideline
ax.axhline(y=5, color="#888", linestyle="--", linewidth=1, alpha=0.8)
ax.text(2000.5, 5.4, "WHO guideline (5 µg/m³)", fontsize=8, color="#888")

# Mark data gap
ax.axvspan(2020.5, 2023, alpha=0.08, color="#888")
ax.text(2021, ax.get_ylim()[1] * 0.85, "No data\n2021–2023",
        fontsize=8, color="#888", ha="center")

ax.set_title("PM2.5 Mean Population Exposure Over Time — Selected Countries",
             fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("PM2.5 Concentration (µg/m³)", fontsize=10)
ax.legend(fontsize=9, frameon=False)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig4_pm25_timeseries.png"), bbox_inches="tight")
plt.close()
print("  Saved fig4_pm25_timeseries.png")


print("\nAll figures saved to reports/figures/")