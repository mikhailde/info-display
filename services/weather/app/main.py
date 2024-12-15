import httpx
from fastapi import FastAPI, HTTPException
from datetime import datetime
from asyncio import Lock
from cachetools import TTLCache
from .config import YANDEX_WEATHER_API_KEY, LOCATION_LATITUDE, LOCATION_LONGITUDE
from .schemas import WeatherData

app = FastAPI()

cache = TTLCache(maxsize=1, ttl=5400)  # Кеш на 90 минут
cache_lock = Lock()  # Блокировка для синхронизации доступа к кешу

async def get_raw_weather_data():
    async with cache_lock:  # Блокируем доступ к кешу
        if "weather_data" in cache:
            return cache["weather_data"]

        headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}
        params = {"lat": LOCATION_LATITUDE, "lon": LOCATION_LONGITUDE, "lang": "ru_RU"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.weather.yandex.ru/v2/forecast", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        # Сохраняем результат в кеш
        cache["weather_data"] = data
        return data

def format_weather_data(weather_response: dict) -> WeatherData:
    fact = weather_response.get("fact", {})
    return WeatherData(
        temperature=fact.get("temp"),
        condition=fact.get("condition"),
        icon=f"https://yastatic.net/weather/i/icons/funky/dark/{fact.get('icon')}.svg",
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.get("/api/v1/weather", response_model=WeatherData)
async def get_weather():
    try:
        raw_weather_data = await get_raw_weather_data()  # Получаем закэшированные данные
        return format_weather_data(raw_weather_data)     # Форматируем данные
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Error getting weather data from Yandex: {e}")

@app.get("/")
async def root():
    return {"message": "Weather Service"}
