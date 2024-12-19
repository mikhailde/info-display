from fastapi import FastAPI, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware  # Импортируйте CORSMiddleware
import httpx
import os
import logging

from .mqtt_client import connect_mqtt, publish_message
from .schemas import ContentResponse

# Используем встроенный логгер Uvicorn, если он доступен
logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

app = FastAPI(
    title="Device Management Service",
    description="Сервис для отправки данных на табло",
    version="0.1.0",
)

# Добавьте CORS middleware
origins = [
    "http://localhost",  # Разрешите запросы от веб-интерфейса, запущенного на localhost
    "http://localhost:*" # Добавьте, если веб-интерфейс может быть запущен на другом порту
    # Добавьте другие адреса, если это необходимо
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Разрешите все методы, включая POST
    allow_headers=["*"],  # Разрешите все заголовки, включая Content-Type
)

router = APIRouter(prefix="/api/v1")

CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content:8000")
DEVICE_ID = os.getenv("DEVICE_ID", "1")

# MQTT client
mqtt_client = None

@app.on_event("startup")
async def startup_event():
    global mqtt_client
    mqtt_client = connect_mqtt()
    if mqtt_client:
        logger.info("MQTT client started successfully.")
    else:
        logger.error("Failed to connect to MQTT broker at startup.")

@app.on_event("shutdown")
async def shutdown_event():
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("MQTT client stopped.")

@router.post(
    "/device/update",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Device"],
    summary="Отправка сообщения на табло",
)
async def update_device():
    """
    Инициирует отправку сообщения на табло.

    Получает последнее статическое сообщение из Content Management Service и публикует его в MQTT топик.
    """
    if not mqtt_client:
        logger.error("MQTT client not connected.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MQTT client not connected")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CONTENT_SERVICE_URL}/api/v1/content")
            response.raise_for_status()
            content = response.json()

        publish_message(mqtt_client, f"device/{DEVICE_ID}/command", content["message"])

    except httpx.HTTPError as e:
        logger.error(f"Content Service unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Content Service unavailable: {e}",
        )
    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing message: {e}",
        )

app.include_router(router)
