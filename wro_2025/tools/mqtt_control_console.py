# pip install paho-mqtt
# python control_console.py

import time
import os
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "dino/command")

# ---------- MQTT callbacks ----------
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] on_connect rc={rc} (0 means success)")
    if rc == 0:
        # QoS 1 subscribe
        client.subscribe(TOPIC, qos=1)
        print(f"[MQTT] Subscribed to {TOPIC}")
    else:
        print("[MQTT] Connect failed — check broker IP/port/firewall")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="replace").strip()
    print(f"\n[RECV] topic={msg.topic} retain={msg.retain} qos={msg.qos} -> {payload}")

    if payload.startswith("MAP "):
        try:
            header, data = payload[4:].split(";", 1)
            rows, cols = map(int, header.split(",", 1))
            flat_vals = [int(x) for x in data.split(",") if x]
            if len(flat_vals) != rows * cols:
                raise ValueError(f"count={len(flat_vals)} expected={rows*cols}")
            grid = [flat_vals[i*cols:(i+1)*cols] for i in range(rows)]
            print(f"[MAP] {rows}x{cols}:")
            for row in grid:
                print(" ".join(str(v) for v in row))
        except Exception as e:
            print(f"[ERROR] Failed to parse MAP: {e}")
    else:
        print("[INFO] Non-MAP message received")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected rc={rc}")

def on_log(client, userdata, level, buf):
    # Uncomment next line for deep debugging
    # print(f"[LOG] {buf}")
    pass

# ---------- helpers ----------
def send_text(client, text, qos=1, retain=False):
    r = client.publish(TOPIC, text, qos=qos, retain=retain)
    r.wait_for_publish()
    print(f"[SEND] '{text}' (qos={qos}, retain={retain}, mid={r.mid})")

def repl(client):
    print("\n=== MQTT Control Console ===")
    print("Commands:")
    print("  start                 -> send 'start'")
    print("  hello                 -> send 'hello'")
    print("  seq                   -> send 'instruction 2 3 3 1'")
    print("  raw <text>            -> publish arbitrary text")
    print("  quit                  -> exit\n")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[SHUTDOWN] Bye!")
            break

        if not line:
            continue
        if line == "quit":
            break
        if line == "start":
            send_text(client, "start"); continue
        if line == "hello":
            send_text(client, "hello"); continue
        if line == "seq":
            send_text(client, "instruction 3 2 3 1"); continue
        if line.startswith("raw "):
            send_text(client, line[4:]); continue

        print("[INFO] Unknown command. Try: start | hello | seq | raw <text> | quit")

# ---------- main ----------
if __name__ == "__main__":
    # Use a UNIQUE client_id to avoid collisions with mosquitto_pub/Arduino
    client = mqtt.Client(
        client_id="python_console_" + str(int(time.time())),
        clean_session=True,           # v3.1.1
        protocol=mqtt.MQTTv311
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()          # run network loop in background
    time.sleep(1.5)              # small grace period

    try:
        repl(client)
    finally:
        client.loop_stop()
        client.disconnect()
