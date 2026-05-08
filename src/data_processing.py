import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.neo_ws_client import (
    NeoWsClient,
    flatten_feed,
    _extract_approach,
    _build_record,
    CACHE_DIR,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


ESSENTIAL_COLS = [
    "id",
    "name",
    "date",
    "diameter_min_m",
    "diameter_max_m",
    "diameter_avg_m",
    "close_approach_date",
    "velocity_kmh",
    "miss_distance_km",
    "is_hazardous",
    "is_high_risk",
    "orbiting_body",
    "risk_score",
    "risk_label",
]


def _range_key(start_date, end_date):
    return f"feed_{start_date}_{end_date}"


def _csv_path(start_date, end_date):
    return DATA_DIR / f"{_range_key(start_date, end_date)}.csv"


def process_feed_to_frame(raw_json):
    records = flatten_feed(raw_json)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    missing = [c for c in ESSENTIAL_COLS if c not in df.columns]
    for c in missing:
        df[c] = ""
    return df[ESSENTIAL_COLS]


def save_feed_csv(raw_json, start_date, end_date):
    df = process_feed_to_frame(raw_json)
    if df.empty:
        return None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = _csv_path(start_date, end_date)
    df.to_csv(path, index=False)
    return path


def load_feed_csv(start_date, end_date):
    path = _csv_path(start_date, end_date)
    if path.exists():
        return pd.read_csv(path)
    return None


def has_feed_csv(start_date, end_date):
    return _csv_path(start_date, end_date).exists()


def load_merged_csvs(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    chunks = []
    current = start
    while current <= end:
        cs = current.strftime("%Y-%m-%d")
        df = load_feed_csv(cs, cs)
        if df is not None and not df.empty:
            chunks.append(df)
        current += timedelta(days=1)

    if not chunks:
        return None
    merged = pd.concat(chunks, ignore_index=True)
    merged = merged.drop_duplicates(subset=["id"])
    return merged


def fetch_and_cache(start_date, end_date, force_refresh=False, progress_callback=None):
    client = NeoWsClient()
    raw, info = client.get_feed_range(
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
        progress_callback=progress_callback,
    )

    saved_paths = []
    for date, asteroids in raw.get("near_earth_objects", {}).items():
        chunk = {"near_earth_objects": {date: asteroids}, "element_count": len(asteroids)}
        chunk_sd = date
        chunk_ed = date
        path = save_feed_csv(chunk, chunk_sd, chunk_ed)
        if path:
            saved_paths.append(path)

    merged = load_merged_csvs(start_date, end_date)
    return merged, info, saved_paths


def convert_cached_json_to_csv(ttl_seconds=3600):
    converted = []
    for path in sorted(CACHE_DIR.glob("feed_*.json")):
        age = datetime.now().timestamp() - path.stat().st_mtime
        if age > ttl_seconds:
            continue
        with open(path) as f:
            raw = json.load(f)
        params = path.stem.replace("feed_", "").split("_")
        if len(params) >= 2:
            sd, ed = params[0], params[1]
            csv_path = save_feed_csv(raw, sd, ed)
            if csv_path:
                converted.append(str(csv_path))
    return converted


def stats(df):
    if df is None or df.empty:
        return {}
    high_risk_count = int(df["is_high_risk"].sum()) if "is_high_risk" in df.columns else int((df["risk_label"] == "HIGH").sum())
    return {
        "total": len(df),
        "hazardous": int(df["is_hazardous"].sum()),
        "high_risk": high_risk_count,
        "avg_velocity_kmh": round(float(df["velocity_kmh"].mean()), 1),
        "avg_diameter_m": round(float(df["diameter_avg_m"].mean()), 1),
        "avg_risk": round(float(df["risk_score"].mean()), 3),
        "max_risk": round(float(df["risk_score"].max()), 3),
        "closest_km": round(float(df["miss_distance_km"].min()), 1),
        "closest_name": str(df.loc[df["miss_distance_km"].idxmin(), "name"]),
        "largest_name": str(df.loc[df["diameter_max_m"].idxmax(), "name"]),
        "largest_m": round(float(df["diameter_max_m"].max()), 1),
        "fastest_name": str(df.loc[df["velocity_kmh"].idxmax(), "name"]),
        "fastest_kmh": round(float(df["velocity_kmh"].max()), 1),
    }


def risk_time_series(df):
    if df is None or df.empty:
        return pd.DataFrame()
    ts = df.groupby("date").agg(
        count=("id", "count"),
        high_risk_count=("is_high_risk", "sum"),
        avg_risk=("risk_score", "mean"),
        max_risk=("risk_score", "max"),
        avg_miss=("miss_distance_km", "mean"),
        closest_miss=("miss_distance_km", "min"),
    ).reset_index()
    ts["high_risk_pct"] = (ts["high_risk_count"] / ts["count"] * 100).round(1)
    ts["date"] = pd.to_datetime(ts["date"])
    ts = ts.sort_values("date")
    return ts


def closest_approach_ranking(df, top_n=10):
    if df is None or df.empty:
        return pd.DataFrame()
    ranking = df.nsmallest(top_n, "miss_distance_km")[
        ["name", "date", "miss_distance_km", "diameter_avg_m", "velocity_kmh", "risk_score", "is_high_risk", "is_hazardous"]
    ].copy()
    ranking["rank"] = range(1, len(ranking) + 1)
    ranking["miss_ld"] = (ranking["miss_distance_km"] / 384_400).round(2)
    return ranking


def highest_risk_ranking(df, top_n=10):
    if df is None or df.empty:
        return pd.DataFrame()
    ranking = df.nlargest(top_n, "risk_score")[
        ["name", "date", "risk_score", "diameter_avg_m", "velocity_kmh", "miss_distance_km", "is_high_risk", "is_hazardous"]
    ].copy()
    ranking["rank"] = range(1, len(ranking) + 1)
    return ranking


def get_or_fetch(start_date, end_date, force_refresh=False):
    merged = load_merged_csvs(start_date, end_date) if not force_refresh else None
    if merged is not None and not merged.empty:
        return merged, {"from_cache": True, "source": "csv"}

    client = NeoWsClient()
    raw, info = client.get_feed_range(
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for date, asteroids in raw.get("near_earth_objects", {}).items():
        chunk = {"near_earth_objects": {date: asteroids}, "element_count": len(asteroids)}
        save_feed_csv(chunk, date, date)

    merged = load_merged_csvs(start_date, end_date)
    info["source"] = "api"
    return merged, info
