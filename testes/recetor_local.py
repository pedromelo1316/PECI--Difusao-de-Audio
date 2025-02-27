import socket
import time
import pyaudio
import numpy as np

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
CHUNK_SIZE = 512

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

p_instance = pyaudio.PyAudio()
stream = p_instance.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=44100,
                         output=True,
                         frames_per_buffer=CHUNK_SIZE//2)  # frames_per_buffer em frames

print("Reproduzindo áudio local...")
received_count = 0

try:
    while True:
        data, addr = sock.recvfrom(CHUNK_SIZE)
        if data:
            audio_data = np.frombuffer(data, dtype=np.int16)
            stream.write(audio_data.tobytes())
            received_count += 1
            print(f"Pacotes recebidos: {received_count}", end="\r", flush=True)
except KeyboardInterrupt:
    pass
finally:
    stream.stop_stream()
    stream.close()
    p_instance.terminate()
    sock.close()
