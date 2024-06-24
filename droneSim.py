import paho.mqtt.client as mqtt
import time
import json

mqtt_config = {
    "mqtt_broker": "broker.hivemq.com",
    "mqtt_port": 1883
}

drone_id = "drone101"
publish_topic = f"{drone_id}/data"
subscribe_topic = f"{drone_id}/call"

msg = {
    "drone_id": drone_id,
    "lat": 24.51,
    "long": 54.643,
    "bat": "85%"
}

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(subscribe_topic)

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")

def simulate_north_movement():
    global msg
    msg["lat"] += 0.01

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_config["mqtt_broker"], mqtt_config["mqtt_port"], 60)

client.loop_start()

try:
    while True:
        simulate_north_movement()
        client.publish(publish_topic, json.dumps(msg))
        print(f"Published: {json.dumps(msg)}")
        time.sleep(10)
except KeyboardInterrupt:
    print("Exiting...")

client.loop_stop()
client.disconnect()
