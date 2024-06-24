import paho.mqtt.client as mqtt
import json
import logger

log = logger.logger

# Global variables and configuration
mqtt_client = None
config = None

def load_config():
    global config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        log.info("Configuration loaded.")
    except FileNotFoundError:
        config = {
            "server_ip": "3.80.77.3",
            "server_port": "50007",
            "mqtt_broker": "broker.hivemq.com",
            "mqtt_port": "1883",
            "drone_id": "drone101"
        }
        log.warning("Configuration file not found. Using default configuration.")

def start_call():
    global mqtt_client
    log.info("Publishing start call message...")
    mqtt_client.publish(f"{config['drone_id']}/call", "on")

def end_call():
    global mqtt_client
    log.info("Publishing end call message...")
    mqtt_client.publish(f"{config['drone_id']}/call", "off")

def on_connect(client, userdata, flags, rc):
    log.info(f"Connected to MQTT broker with code {rc}.")
    #client.subscribe(f"{config['drone_id']}/data")

def on_message(client, userdata, message):
    msg = message.payload.decode()
    log.info(f"Received message on {message.topic}: {msg}")

def clean_exit():
    log.info("Cleaning up MQTT client...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

# MQTT setup
load_config()
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(config['mqtt_broker'], int(config['mqtt_port']), 60)
mqtt_client.loop_start()
log.info("MQTT client setup completed.")
