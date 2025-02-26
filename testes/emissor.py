import socket
import time
import pyaudio

UDP_IP = "192.168.1.3"  # Endereço de broadcast ou ajuste conforme necessário
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Configuração do PyAudio para captar áudio do microfone
CHUNK = 256
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Capturando áudio do microfone...")

try:
    while True:
        data = stream.read(CHUNK)
        sock.sendto(data, (UDP_IP, UDP_PORT))
        # Calcular tempo baseado no tamanho dos dados (2 bytes por amostra) - opcional
        #sleep_time = len(data) / (RATE * 2)
        #time.sleep(sleep_time)
except KeyboardInterrupt:
    print("Transmissão interrompida")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    sock.close()