import paho.mqtt.client as mqtt
import os
import logging

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DEVICE_ID = "tablo_1"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def publish_message(message: str, device_id: str = DEVICE_ID):
    """
    Публикует сообщение в MQTT топик.

    Args:
        message: Сообщение для публикации.
        device_id: Идентификатор устройства (топика). По умолчанию - "tablo_1".
    """
    client = mqtt.Client()
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        logger.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")

        result = client.publish(f"device/{device_id}/command", message)
        logger.info(f"Publishing message '{message}' to topic 'device/{device_id}/command'")

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Message published successfully with message ID: {result.mid}")
        else:
            logger.error(f"Failed to publish message. Return code: {result.rc}")

        client.disconnect()
    except ConnectionRefusedError as e:
        logger.error(f"Error: Could not connect to MQTT broker: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
