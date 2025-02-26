import os, subprocess, time, socket, threading, queue
import pyaudio
import numpy as np

# Configurações UDP
UDP_IP = "255.255.255.255"  # ajuste conforme necessário
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Parâmetros de áudio
RATE = 44100
CHANNELS = 1
FORMAT = pyaudio.paInt16
# Cada frame = 2 bytes (s16le); usar 128 frames para 256 bytes por fonte
CHUNK_FRAMES = 128  
CHUNK_BYTES = CHUNK_FRAMES * 2      # 256 bytes

# Inicializar PyAudio para microfone
p = pyaudio.PyAudio()
mic_stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_FRAMES)

# Queues para cada fonte
mic_queue = queue.Queue()
file_queue = queue.Queue()
stop_event = threading.Event()

# Adicionar condições para sincronização de filas
mic_condition = threading.Condition()
file_condition = threading.Condition()

def get_mic_audio(q, stop_event):
    while not stop_event.is_set():
        try:
            data = mic_stream.read(CHUNK_FRAMES)
            with mic_condition:
                while not q.empty():
                    mic_condition.wait(timeout=0.01)
                q.put(data)
                mic_condition.notify_all()
        except Exception:
            break

def get_local_audio(q, stop_event):
    playlist_dir = "Playlist"  # Pasta com arquivos .mp3
    files = [os.path.join(playlist_dir, f) for f in os.listdir(playlist_dir) if f.lower().endswith(".mp3")]
    if not files:
        stop_event.set()
        return
    file_index = 0
    while not stop_event.is_set():
        current_file = files[file_index]
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", current_file,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(RATE),
            "-ac", str(CHANNELS),
            "pipe:1"
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while not stop_event.is_set():
                data = process.stdout.read(CHUNK_BYTES)
                if not data:
                    break
                with file_condition:
                    while not q.empty():
                        file_condition.wait(timeout=0.01)
                    q.put(data)
                    file_condition.notify_all()
        finally:
            if process.stdout:
                process.stdout.close()
            process.terminate()
            process.wait()
        file_index = (file_index + 1) % len(files)

# Iniciar threads das fontes
mic_thread = threading.Thread(target=get_mic_audio, args=(mic_queue, stop_event))
file_thread = threading.Thread(target=get_local_audio, args=(file_queue, stop_event))
mic_thread.start()
file_thread.start()

sent_count = 0   # Contador de pacotes enviados

print("Transmitindo áudio combinado (primeiros 256 local + segundos 256 voz)...")

try:
    while not stop_event.is_set():
        try:
            mic_data = mic_queue.get()
            with mic_condition:
                mic_condition.notify_all()
            file_data = file_queue.get()
            with file_condition:
                file_condition.notify_all()
        except queue.Empty:
            continue
        # Se os dados forem menores que CHUNK_BYTES, preencha com zeros
        if len(file_data) < CHUNK_BYTES:
            file_data += b'\x00' * (CHUNK_BYTES - len(file_data))
        if len(mic_data) < CHUNK_BYTES:
            mic_data += b'\x00' * (CHUNK_BYTES - len(mic_data))
        # Concatenar: primeiros 256 bytes do áudio local e depois 256 bytes do microfone
        packet = file_data[:CHUNK_BYTES] + mic_data[:CHUNK_BYTES]
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        sent_count += 1
        print(f"Pacotes enviados: {sent_count} mic: {mic_queue.qsize()} local: {file_queue.qsize()}", end="\r", flush=True)
except KeyboardInterrupt:
    stop_event.set()
finally:
    mic_thread.join()
    file_thread.join()
    mic_stream.stop_stream()
    mic_stream.close()
    p.terminate()
    sock.close()
