from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import httpx
import os
from mqtt_client import publish_message

app = FastAPI(
    title="Device Management Service",
    description="Сервис для отправки данных на табло",
    version="0.1.0",
)

CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content:8000")

class ContentResponse(BaseModel):
    message: str = Field(..., description="Текст сообщения")
    created_at: str = Field(..., description="Время создания сообщения")

@app.post(
    "/api/v1/device/update",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Device"],
    summary="Отправка сообщения на табло",
)
async def update_device():
    """
    Инициирует отправку сообщения на табло.

    Получает последнее статическое сообщение из Content Management Service и публикует его в MQTT топик.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CONTENT_SERVICE_URL}/api/v1/content")
            response.raise_for_status()
            content = ContentResponse(**response.json())

            publish_message(message=content.message)
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Content Service unavailable: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error publishing message: {e}",
            )
