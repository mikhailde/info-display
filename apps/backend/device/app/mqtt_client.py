import paho.mqtt.client as mqtt
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_KEEPALIVE = 60

def connect_mqtt() -> mqtt.Client:
    """
    Подключается к MQTT брокеру.

    Returns:
        mqtt.Client: Объект MQTT клиента в случае успешного подключения, None в противном случае.
    """
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    client = mqtt.Client()
    client.on_connect = on_connect
    try:
        client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        return client
    except ConnectionRefusedError as e:
        logger.error(f"Error: Could not connect to MQTT broker: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None

def publish_message(client: mqtt.Client, message: str, device_id: str):
    """
    Публикует сообщение в MQTT топик.

    Args:
        client (mqtt.Client): Объект MQTT клиента.
        message (str): Сообщение для публикации.
        device_id (str): Идентификатор устройства (топика).
    """
    topic = f"device/{device_id}/command"
    result = client.publish(topic, message)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        logger.info(f"Message `{message}` sent to topic `{topic}`")
    else:
        logger.error(f"Failed to send message to topic {topic}")
