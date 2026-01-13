import os
import json
import logging
import threading
import requests
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_INPUT_TOPIC = os.getenv("MQTT_INPUT_TOPIC", "INTRA_input_test")

API_HOST = os.getenv("API_HOST", "localhost")
PORT = int(os.getenv("PORT", "8086"))

_client = None
_stop_event = threading.Event()


def forward_to_rest(model_name, features):
    try:
        url = f"http://{API_HOST}:{PORT}/predict/{model_name}"
        response = requests.post(url, json={"input": features}, timeout=10)

        if response.status_code == 200:
            logger.info(f"Prediction forwarded successfully for model '{model_name}'")
        else:
            logger.error(
                f"REST API error for model '{model_name}': "
                f"{response.status_code} {response.text}"
            )

    except Exception as e:
        logger.exception(f"Failed to call REST API for model '{model_name}': {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT consumer connected successfully")
        client.subscribe(MQTT_INPUT_TOPIC)
        logger.info(f"Subscribed to MQTT topic '{MQTT_INPUT_TOPIC}'")
    else:
        logger.error(f"MQTT connection failed with rc={rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.info(f"Received MQTT message: {payload}")

        model_name = payload.get("model")
        features = payload.get("input")

        if not model_name or features is None:
            raise ValueError("Message must contain 'model' and 'input'")

        forward_to_rest(model_name, features)

    except Exception as e:
        logger.exception(f"Failed to process MQTT message: {e}")


def start_mqtt_consumer():
    global _client

    if _client is not None:
        return

    logger.info("Starting MQTT consumer")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    _client = client


def stop_mqtt_consumer():
    logger.info("Stopping MQTT consumer")

    if _client:
        _client.loop_stop()
        _client.disconnect()
