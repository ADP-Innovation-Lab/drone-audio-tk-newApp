import gui
import voip
import mqtt
import logger
import json

log = logger.logger

def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        log.error("Configuration file not found.")
        return None

config = load_config()

def start_call():
    if config:
        voip.start_client(config['server_ip'], int(config['server_port']))
    else:
        log.error("Cannot start call. Configuration not loaded.")

def end_call():
    voip.stop_client()

def open_settings():
    # Implement settings logic here
    pass

def on_closing():
    end_call()
    app.destroy()

app = gui.App(start_call, end_call, on_closing)
app.start()
