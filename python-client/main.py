import os
import json
import time
import paho.mqtt.client as mqtt
import grpc

import model_pb2
import model_pb2_grpc

import time

MAX_RETRIES = 5
WAIT_SECONDS = 3

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SUB = "sensor/+/data"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(TOPIC_SUB)
    print(f"[MQTT] Subscribed to topic: {TOPIC_SUB}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        print(f"[RECV] Topic: {msg.topic} | Payload: {data}")

        # Extract device_id from topic
        topic_parts = msg.topic.split("/")
        device_id = topic_parts[1] if len(topic_parts) >= 3 else "unknown"

        # === Call gRPC ===
        request = model_pb2.SensorRequest(
            device_id=device_id,
            irradiation=float(data.get("irradiation", 0.0)),
            module_temperature=float(data.get("module_temperature", 0.0)),
            ambient_temperature=float(data.get("ambient_temperature", 0.0)),
            timestamp=int(time.time())
        )

        response = stub.Predict(request)
        print(f"[AI] Prediction score: {response.score}, Status: {response.status}")

        # === Send by MQTT For respond to device ===
        response_topic = f"device/{device_id}/response"
        response_payload = {
            "device_id": device_id,
            "status": response.status,
            "score": {
                "IRRADIATION": response.score.IRRADIATION,
                "MODULE_TEMPERATURE": response.score.MODULE_TEMPERATURE,
                "AMBIENT_TEMPERATURE": response.score.AMBIENT_TEMPERATURE
            },
            "received_at": time.time()
        }

        client.publish(response_topic, json.dumps(response_payload))
        print(f"[SEND] → {response_topic} | Payload: {response_payload}")

    except Exception as e:
        print(f"[ERROR] Failed to process message: {e}")
        
def wait_for_grpc_server():
    for i in range(MAX_RETRIES):
        try:
            channel = grpc.insecure_channel("grpc-server:50051")
            grpc.channel_ready_future(channel).result(timeout=5)
            print("[gRPC] Connected to grpc-server")
            return channel
        except Exception as e:
            print(f"[gRPC] Retry {i+1}/{MAX_RETRIES} - Waiting for grpc-server... ({e})")
            time.sleep(WAIT_SECONDS)
    raise RuntimeError("Failed to connect to gRPC server after retries")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_forever()
    
# gRPC setup
channel = wait_for_grpc_server()
stub = model_pb2_grpc.ModelServiceStub(channel)

if __name__ == "__main__":
    main()
