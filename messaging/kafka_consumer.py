import os
import json
import logging
import threading
import requests
from confluent_kafka import Consumer


logger = logging.getLogger(__name__)

# Kafka config
KAFKA_SERVERS = "195.201.122.4:9093,195.201.122.4:9096,195.201.122.4:9098"
KAFKA_INPUT_TOPIC = "INTRA_input_test"
KAFKA_GROUP_ID = "ml-serving-tool"

API_HOST = os.getenv("API_HOST", "localhost")
PORT = int(os.getenv("PORT", "8086"))

# Paths to certificates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_DIR = os.path.join(BASE_DIR, "certs")
CA_CERT = os.path.join(CERT_DIR, "ca.crt")
CLIENT_CERT = os.path.join(CERT_DIR, "client.crt")
CLIENT_KEY = os.path.join(CERT_DIR, "client.key")

_consumer = None
_stop_event = threading.Event()
_consumer_thread = None


def get_consumer():
    global _consumer

    if _consumer is None:
        logger.info("Creating Kafka consumer with SSL")

        conf = {
            "bootstrap.servers": KAFKA_SERVERS,
            "group.id": KAFKA_GROUP_ID,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,

            "security.protocol": "SSL",
            "ssl.ca.location": CA_CERT,
            "ssl.certificate.location": CLIENT_CERT,
            "ssl.key.location": CLIENT_KEY,

            "client.id": "ml-serving-kafka-consumer",
        }

        _consumer = Consumer(conf)
        _consumer.subscribe([KAFKA_INPUT_TOPIC])

    return _consumer

def forward_to_rest(model_name, features):
    try:
        # Assuming REST API runs on localhost in the same container
        url = f"http://{API_HOST}:{PORT}/predict/{model_name}"
        response = requests.post(url, json={"input": features}, timeout=10)
        if response.status_code == 200:
            logger.info(f"Prediction sent successfully for model '{model_name}'")
        else:
            logger.error(f"REST API error for model '{model_name}': {response.text}")
    except Exception as e:
        logger.exception(f"Failed to call REST API for model '{model_name}': {e}")


def _consume_loop():
    consumer = get_consumer()
    logger.info("Kafka consumer loop started")

    try:
        while not _stop_event.is_set():
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                payload = json.loads(msg.value().decode("utf-8"))
                logger.info(f"Received Kafka message: {payload}")

                model_name = payload.get("model")
                features = payload.get("input")

                if not model_name or features is None:
                    raise ValueError("Message must contain 'model' and 'input'")

                # Forward to REST API for prediction
                forward_to_rest(model_name, features)

            except Exception as e:
                logger.exception(f"Failed to process Kafka message: {e}")

    finally:
        logger.info("Closing Kafka consumer")
        consumer.close()

    
def start_kafka_consumer():
    global _consumer_thread

    if _consumer_thread is None:
        logger.info("Starting Kafka consumer thread")
        _consumer_thread = threading.Thread(
            target=_consume_loop,
            daemon=True
        )
        _consumer_thread.start()


def stop_kafka_consumer():
    logger.info("Stopping Kafka consumer thread")
    _stop_event.set()

    if _consumer_thread:
        _consumer_thread.join(timeout=5)