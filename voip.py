import socket
import pyaudio
import threading
import logger

log = logger.logger

client_socket = None
audio = None
stream_in = None
stream_out = None
receive_thread = None
send_thread = None
connected_to_server = False

def start_client(server_ip, server_port):
    global client_socket, audio, stream_in, stream_out, receive_thread, send_thread, connected_to_server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    log.info(f"Connected to server at {server_ip}:{server_port}")

    audio = pyaudio.PyAudio()

    # Output
    stream_out = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=1024)

    # Input
    stream_in = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    connected_to_server = True

    def receive():
        while connected_to_server:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                stream_out.write(data)
            except (ConnectionResetError, OSError):
                break

    def send():
        while connected_to_server:
            try:
                data = stream_in.read(1024)
                client_socket.sendall(data)
            except (ConnectionResetError, OSError):
                break

    receive_thread = threading.Thread(target=receive)
    send_thread = threading.Thread(target=send)

    receive_thread.start()
    send_thread.start()

def stop_client():
    global client_socket, audio, stream_in, stream_out, receive_thread, send_thread, connected_to_server
    connected_to_server = False
    if client_socket:
        client_socket.close()
    if stream_in:
        stream_in.stop_stream()
        stream_in.close()
    if stream_out:
        stream_out.stop_stream()
        stream_out.close()
    if audio:
        audio.terminate()

    if receive_thread:
        receive_thread.join()
    if send_thread:
        send_thread.join()

    log.info("Disconnected from server")
