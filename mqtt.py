import paho.mqtt.client as mqtt
import json
import logger
from datetime import datetime

log = logger.logger

# Global variables and configuration
mqtt_client = None
config = None
TOPICS = []


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

def load_drones():
    global TOPICS
    with open('drones.json', 'r') as file:
        drones = json.load(file)
        TOPICS = [f"{drone['drone_id']}/data" for drone in drones]

def mqtt_start_call():
    global mqtt_client
    log.info("Publishing start call message...")
    mqtt_client.publish(f"{config['drone_id']}/call", "on")

def mqtt_end_call():
    global mqtt_client
    log.info("Publishing end call message...")
    mqtt_client.publish(f"{config['drone_id']}/call", "off")


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    drone_id = payload['drone_id']
    lat = payload['lat']
    long = payload['long']
    bat = payload['bat']
    lastseen = datetime.utcnow().isoformat() + 'Z'
    # Update the drones.json file
    with open('drones.json', 'r') as file:
        drones = json.load(file)
    
    for drone in drones:
        if drone['drone_id'] == drone_id:
            drone['lat'] = lat
            drone['long'] = long
            drone['bat'] = bat
            drone['lastseen'] = lastseen
            break

    with open('drones.json', 'w') as file:
        json.dump(drones, file, indent=4)

    if userdata and userdata['app']:
        userdata['app'].update_drone_marker(drone_id, lat, long, bat, lastseen)

def connect_mqtt(app):
    global mqtt_client
    load_config()
    mqtt_client = mqtt.Client(userdata={'app': app})
    mqtt_client.on_message = on_message
    mqtt_client.connect(config['mqtt_broker'], int(config['mqtt_port']), 60)
    load_drones()
    for topic in TOPICS:
        mqtt_client.subscribe(topic)
    mqtt_client.loop_start()
    log.info("MQTT client setup completed.")

def disconnect_mqtt():
    log.info("Cleaning up MQTT client...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

def clean_exit():
    log.info("Cleaning up MQTT client...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
