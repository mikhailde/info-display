import paho.mqtt.client as mqtt
import os
import logging

# Используем встроенный логгер Uvicorn, если он доступен
logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_KEEPALIVE = 60

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def connect_mqtt() -> mqtt.Client:
    """Подключается к MQTT брокеру и возвращает объект клиента."""
    client = mqtt.Client()
    client.on_connect = on_connect

    try:
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...") # Добавь эту строку
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        client.loop_start()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return None

def publish_message(client: mqtt.Client, topic: str, message: str):
    """Публикует сообщение в MQTT топик."""
    result = client.publish(topic, message)
    if result.rc == 0:
        logger.info(f"Message '{message}' sent to topic '{topic}'")
    else:
        logger.error(f"Failed to send message to topic '{topic}', return code: {result.rc}")
