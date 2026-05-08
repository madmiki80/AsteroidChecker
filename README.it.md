# ASTEROIDADVISOR ☄️

Una dashboard interattiva per **Oggetti Near-Earth (NEO)** basata sull'API NeoWs della NASA. Esplora, filtra e visualizza gli asteroidi in avvicinamento con un sistema di punteggio di rischio in tempo reale.

## Funzionalità

- **📡 Feed NEO** — Recupera dati sugli asteroidi per intervallo di date con cache intelligente (DiskCache + CSV)
- **🔭 Esplora Catalogo** — Navigazione paginata del catalogo NEO completo della NASA
- **☄️ Punteggio di Rischio** — Modello multi-fattore (dimensione 30%, velocità 20%, distanza 30%, flag NASA 20%)
- **🌡️ Mappa di Calore** — Rischio medio giornaliero visualizzato come heatmap stile GitHub
- **📈 Serie Temporale** — Punteggio di rischio medio e massimo nel tempo
- **🏆 Classifiche** — Top 10 avvicinamenti e asteroidi a più alto rischio
- **📊 Grafici** — Distribuzioni di dimensione/velocità/distanza, scatter plot, istogrammi
- **🔬 Dettaglio** — Gauge del rischio, metriche e badge per ogni asteroide
- **💾 Cache Persistente** — Cache JSON grezza (TTL 1h) + file CSV puliti
- **🌐 Bilingue** — English / Italiano

## Avvio Rapido

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Chiave API

L'app funziona subito con `DEMO_KEY` della NASA (30 richieste/h). Per uso intensivo, ottieni una chiave gratuita su https://api.nasa.gov/ e impostala in uno di questi modi:

- File `.env`: `NASA_API_KEY=la_tua_chiave`
- File `.streamlit/secrets.toml`: `NASA_API_KEY = "la_tua_chiave"`

## Struttura del Progetto

```
├── app.py                     # Punto di ingresso
├── src/
│   ├── dashboard.py           # UI Streamlit, grafici, layout
│   ├── data_processing.py     # Cache CSV, statistiche, classifiche
│   ├── neo_ws_client.py       # Client NASA NeoWs, punteggio rischio
│   └── translations.py        # Traduzioni EN / IT
├── cache/                     # Cache JSON grezza (creata automaticamente)
├── data/                      # File CSV puliti (creati automaticamente)
├── .streamlit/
│   ├── config.toml            # Tema e configurazione server Streamlit
│   └── secrets.toml           # Chiave API NASA (gitignorato)
└── requirements.txt
```

## Punteggio di Rischio

Ogni asteroide riceve un punteggio `0.0 – 1.0` basato su:

| Fattore | Peso | Dettaglio |
|---|---|---|
| Dimensione | 30% | Scala log, più grande = rischio maggiore |
| Velocità | 20% | Più veloce = rischio maggiore |
| Distanza di mancato | 30% | Più vicino = rischio maggiore |
| Flag NASA | 20% | Bonus se segnalato come PHO |

**Soglie:** ≥0.8 ALTO · ≥0.6 MEDIO (default) · ≥0.2 BASSO · &lt;0.2 NESSUNO

## Stack Tecnologico

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?logo=plotly&logoColor=fff)](https://plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=fff)](https://pandas.pydata.org/)
[![NASA API](https://img.shields.io/badge/NASA_NeoWs-0B3D91?logo=nasa&logoColor=fff)](https://api.nasa.gov/)


## Vedi su streamlit l'app !!
https://asteroidchecker.streamlit.app/