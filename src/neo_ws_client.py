import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

try:
    import streamlit as st
    _ST_SECRETS_KEY = st.secrets.get("NASA_API_KEY")
except Exception:
    _ST_SECRETS_KEY = None

BASE_URL = "https://api.nasa.gov/neo/rest/v1"
FEED_MAX_DAYS = 7
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


class DiskCache:
    def __init__(self, cache_dir=None, ttl_seconds=3600):
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _filename(self, endpoint, params):
        parts = [endpoint] + [f"{k}-{v}" for k, v in sorted(params.items())]
        safe = "_".join(parts)
        safe = safe.replace("/", "_").replace("?", "_").replace(":", "_")
        safe = "".join(c if c.isalnum() or c in "_-." else "_" for c in safe)
        if not safe.endswith(".json"):
            safe += ".json"
        return safe

    def get(self, endpoint, params):
        path = self.cache_dir / self._filename(endpoint, params)
        if path.exists():
            age = time.time() - path.stat().st_mtime
            if age < self.ttl_seconds:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None

    def set(self, endpoint, params, data):
        path = self.cache_dir / self._filename(endpoint, params)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def has(self, endpoint, params):
        path = self.cache_dir / self._filename(endpoint, params)
        if path.exists():
            age = time.time() - path.stat().st_mtime
            return age < self.ttl_seconds
        return False

    def age(self, endpoint, params):
        path = self.cache_dir / self._filename(endpoint, params)
        if path.exists():
            return time.time() - path.stat().st_mtime
        return None

    def clear_all(self):
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clear_endpoint(self, endpoint):
        for p in self.cache_dir.glob(f"{endpoint}_*.json"):
            p.unlink()


class NeoWsClient:
    def __init__(self, api_key=None, cache_ttl=3600):
        self.api_key = api_key or _ST_SECRETS_KEY or os.getenv("NASA_API_KEY", "DEMO_KEY")
        self.session = requests.Session()
        self.session.params = {"api_key": self.api_key}
        self._last_call = 0.0
        self.cache = DiskCache(ttl_seconds=cache_ttl)

    def _rate_limited_call(self, url, params):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < 0.6:
            time.sleep(0.6 - elapsed)
        self._last_call = time.time()
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_feed(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end = datetime.now() + timedelta(days=FEED_MAX_DAYS)
            end_date = end.strftime("%Y-%m-%d")

        return self._rate_limited_call(
            f"{BASE_URL}/feed",
            {"start_date": start_date, "end_date": end_date},
        )

    def get_feed_range(
        self,
        start_date,
        end_date,
        force_refresh=False,
        progress_callback=None,
    ):
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if (end - start).days <= FEED_MAX_DAYS:
            params = {"start_date": start_date, "end_date": end_date}
            cached = self.cache.get("feed", params)
            if cached and not force_refresh:
                return cached, {"from_cache": True, "chunks": 1, "cached_chunks": 1}
            if progress_callback:
                progress_callback(start_date, end_date)
            data = self.get_feed(start_date, end_date)
            self.cache.set("feed", params, data)
            return data, {"from_cache": False, "chunks": 1, "cached_chunks": 0}

        chunks = []
        cached_count = 0
        total_chunks = 0
        current = start
        while current < end:
            chunk_end = min(current + timedelta(days=FEED_MAX_DAYS - 1), end)
            cs = current.strftime("%Y-%m-%d")
            ce = chunk_end.strftime("%Y-%m-%d")
            params = {"start_date": cs, "end_date": ce}
            total_chunks += 1

            cached = self.cache.get("feed", params)
            if cached and not force_refresh:
                chunks.append(cached)
                cached_count += 1
            else:
                if progress_callback:
                    progress_callback(cs, ce)
                data = self.get_feed(cs, ce)
                self.cache.set("feed", params, data)
                chunks.append(data)

            current = chunk_end + timedelta(days=1)

        merged = {"near_earth_objects": {}, "element_count": 0}
        seen_ids = set()
        for chunk in chunks:
            for date, asteroids in chunk.get("near_earth_objects", {}).items():
                if date not in merged["near_earth_objects"]:
                    merged["near_earth_objects"][date] = []
                for ast in asteroids:
                    aid = ast.get("id")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        merged["near_earth_objects"][date].append(ast)
                        merged["element_count"] += 1

        return merged, {
            "from_cache": cached_count == total_chunks,
            "chunks": total_chunks,
            "cached_chunks": cached_count,
        }

    def browse(self, page=0, size=20):
        params = {"page": page, "size": size}
        cached = self.cache.get("browse", params)
        if cached:
            return cached, True
        data = self._rate_limited_call(f"{BASE_URL}/neo/browse", params)
        self.cache.set("browse", params, data)
        return data, False

    def get_asteroid(self, asteroid_id):
        return self._rate_limited_call(f"{BASE_URL}/neo/{asteroid_id}", {})


LUNAR_DISTANCE_KM = 384_400
ASTRO_UNIT_KM = 149_597_870.7
HIGH_RISK_THRESHOLD = 0.6


def compute_risk_score(row):
    diam = row.get("diameter_avg_m", row.get("diameter_max_m", 0))
    vel = row.get("velocity_kmh", 0)
    miss = row.get("miss_distance_km", 0)
    hazardous = row.get("is_hazardous", False)

    if miss <= 0:
        return 1.0

    import math
    size_factor = min(1.0, max(0.0, math.log10(max(diam, 1) / 10) / 2)) if diam > 10 else 0.0
    speed_factor = min(1.0, max(0.0, (vel - 20000) / 100000))
    dist_factor = 1.0 - min(1.0, miss / LUNAR_DISTANCE_KM)
    hazard_bonus = 0.2 if hazardous else 0.0

    score = 0.3 * size_factor + 0.2 * speed_factor + 0.3 * dist_factor + hazard_bonus
    return round(min(1.0, score), 4)


def _extract_approach(ast):
    approach = (ast.get("close_approach_data") or [{}])[0]
    diam = ast.get("estimated_diameter", {}).get("meters", {})
    diameter_min = float(diam.get("estimated_diameter_min", 0) or 0)
    diameter_max = float(diam.get("estimated_diameter_max", 0) or 0)

    vel_kmh = approach.get("relative_velocity", {}).get("kilometers_per_hour", "0")
    vel_kmps = approach.get("relative_velocity", {}).get("kilometers_per_second", "0")
    vel_mph = approach.get("relative_velocity", {}).get("miles_per_hour", "0")

    miss_km = approach.get("miss_distance", {}).get("kilometers", "0")
    miss_lunar = approach.get("miss_distance", {}).get("lunar", "0")
    miss_au = approach.get("miss_distance", {}).get("astronomical", "0")

    return {
        "diameter_min_m": round(diameter_min, 2),
        "diameter_max_m": round(diameter_max, 2),
        "diameter_avg_m": round((diameter_min + diameter_max) / 2, 2),
        "absolute_magnitude": ast.get("absolute_magnitude_h"),
        "is_hazardous": ast.get("is_potentially_hazardous_asteroid", False),
        "velocity_kmh": round(float(vel_kmh), 2) if vel_kmh else 0,
        "velocity_kmps": round(float(vel_kmps), 4) if vel_kmps else 0,
        "velocity_mph": round(float(vel_mph), 2) if vel_mph else 0,
        "miss_distance_km": round(float(miss_km), 2) if miss_km else 0,
        "miss_distance_lunar": round(float(miss_lunar), 2) if miss_lunar else 0,
        "miss_distance_au": round(float(miss_au), 8) if miss_au else 0,
        "orbiting_body": approach.get("orbiting_body", "N/A"),
        "close_approach_date": approach.get("close_approach_date", ""),
    }


def _build_record(ast, date, extra):
    row = {
        "id": ast.get("id"),
        "name": ast.get("name"),
        "date": date,
        "neo_reference_id": ast.get("neo_reference_id"),
        "url": ast.get("nasa_jpl_url"),
        **extra,
    }
    row["risk_score"] = compute_risk_score(row)
    row["is_high_risk"] = row["risk_score"] >= HIGH_RISK_THRESHOLD
    if row["risk_score"] >= 0.8:
        row["risk_label"] = "HIGH"
    elif row["risk_score"] >= HIGH_RISK_THRESHOLD:
        row["risk_label"] = "MEDIUM"
    elif row["risk_score"] >= 0.2:
        row["risk_label"] = "LOW"
    else:
        row["risk_label"] = "NONE"
    return row


def flatten_feed(data):
    records = []
    for date, asteroids in data.get("near_earth_objects", {}).items():
        for ast in asteroids:
            extra = _extract_approach(ast)
            records.append(_build_record(ast, date, extra))
    return records


def flatten_browse(data):
    records = []
    for ast in data.get("near_earth_objects", []):
        extra = _extract_approach(ast)
        records.append(_build_record(ast, extra.get("close_approach_date", ""), extra))
    return records
