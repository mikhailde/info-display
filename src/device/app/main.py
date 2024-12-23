from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
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
        payload = json.loads(msg.payload.decode())
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
    summary="Отправка сообщения на табло"
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
            logger.info(f"Received content from Content Service: {content}")

        publish_message(mqtt_client, f"device/{DEVICE_ID}/command", content["message"])
        logger.info(f"Sent message to MQTT topic: device/{DEVICE_ID}/command, message: {content['message']}")

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
