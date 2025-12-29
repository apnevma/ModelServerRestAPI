import json
import logging
import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

"""
MQTT_BROKER = "128.140.70.68"
MQTT_PORT = 30005
MQTT_USERNAME = "ssf"
MQTT_PASSWORD = "FhdJW6UppzXKFhdDfyHEEPbe"
"""

# --- For dev only ---
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

MQTT_TOPIC = "INTRA_test_topic1"

_mqtt_client = None


def get_mqtt_client():
    global _mqtt_client

    if _mqtt_client is None:
        log.info("Creating MQTT producer client")

        client = mqtt.Client()
        #client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                log.info("MQTT connected successfully")
            else:
                log.error(f"MQTT connection failed with rc={rc}")

        client.on_connect = on_connect

        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()

        _mqtt_client = client

    return _mqtt_client


def send_mqtt_message(message: dict):
    """
    Send a JSON message to MQTT.
    """
    try:
        client = get_mqtt_client()
        payload = json.dumps(message).encode("utf-8")

        result = client.publish(MQTT_TOPIC, payload)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Publish failed with rc={result.rc}")

        log.info("Message published to MQTT successfully")
        return True

    except Exception as e:
        log.error(f"MQTT send failed: {e}")
        return False