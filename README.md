# Breaking the Link

**Data Visualization project: interactive dashboard visualizing the decoupling of GDP growth and GHG emissions**

Can a nation expand its economy while simultaneously shrinking its environmental footprint? This dashboard explores the *Green Growth* hypothesis across 90 countries from 1990 to 2023, combining economic, environmental, and climate projection data into an interactive map-based visualization.

🌍 **Live dashboard:** https://breaking-the-link-economic-decoupling-dataviz.streamlit.app  
🎥 **Demo video:** https://www.youtube.com/watch?v=PLACEHOLDER

---

## What the dashboard shows

The project is built around the **Tapio Decoupling Elasticity Index** — a measure of how tightly a country's GHG emissions are coupled to its GDP growth. Countries are classified into seven categories ranging from *Absolute Decoupling* (GDP growing, emissions falling) to *Strong Negative Decoupling* (GDP falling, emissions rising).

The dashboard has two views, selectable from the top navigation bar:

| View | Script | Description |
|------|--------|-------------|
| **Decoupling Map** | `view1.py` | World map coloured by Tapio decoupling status, with per-country gradient based on the actual elasticity value. Toggle between annual and 5-year rolling average to smooth short-term shocks — such as the COVID-2020 disruption — and reveal underlying long-term trends. |
| **Air Quality Layer** | `view2.py` | Optional layer toggled within the Decoupling Map. Overlays sub-national PM2.5 concentration bubbles (723 regions across 52 countries) sized and coloured on a clean-to-hazardous scale. Dims the underlying choropleth while active. |
| **Future Scenarios** | `view3.py` | Forward-looking view linking each country's current decoupling trajectory to an SSP climate scenario, showing projected change in hot days, tropical nights, and icing days relative to the 1981–2010 baseline, out to 2060. Click any country to explore all four SSP pathways. |

---

## Data sources

| Dataset | Source | Coverage |
|---------|--------|----------|
| GHG total emissions | OECD Data Explorer (`DSD_AIR_GHG@DF_AIR_GHG`) | 1985–2023 |
| GDP per capita PPP | World Bank Open Data (`NY.GDP.PCAP.PP.CD`) | 1990–2023 |
| PM2.5 air pollution | OECD Data Explorer (`DSD_AIR_POL@DF_AIR_POLL`) | 1990–2020 |
| Climate projections | OECD Data Explorer (`DSD_REG_CLIM@DF_CLIM_PROJ`) | 2030–2060 |

Raw data files are not included in this repository due to licensing restrictions. See the **Replication** section below for download instructions.

---

## Repository structure

```
├── .streamlit/
│   └── config.toml         ← Theme configuration
├── dashboard/
│   ├── app.py              ← Streamlit entry point
│   ├── view1.py            ← Tapio choropleth map
│   ├── view2.py            ← PM2.5 bubble overlay
│   ├── view3.py            ← Climate projections
│   └── style.py            ← Shared colour tokens and CSS
├── data/
│   ├── raw/                ← Raw source files (not committed, see below)
│   └── processed/          ← Pipeline outputs (committed)
├── reports/                ← Course deliverables (technical report + final report, PDFs), not needed to run the dashboard
├── geocode.py              ← Geocodes PM2.5 regions via Nominatim
├── panel.py                ← Data preprocessing pipeline
├── requirements.txt
└── README.md
```

---

## Replication

### 1. Clone the repository

```bash
git clone https://github.com/kristine-p/economic-decoupling-dataviz.git
cd economic-decoupling-dataviz
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download raw data

Download the following files from their respective sources and place them in `data/raw/`:

| File | Source |
|------|--------|
| `GHG_all.csv` | [OECD Data Explorer](https://data-explorer.oecd.org) → Air and GHG Emissions (`DSD_AIR_GHG@DF_AIR_GHG`) |
| `GHGpercapita.csv` | Same OECD dataset, per capita measure |
| `GDP_PPPadjusted.csv` | [World Bank](https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.CD) → Download → CSV |
| `PM2.5.csv` | [OECD Data Explorer](https://data-explorer.oecd.org) → Exposure to Air Pollution (`DSD_AIR_POL@DF_AIR_POLL`) |
| `CLIM_PROJ_all.csv` | [OECD Data Explorer](https://data-explorer.oecd.org) → Climate Projections (`DSD_REG_CLIM@DF_CLIM_PROJ`) — ~1.5 GB |

### 4. Run the preprocessing pipeline

```bash
python3 panel.py
```

This produces `data/processed/merged_panel.csv`, `data/processed/pm25_regions.csv`, and `data/processed/climate_projections.csv`.

### 5. Geocode PM2.5 regions *(optional — already committed)*

The geocoded file `data/processed/pm25_regions_geocoded.csv` is already included in the repository. Only re-run this step if you need to regenerate it:

```bash
python3 geocode.py
```

Note: this makes ~723 requests to the Nominatim API at 1.2 second intervals and takes approximately 15 minutes.

### 6. Launch the dashboard

```bash
cd dashboard
streamlit run app.py
```

---

## Authors

| Name | GitHub |
|------|--------|
| Kristine Paegle | [@kristine-p](https://github.com/kristine-p) |
| Giuseppe Pio Mangiacotti | [@givmangi](https://github.com/givmangi) |
| Martin Krisak | [@martin-kri](https://github.com/martin-kri) |