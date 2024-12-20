import httpx
from fastapi import FastAPI, HTTPException, APIRouter
from datetime import datetime
from asyncio import Lock
from cachetools import TTLCache
from .config import YANDEX_API_KEY, LOCATION_LATITUDE, LOCATION_LONGITUDE
from .schemas import WeatherData
import logging

# Настройка логирования
logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

app = FastAPI(
    title="Weather Service",
    description="Сервис для получения данных о погоде",
    version="0.1.0"
)

router = APIRouter(prefix="/api/v1")

cache = TTLCache(maxsize=1, ttl=5400)  # Кеш на 90 минут
cache_lock = Lock()  # Блокировка для синхронизации доступа к кешу

async def _get_raw_weather_data():
    """Получает сырые данные о погоде от Яндекс.Погоды. Использует кэширование."""
    async with cache_lock:
        if "weather_data" in cache:
            logger.info("Returning cached weather data.")
            return cache["weather_data"]

        logger.info("Fetching weather data from Yandex.Weather API.")
        headers = {"X-Yandex-API-Key": YANDEX_API_KEY}
        params = {"lat": LOCATION_LATITUDE, "lon": LOCATION_LONGITUDE, "lang": "ru_RU"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.weather.yandex.ru/v2/forecast", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched weather data from Yandex.Weather API. Status code: {response.status_code}, Response: {data}") # Добавляем лог об успешном ответе

        cache["weather_data"] = data
        return data

def _format_weather_data(weather_response: dict) -> WeatherData:
    """Форматирует данные о погоде в нужный формат."""
    fact = weather_response.get("fact", {})
    return WeatherData(
        temperature=fact.get("temp"),
        condition=fact.get("condition"),
        icon=f"https://yastatic.net/weather/i/icons/funky/dark/{fact.get('icon')}.svg",
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@router.get("/weather", response_model=WeatherData)
async def get_weather():
    """Возвращает данные о погоде."""
    try:
        raw_weather_data = await _get_raw_weather_data()
        return _format_weather_data(raw_weather_data)
    except httpx.HTTPError as e:
        logger.error(f"Error getting weather data from Yandex: {e}")
        raise HTTPException(status_code=503, detail=f"Error getting weather data from Yandex: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "Weather Service"}

app.include_router(router)
