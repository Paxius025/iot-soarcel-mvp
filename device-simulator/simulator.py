import os
import time
import json
import random
import threading
import paho.mqtt.client as mqtt
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [DeviceSim] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Environment config
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", "device1")

# MQTT topic
TOPIC_PUB = f"sensor/{DEVICE_ID}/data"
TOPIC_SUB = f"device/{DEVICE_ID}/response"

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT broker with code {rc}")
    client.subscribe(TOPIC_SUB)
    logger.info(f"Subscribed to {TOPIC_SUB}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    logger.info(f"Received on {msg.topic}: {payload}")

# Publish sensor data periodically
def publish_sensor_data(client):
    while True:
        try:
            payload = {
                "device_id": DEVICE_ID,
                "irradiation": round(random.uniform(0.0, 1.0), 3),  # Solar irradiation
                "module_temperature": round(random.uniform(30.0, 60.0), 2),  # Module temperature
                "ambient_temperature": round(random.uniform(25.0, 45.0), 2)  # Ambient temperature
            }
            client.publish(TOPIC_PUB, json.dumps(payload))
            logger.info(f"Published to {TOPIC_PUB}: {payload}")
            time.sleep(random.uniform(1, 3))  # Publish every 1-3 seconds
        except Exception as e:
            logger.error(f"Error publishing sensor data: {e}")

# Main
def main():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(BROKER, PORT, 60)

        # Start publishing in background
        threading.Thread(target=publish_sensor_data, args=(client,), daemon=True).start()

        client.loop_forever()
    except Exception as e:
        logger.error(f"Main loop error: {e}")
        raise

if __name__ == "__main__":
    main()
