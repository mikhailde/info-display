from fastapi import FastAPI, HTTPException, Request, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
import httpx

import models, schemas
from database import engine, SessionLocal

# Настройка логгирования
logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

# Создание таблицы в БД
models.Base.metadata.create_all(bind=engine)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Content Management Service",
    description="Сервис для управления статическим контентом",
    version="0.1.0",
)
app.router.on_startup = [] #очистка кэша

# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутер для API v1
router = APIRouter(prefix="/api/v1")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Константы для MQTT
MQTT_BROKER = os.getenv("MOSQUITTO_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MOSQUITTO_PORT", 1883))
MQTT_TOPIC = "tablo_topic" # Этот топик сейчас не нужен, но оставим на случай, если захотите отправлять и в него тоже

# Инициализация MQTT клиента
mqtt_client = mqtt.Client()

# Обработчик события подключения к MQTT брокеру
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()

# Эндпоинт для создания контента
DEVICE_MANAGEMENT_SERVICE_URL = os.getenv("DEVICE_MANAGEMENT_SERVICE_URL", "http://device:8000")

@router.post("/content", response_model=schemas.Content, status_code=status.HTTP_201_CREATED)
def create_content(content: schemas.ContentCreate, db: Session = Depends(get_db)):
    """Создает новый контент."""
    print("DEBUG: create_content function called!")
    logger.info(f"Received request to create content: {content.message}")
    db_content = models.Content(message=content.message)
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    logger.info(f"Content created successfully: {db_content}")

    # Добавляем вызов Device Management Service для обновления данных на табло
    try:
        with httpx.Client() as client:
            response = client.post(f"{DEVICE_MANAGEMENT_SERVICE_URL}/api/v1/device/update")
            response.raise_for_status()
        logger.info("Successfully notified Device Management Service to update device.")
    except httpx.HTTPError as e:
        logger.error(f"Failed to notify Device Management Service: {e}")

    return db_content

# Эндпоинт для получения последнего контента
@router.get("/content", response_model=schemas.Content)
def read_latest_content(db: Session = Depends(get_db)):
    """Возвращает последний созданный контент."""
    logger.info("Received request to read latest content")
    content = db.query(models.Content).order_by(models.Content.id.desc()).first()
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    logger.info(f"Latest content retrieved successfully: {content}")
    return content

# Эндпоинт для отправки сообщения через MQTT (теперь сохраняет в БД)
@router.post("/send_message")
async def send_message(request: Request, db: Session = Depends(get_db)):
    """Принимает сообщение, сохраняет его в БД и публикует его в MQTT (опционально)."""
    try:
        data = await request.json()
        message = data.get("message")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Сохраняем сообщение в БД
        db_content = models.Content(message=message)
        db.add(db_content)
        db.commit()
        db.refresh(db_content)
        logger.info(f"Message saved to database: {message}")

        # Опционально: публикуем сообщение в MQTT (раскомментируйте, если нужно)
        # mqtt_client.publish(MQTT_TOPIC, message)
        # logger.info(f"Message published to MQTT topic {MQTT_TOPIC}: {message}")

        return {"status": "ok", "message_id": db_content.id}  # Возвращаем ID созданного сообщения
    except Exception as e:
        logger.error(f"Error saving message to database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Подключение роутера к приложению
app.include_router(router)
