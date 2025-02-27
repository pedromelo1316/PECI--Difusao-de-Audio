import socket
import queue
import threading
import time
import numpy as np
import pyaudio
import struct

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
CHUNK_SIZE = 512             # Tamanho total do pacote
HALF_SIZE = CHUNK_SIZE // 2  # 256 bytes por canal

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Pergunta ao usuário a opção de extração
option = input("Escolha o canal a reproduzir:\n1) Áudio local (primeiros 256 bytes)\n2) Áudio da voz (segundos 256 bytes)\nOpção: ")

# Inicializar queue para armazenar os dados recebidos
audio_queue = queue.Queue()
received_count = 0   # Contador de pacotes recebidos
played_count = 0
recv_start_time = None
play_start_time = None

def receive_udp(q, stop_event):
    global received_count, recv_start_time
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(CHUNK_SIZE)
            if data:
                if recv_start_time is None:
                    recv_start_time = time.time()
                if option.strip() == "1":
                    # Extrair os primeiros 256 bytes (áudio local)
                    extracted = data[0:HALF_SIZE] if len(data) >= HALF_SIZE else data + b'\x00'*(HALF_SIZE - len(data))
                else:
                    # Extrair os últimos 256 bytes (áudio da voz)
                    extracted = data[HALF_SIZE:CHUNK_SIZE] if len(data) >= CHUNK_SIZE else (data[HALF_SIZE:] + b'\x00'*(CHUNK_SIZE - len(data))) if len(data) > HALF_SIZE else b'\x00'*HALF_SIZE
                q.put(extracted)
                received_count += 1
                print(f"Pacotes recebidos: {received_count}", end="\r", flush=True)
        except Exception:
            break

def wait_queue(q, stop_event, min_buffer_size=40):
    while q.qsize() < min_buffer_size and not stop_event.is_set():
        #print(f"Waiting for buffer... Queue size: {q.qsize()}")
        time.sleep(0.01)

class VolumeControl:
    def __init__(self, volume=1.0):
        self.volume = volume
    def getVolume(self):
        return self.volume

def play_audio_from_queue(q, stop_event, volume_control, min_buffer_size=100):
    global played_count, play_start_time
    p_instance = pyaudio.PyAudio()
    stream = p_instance.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=44100,
                             output=True,
                             frames_per_buffer=256)
    wait_queue(q, stop_event, min_buffer_size)
    print("Starting audio playback...")
    try:
        while not stop_event.is_set():
            if not q.empty():
                data = q.get()
                if play_start_time is None:
                    play_start_time = time.time()
                volume = volume_control.getVolume()
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_data = np.clip(audio_data * volume, -32768, 32767).astype(np.int16)
                stream.write(audio_data.tobytes())
                played_count += 1
            else:
                #print(f"Buffer underrun... {q.qsize()}")
                wait_queue(q, stop_event, min_buffer_size)
                #time.sleep(0.005)
    finally:
        stream.stop_stream()
        stream.close()
        p_instance.terminate()

if __name__ == "__main__":
    stop_event = threading.Event()
    volume_control = VolumeControl(1.0)
    receiver_thread = threading.Thread(target=receive_udp, args=(audio_queue, stop_event))
    player_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event, volume_control))
    
    receiver_thread.start()
    player_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
    
    receiver_thread.join()
    player_thread.join()
    sock.close()