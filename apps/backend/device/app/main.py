from fastapi import FastAPI, HTTPException, status, APIRouter
import httpx
import os
import logging

from mqtt_client import connect_mqtt, publish_message
from schemas import ContentResponse

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Device Management Service",
    description="Сервис для отправки данных на табло",
    version="0.1.0",
)

router = APIRouter(prefix="/api/v1")

CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content:8000/") # Слэш на конце
DEVICE_ID = os.getenv("DEVICE_ID", "tablo_1")

# MQTT client
mqtt_client = None

@app.on_event("startup")
async def startup_event():
    global mqtt_client
    mqtt_client = connect_mqtt()
    if mqtt_client:
        mqtt_client.loop_start()

@app.on_event("shutdown")
async def shutdown_event():
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MQTT client not connected")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CONTENT_SERVICE_URL}api/v1/content/")
            response.raise_for_status()
            content = ContentResponse(**response.json())
            publish_message(mqtt_client, content.message, DEVICE_ID)
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
