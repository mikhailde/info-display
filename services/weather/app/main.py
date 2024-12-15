import httpx
from fastapi import FastAPI, HTTPException
from cachetools import TTLCache, cached
from datetime import datetime
from .config import YANDEX_WEATHER_API_KEY, LOCATION_LATITUDE, LOCATION_LONGITUDE
from .schemas import WeatherData

app = FastAPI()

weather_cache = TTLCache(maxsize=1, ttl=300)

@cached(weather_cache)
async def get_weather_from_yandex_api():
    headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}
    params = {"lat": LOCATION_LATITUDE, "lon": LOCATION_LONGITUDE, "lang": "ru_RU"}
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.weather.yandex.ru/v2/forecast", headers=headers, params=params)
        response.raise_for_status()
        return response.json()

def format_weather_data(weather_response: dict) -> WeatherData:
    now = weather_response.get("fact", {})
    temp = now.get("temp")
    condition = now.get("condition")
    icon_code = now.get("icon")
    icon_url = f"https://yastatic.net/weather/i/icons/funky/dark/{icon_code}.svg"
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return WeatherData(temperature=temp, condition=condition, icon=icon_url, updated_at=updated_at)

async def get_weather_data() -> WeatherData:
    weather_response = await get_weather_from_yandex_api()
    return format_weather_data(weather_response)

@app.get("/")
async def root():
    return {"message": "Weather Service"}

@app.get("/api/v1/weather", response_model=WeatherData)
async def get_weather():
    try:
        return await get_weather_data()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Error getting weather data from Yandex: {e}")
