"""Зовнішні API для вкладки Віджети: погода, крипта, GitHub. Усе з кешем."""
import requests

import config
from db import cache_get, cache_set

_TIMEOUT = 10


def get_weather():
    """Open-Meteo (без ключа). Поточна + макс/мін на сьогодні."""
    cached = cache_get("weather", 900)  # 15 хв
    if cached is not None:
        return cached
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": config.WEATHER_LAT,
                "longitude": config.WEATHER_LON,
                "current": "temperature_2m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        d = r.json()
        result = {
            "ok": True,
            "city": config.WEATHER_CITY,
            "temp": round(d["current"]["temperature_2m"]),
            "code": d["current"]["weather_code"],
            "t_max": round(d["daily"]["temperature_2m_max"][0]),
            "t_min": round(d["daily"]["temperature_2m_min"][0]),
            "precip": d["daily"]["precipitation_sum"][0],
        }
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    cache_set("weather", result)
    return result


def get_crypto():
    """CoinGecko simple price (без ключа)."""
    cached = cache_get("crypto", 300)  # 5 хв
    if cached is not None:
        return cached
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(config.CRYPTO_IDS),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        coins = []
        for cid in config.CRYPTO_IDS:
            info = data.get(cid)
            if info:
                coins.append({
                    "id": cid,
                    "price": info.get("usd"),
                    "change": round(info.get("usd_24h_change", 0), 1),
                })
        result = {"ok": True, "coins": coins}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    cache_set("crypto", result)
    return result


def get_github():
    """Останні події/репо користувача. Потрібен GITHUB_USER (токен опційно для ліміту)."""
    if not config.GITHUB_USER:
        return {"ok": False, "error": "GITHUB_USER не заданий"}
    cached = cache_get("github", 600)  # 10 хв
    if cached is not None:
        return cached
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    try:
        r = requests.get(
            f"https://api.github.com/users/{config.GITHUB_USER}/repos",
            params={"sort": "pushed", "per_page": 5},
            headers=headers,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        repos = [{
            "name": x["name"],
            "url": x["html_url"],
            "stars": x["stargazers_count"],
            "pushed_at": x["pushed_at"][:10],
        } for x in r.json()]
        result = {"ok": True, "repos": repos}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    cache_set("github", result)
    return result
