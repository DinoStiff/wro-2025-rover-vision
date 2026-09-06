import os

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "dino/command")

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected to {BROKER}:{PORT}")
    client.subscribe(TOPIC, qos=1)

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8").strip()
    print(f"\n[RECV] {payload}")

    if payload.startswith("MAP "):
        try:
            header, data = payload[4:].split(";", 1)
            rows, cols = map(int, header.split(","))
            flat_vals = list(map(int, data.split(",")))

            # Rebuild into 2D list
            grid = [flat_vals[i*cols:(i+1)*cols] for i in range(rows)]

            print(f"[MAP] {rows}x{cols}:")
            for row in grid:
                print(" ".join(str(v) for v in row))

        except Exception as e:
            print(f"[ERROR] Failed to parse map: {e}")
    else:
        print("[INFO] Non-MAP message received")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="map_viewer")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)
print(f"[BOOT] Listening for map data on topic '{TOPIC}'...")
client.loop_forever()
