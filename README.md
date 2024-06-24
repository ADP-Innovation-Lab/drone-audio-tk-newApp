# drone-audio-tk-newApp
main.py
---------
1. Import necessary modules and functions
2. Define start_call, end_call, and on_closing functions
3. Initialize and run the App class from gui.py

gui.py
---------
1. Import necessary modules
2. Define the App class
   - Initialize the GUI window
   - Create left and right frames
   - Add buttons and map to the GUI
   - Define methods for button actions and map interactions

logger.py
---------
1. Set up logging configuration
2. Define a logger instance for the app

mqtt.py
---------
1. Import necessary modules
2. Define connect_mqtt function to establish MQTT connection
3. Define on_message callback to handle incoming MQTT messages
4. Define subscribe function to subscribe to MQTT topics
5. Define publish function to send MQTT messages

voip.py
---------
1. Import necessary modules
2. Define start_client function to initiate audio call
   - Establish socket connection
   - Set up audio input and output streams
   - Start threads for receiving and sending audio data
3. Define stop_client function to terminate audio call
   - Close socket and audio streams
   - Join threads
