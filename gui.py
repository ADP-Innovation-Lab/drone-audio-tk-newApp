import customtkinter
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import os
import json
import logger
import mqtt  
import threading
import time

log = logger.logger

customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):

    APP_NAME = "ADP | Drone Call System"
    WIDTH = 1200
    HEIGHT = 800

    def __init__(self, start_call, end_call, on_closing, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start_call = start_call
        self.voip_end_call = end_call
        self.on_closing = on_closing

        self.title(App.APP_NAME)
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.marker_list = {}
        self.selected_drone_id = None
        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Added for status bar at the bottom

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============

        self.frame_left.grid_rowconfigure(0, weight=0)
        self.frame_left.grid_rowconfigure(1, weight=0)
        self.frame_left.grid_rowconfigure(2, weight=0)
        self.frame_left.grid_rowconfigure(3, weight=0)
        self.frame_left.grid_rowconfigure(4, weight=0)
        self.frame_left.grid_rowconfigure(5, weight=0)
        self.frame_left.grid_rowconfigure(6, weight=0)
        self.frame_left.grid_rowconfigure(7, weight=1)  # Make row 7 expand to take up extra space

        # Load and resize the image
        image_path = os.path.join(os.path.dirname(__file__), "images", "logo2.png")
        self.logo_image = customtkinter.CTkImage(Image.open(image_path), size=(150, 150))

        #self.drone_icon_path = os.path.join(os.path.dirname(__file__), "images", "online.png")
        #self.drone_icon_image = Image.open(self.drone_icon_path).resize((25, 25))
        
        self.drone_online_path = os.path.join(os.path.dirname(__file__), "images", "online.png")
        self.drone_online_image = ImageTk.PhotoImage(Image.open(self.drone_online_path).resize((64, 64)))

        self.drone_offline_path = os.path.join(os.path.dirname(__file__), "images", "offline.png")
        self.drone_offline_image = ImageTk.PhotoImage(Image.open(self.drone_offline_path).resize((64, 64)))

        self.logo_label = customtkinter.CTkLabel(master=self.frame_left, text="", image=self.logo_image)
        self.logo_label.grid(pady=(20, 20), padx=(20, 20), row=0, column=0, sticky="n")

        self.drone_label = customtkinter.CTkLabel(master=self.frame_left, text="Select Drone:", anchor="w", font=("Helvetica", 12, "bold"))
        self.drone_label.grid(row=1, column=0, padx=(0, 0), pady=(0, 0))

        # Load drone IDs from drones.json and set them to the dropdown menu
        drone_ids = self.load_drone_ids()
        self.drone_select_menu = customtkinter.CTkOptionMenu(self.frame_left, values=drone_ids, command=self.drone_select)
        self.drone_select_menu.grid(row=2, column=0, padx=(20, 20), pady=(10, 0))

        self.make_call_button = customtkinter.CTkButton(master=self.frame_left, text="Make Call", fg_color="green", command=self.make_call_button)
        self.make_call_button.grid(pady=(20, 0), padx=(20, 20), row=3, column=0)
        self.make_call_button.bind("<Enter>", lambda e: self.show_tooltip("Make a call"))
        self.make_call_button.bind("<Leave>", lambda e: self.hide_tooltip())

        self.end_call_button = customtkinter.CTkButton(master=self.frame_left, text="End Call", fg_color="red", command=self.end_call_button)
        self.end_call_button.grid(pady=(20, 0), padx=(20, 20), row=4, column=0)
        self.end_call_button.bind("<Enter>", lambda e: self.show_tooltip("End the call"))
        self.end_call_button.bind("<Leave>", lambda e: self.hide_tooltip())

        self.settings_button = customtkinter.CTkButton(master=self.frame_left, text="Settings", command=self.open_settings)
        self.settings_button.grid(pady=(20, 0), padx=(20, 20), row=5, column=0)

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="type address")
        self.entry.grid(row=0, column=0, sticky="we", padx=(0, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_5.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        # ============ status bar ============

        self.status_frame = customtkinter.CTkFrame(master=self, height=30, corner_radius=0, fg_color=None)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="we")

        # Configure the columns to allow the labels to align properly
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.status_frame.grid_columnconfigure(2, weight=1)

        self.connected_label = customtkinter.CTkLabel(master=self.status_frame, text="Server: Connected", anchor="w", fg_color="gray20")
        self.connected_label.grid(row=0, column=0, padx=(20, 20), pady=(5, 5), sticky="w")

        self.status_label = customtkinter.CTkLabel(master=self.status_frame, text="Status: Idle", anchor="center", fg_color="gray20")
        self.status_label.grid(row=0, column=1, padx=(20, 20), pady=(5, 5), sticky="")

        self.copyright_label = customtkinter.CTkLabel(master=self.status_frame, text="ADP Applied Innovation Lab © 2024", anchor="e",
                                                      text_color="#1f6aa5", font=("Helvetica", 16, "bold"))
        self.copyright_label.grid(row=0, column=2, padx=(20, 20), pady=(5, 5), sticky="e")

        # ============ Set Map default values
        self.map_widget.set_address("Abu Dhabi")
        #self.map_option_menu.set("Google satellite")
        #self.appearance_mode_optionemenu.set("Dark")

        # ============ Load initial markers from drones.json ============
        self.load_initial_markers()

        # ============ MQTT Connection ============
        mqtt.connect_mqtt(self)
        # ============Start periodic update
        #self.start_periodic_update()

    def load_initial_markers(self):
        drones = self.load_drones()
        for drone in drones:
            self.add_drone_marker(drone['drone_id'], drone['lat'], drone['long'], drone['bat'], drone['lastseen'])

    def add_drone_marker(self, drone_id, lat, long, bat, lastseen):
        marker_image = self.get_drone_image(lastseen)
        marker = self.map_widget.set_marker(lat, long, text=f"{drone_id} ({bat})", icon=marker_image)
        self.marker_list[drone_id] = marker

    def update_drone_marker(self, drone_id, lat, long, bat, lastseen):
        if drone_id in self.marker_list:
            marker = self.marker_list[drone_id]
            marker.set_position(lat, long)
            marker.set_text(f"{drone_id} ({bat})")
            #marker.set_image(self.get_drone_image(lastseen))
            #marker.set_icon(self.get_drone_image(lastseen))
        else:
            self.add_drone_marker(drone_id, lat, long, bat, lastseen)


    def get_drone_image(self, lastseen):
        
        lastseen_time = datetime.fromisoformat(lastseen.replace('Z', ''))
        current_time = datetime.utcnow()

        if current_time - lastseen_time > timedelta(minutes=10):
            return self.drone_offline_image
        else:
            return self.drone_online_image
        
    def start_periodic_update(self):
        def update():
            while True:
                self.update_all_markers()
                time.sleep(10)
                
        threading.Thread(target=update, daemon=True).start()

    def update_all_markers(self):
        with open('drones.json', 'r') as file:
            drones = json.load(file)
            for drone in drones:
                self.update_drone_marker(drone['drone_id'], drone['lat'], drone['long'], drone['bat'], drone['lastseen'])

    def load_drones(self):
        try:
            with open('drones.json', 'r') as f:
                drones = json.load(f)
                return drones
        except FileNotFoundError:
            log.error("Drones file not found.")
            return []
        
    def load_drone_ids(self):
        try:
            with open('drones.json', 'r') as f:
                drones = json.load(f)
                drone_ids = [drone['drone_id'] for drone in drones]
                return drone_ids
        except FileNotFoundError:
            log.error("Drones file not found.")
            return []

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            log.error("Config file not found.")
            return {
                "server_ip": "3.208.18.29",
                "server_port": "50007",
                "mqtt_broker": "broker.hivemq.com",
                "mqtt_port": "1883"
            }

    def open_settings(self):
        log.info("Opening settings window")
        self.settings_window = customtkinter.CTkToplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x300")
        self.settings_window.attributes('-topmost', True)  # Make the settings window appear on top

        self.config_entries = {}

        config_data = self.load_config()
        
        # Move Tile Server options to settings window
        self.map_label = customtkinter.CTkLabel(self.settings_window, text="Map Server:", anchor="w")
        self.map_label.grid(row=0, column=0, padx=(20, 20), pady=(10, 0))

        self.map_option_menu = customtkinter.CTkOptionMenu(self.settings_window, values=["Google normal", "OpenStreetMap", "Google satellite"],
                                                           command=self.change_map)
        self.map_option_menu.grid(row=1, column=0, padx=(20, 20), pady=(10, 0))

        # Move Appearance Mode options to settings window
        self.appearance_mode_label = customtkinter.CTkLabel(self.settings_window, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=0, column=1, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.settings_window, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=1, column=1, padx=(20, 20), pady=(10, 0))

        config_labels = ["Server IP:", "Server Port:", "MQTT Broker:", "MQTT Port:"]
        config_keys = ["server_ip", "server_port", "mqtt_broker", "mqtt_port"]

        for i, label in enumerate(config_labels, start=4):
            customtkinter.CTkLabel(self.settings_window, text=label, anchor="w").grid(row=i, column=0, padx=(20, 20), pady=(10, 0))
            self.config_entries[config_keys[i - 4]] = customtkinter.CTkEntry(self.settings_window)
            self.config_entries[config_keys[i - 4]].insert(0, config_data[config_keys[i - 4]])
            self.config_entries[config_keys[i - 4]].grid(row=i, column=1, padx=(20, 20), pady=(10, 0))

        # Add Save and Close buttons
        self.save_button = customtkinter.CTkButton(master=self.settings_window, text="Save", command=self.save_settings)
        self.save_button.grid(row=8, column=0, padx=(20, 20), pady=(10, 10))

        self.close_button = customtkinter.CTkButton(master=self.settings_window, text="Close", command=self.settings_window.destroy)
        self.close_button.grid(row=8, column=1, padx=(20, 20), pady=(10, 10))

    def save_settings(self):
        new_config = {}
        for key, entry in self.config_entries.items():
            new_config[key] = entry.get()

        with open('config.json', 'w') as f:
            json.dump(new_config, f, indent=4)

        log.info("Configuration saved and MQTT client reconnected")
        
        # Reset MQTT connection
        mqtt.disconnect_mqtt()
        mqtt.connect_mqtt(self)

        self.settings_window.destroy()

    def show_tooltip(self, text):
        self.tooltip = customtkinter.CTkLabel(master=self.frame_left, text=text, corner_radius=5, fg_color="grey")
        self.tooltip.place(x=20, y=450)

    def hide_tooltip(self):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

    def search_event(self, event=None):
        address = self.entry.get()
        if address:
            self.map_widget.set_address(address)
            log.info(f"Searching for address: {address}")

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))
        log.info(f"Setting marker at position: {current_position}")

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()
        self.marker_list.clear()
        log.info("Clearing all markers.")

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        log.info(f"Changing appearance mode to: {new_appearance_mode}")

    def change_map(self, new_map: str):
        if new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        log.info(f"Changing map to: {new_map}")

    def drone_select(self, selection):
        log.info(f"Drone selected: {selection}")
        self.selected_drone_id = selection
        self.status_label.configure(text=f"Status: {selection} selected")

    def make_call_button(self):
        log.info("Make call button pressed")
        mqtt.mqtt_start_call( self.selected_drone_id)
        self.status_label.configure(text="Status: Calling...")
        self.start_call()

    def end_call_button(self):
        log.info("End call button pressed")
        mqtt.mqtt_end_call( self.selected_drone_id)
        self.status_label.configure(text="Status: Call ended")
        
        self.voip_end_call()

    def start(self):
        self.mainloop()
