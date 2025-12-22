import os
import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

KAFKA_SERVERS = "195.201.122.4:9093,195.201.122.4:9096,195.201.122.4:9098"

# Paths to certificates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_DIR = os.path.join(BASE_DIR, "certs")
CA_CERT = os.path.join(CERT_DIR, "ca.crt")
CLIENT_CERT = os.path.join(CERT_DIR, "client.crt")
CLIENT_KEY = os.path.join(CERT_DIR, "client.key")

# Singleton producer
_producer = None


def get_producer():
    # Iinitialization of the Kafka producer
    global _producer
    if _producer is None:
        logger.info("Creating Kafka producer with SSL")
        conf = {
            "bootstrap.servers": KAFKA_SERVERS,
            "security.protocol": "SSL",
            "ssl.ca.location": CA_CERT,
            "ssl.certificate.location": CLIENT_CERT,
            "ssl.key.location": CLIENT_KEY,
            "acks": "all",
            # Optional tuning
            "message.send.max.retries": 3,
            "retry.backoff.ms": 1000,
            "client.id": "flask-kafka-producer"
        }
        _producer = Producer(conf)
    return _producer


def send_message(topic, message, key=None):
    """
    Send a JSON-serializable message to Kafka.

    :param topic: Kafka topic name
    :param message: Python dict (will be JSON-encoded)
    :param key: optional string key for partitioning
    """
    try:
        producer = get_producer()
        producer.produce(
            topic=topic,
            key=key,
            value=json.dumps(message)
        )
        # Flush ensures message is sent before returning
        producer.flush()
        logger.info(f"Message sent to topic '{topic}' successfully")
        return True
    except Exception as e:
        logger.error(f"Kafka send failed: {e}")
        return False