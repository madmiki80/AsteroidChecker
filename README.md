# ASTEROIDADVISOR ☄️

An interactive **Near-Earth Object (NEO) dashboard** powered by NASA's NeoWs API. Browse, filter, and visualize asteroid close approaches with a real-time risk scoring system.

## Features

- **📡 NEO Feed** — Fetch asteroid data by date range with smart caching (DiskCache + CSV)
- **🔭 Browse Catalog** — Paginated browse of NASA's full NEO catalog
- **☄️ Risk Scoring** — Multi-factor risk model (size 30%, speed 20%, distance 30%, NASA hazard flag 20%)
- **🌡️ GitHub-style Heatmap** — Daily average risk visualized as a heatmap
- **📈 Time Series** — Average and max risk scores over time
- **🏆 Rankings** — Top 10 closest approaches and highest-risk asteroids
- **📊 Charts** — Size/speed/distance distributions, scatter plots, histograms
- **🔬 Detail View** — Per-asteroid gauge, metrics, and risk badge
- **💾 Persistent Cache** — Raw JSON cache (1h TTL) + cleaned CSV files
- **🌐 Bilingual** — English / Italiano

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

### API Key

The app works out of the box with NASA's `DEMO_KEY` (30 req/h). For production use, get a free API key at https://api.nasa.gov/ and set it in one of:

- `.env` file: `NASA_API_KEY=your_key_here`
- `.streamlit/secrets.toml`: `NASA_API_KEY = "your_key_here"`

## Project Structure

```
├── app.py                     # Entry point
├── src/
│   ├── dashboard.py           # Streamlit UI, charts, layout
│   ├── data_processing.py     # CSV caching, stats, rankings
│   ├── neo_ws_client.py       # NASA NeoWs client, risk scoring
│   └── translations.py        # EN / IT translations
├── cache/                     # Raw JSON cache (auto-created)
├── data/                      # Cleaned CSV files (auto-created)
├── .streamlit/
│   ├── config.toml            # Streamlit theme & server config
│   └── secrets.toml           # NASA API key (gitignored)
└── requirements.txt
```

## Risk Scoring

Each asteroid receives a score `0.0 – 1.0` based on:

| Factor | Weight | Detail |
|---|---|---|
| Size | 30% | Log scale, larger = higher risk |
| Speed | 20% | Faster = higher risk |
| Miss Distance | 30% | Closer = higher risk |
| NASA Hazard Flag | 20% | Bonus if flagged as PHO |

**Thresholds:** ≥0.8 HIGH · ≥0.6 MEDIUM (default) · ≥0.2 LOW · &lt;0.2 NONE

## Tech Stack

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?logo=plotly&logoColor=fff)](https://plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=fff)](https://pandas.pydata.org/)
[![NASA API](https://img.shields.io/badge/NASA_NeoWs-0B3D91?logo=nasa&logoColor=fff)](https://api.nasa.gov/)


## See it working !!
https://asteroidchecker.streamlit.app/