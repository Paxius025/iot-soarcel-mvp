# IoT + AI System Workflow

## System Architecture

**Flow:** ESP32 → MQTT → AI Model (gRPC) → Response

```bash
[ESP32 Sensor]
    │
    ▼
[MQTT Publish: sensor/{id}/data]
    │
    ▼
[MQTT Broker]
    │
    ▼
[GoApp: MQTT Subscribe]
    │
    ▼
[gRPC Request]
    │
    ▼
[Python Model Server (AI)]
    │
    ▼
[gRPC Response]
    │
    ▼
┌────────────┬─────────────────────┐
▼            ▼                     ▼
Web/CLI   MQTT Publish     Database (Optional)
        device/{id}/response
```

---

## 1. Device Simulator

The device simulator emulates real devices, such as solar panels and sensors. It transmits sensor data, including:

- `IRRADIATION`
- `MODULE_TEMPERATURE`
- `AMBIENT_TEMPERATURE`
- `timestamp`

Data is published to the following MQTT topic:

```
sensor/<device_id>/data
```

---

## 2. MQTT Broker (Mosquitto)

The MQTT broker acts as middleware, receiving messages from the device simulator and forwarding them to subscribed clients (e.g., the Python client).

---

## 3. Python MQTT Client

- Subscribes to the MQTT topic: `sensor/+/data`
- Upon receiving data:
    - Converts the payload to JSON
    - Extracts the `device_id` from the topic
    - Constructs a `SensorRequest` object
    - Sends the data to the gRPC server using `ModelService.Predict()`
    - Receives the AI-generated result (score)
    - Publishes the result to:

       ```
       device/<device_id>/response
       ```

---

## 4. gRPC Server

- Listens on port `50051`
- Exposes the `ModelService` with the `Predict` method
- Receives sensor data via `SensorRequest`
- Invokes the AI model (`GRUModel`) for forecasting
- Returns an `AIResponse` to the MQTT client

---

## 5. Result Delivery

- AI results are published via MQTT to:

    ```
    device/<device_id>/response
    ```

- The device simulator or a dashboard can subscribe to this topic to receive the results.

---

## Step-by-Step Workflow

1. The device simulator publishes data to the MQTT broker (`sensor/device1/data`).
2. The MQTT client receives the data, processes it, and sends it to the gRPC server.
3. The gRPC server runs the AI model and returns a score.
4. The MQTT client publishes the score to the response topic.
5. The device simulator or dashboard subscribes to receive the results.

---

## 📄 License

This project is released **without an open source license**.

All rights reserved.  
You may view the code for educational purposes only.  
Copying, modification, or use in other projects is **not permitted** without explicit permission.

For inquiries, please contact: [github.com/paxius025](https://github.com/paxius025)
