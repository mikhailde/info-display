from fastapi import FastAPI, HTTPException, status, APIRouter, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import httpx
import os
import logging
import json
import time
from typing import Dict

from .mqtt_client import connect_mqtt, publish_message
from .schemas import ContentResponse

logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

app = FastAPI(
    title="Device Management Service",
    description="Сервис для отправки данных на табло",
    version="0.1.0",
)

origins = [
    "http://localhost",
    "http://localhost:*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/v1")

CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content:8000")
DEVICE_ID = os.getenv("DEVICE_ID", "1")
MQTT_TOPIC_STATUS = f"device/{DEVICE_ID}/status"
API_KEY = os.getenv("DEVICE_API_KEY", "your_api_key") # Получаем API ключ из переменной окружения

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

# MQTT client
mqtt_client = None
# Store for device status data
device_status_store: Dict[str, Dict] = {}

async def get_device_status_store():
    return device_status_store

@app.on_event("startup")
async def startup_event():
    global mqtt_client
    mqtt_client = connect_mqtt()
    if mqtt_client:
        logger.info("MQTT client started successfully.")
        mqtt_client.subscribe(MQTT_TOPIC_STATUS)
        mqtt_client.on_message = on_message
    else:
        logger.error("Failed to connect to MQTT broker at startup.")

@app.on_event("shutdown")
async def shutdown_event():
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("MQTT client stopped.")

def on_message(client, userdata, msg):
    """Callback function to handle incoming MQTT messages."""
    try:
        # Добавляем проверку API ключа в сообщении
        payload = json.loads(msg.payload.decode())
        api_key = payload.get("api_key")

        if api_key != API_KEY:
          logger.warning(f"Unauthorized MQTT message from device: {payload.get('device_id')}, topic: {msg.topic}")
          return
        device_id = payload.get("device_id")

        if device_id:
            device_status_store[device_id] = {
                "status": payload.get("status"),
                "last_seen": payload.get("last_seen"),
                "message": payload.get("message"),
                "brightness": payload.get("brightness"),
                "temperature": payload.get("temperature"),
                "free_space": payload.get("free_space"),
                "uptime": payload.get("uptime")
            }
            logger.info(f"Status updated for device {device_id}")
        else:
            logger.warning("Received message without device_id")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message: {e}")

@router.post(
    "/device/update",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Device"],
    summary="Отправка сообщения на табло",
    dependencies=[Depends(get_api_key)]
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

@router.get(
    "/device/{device_id}/status",
    tags=["Device"],
    summary="Получение статуса табло",
    response_model=dict,
    dependencies=[Depends(get_api_key)]
)
async def get_device_status(device_id: str, device_status: Dict = Depends(get_device_status_store)):
    """
    Возвращает статус указанного табло.
    """
    if device_id in device_status:
        return device_status[device_id]
    else:
        raise HTTPException(status_code=404, detail="Device not found")

app.include_router(router)
