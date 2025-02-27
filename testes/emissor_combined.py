import os, subprocess, time, socket, threading, queue
import pyaudio
import numpy as np

# Configurações UDP
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Parâmetros de áudio
RATE = 44100
CHANNELS = 1
FORMAT = pyaudio.paInt16
# Cada frame = 2 bytes (s16le); usar 128 frames para 256 bytes por fonte
CHUNK_FRAMES = 8192  
CHUNK_BYTES = CHUNK_FRAMES * 2      # 256 bytes

# Inicializar PyAudio para microfone
p = pyaudio.PyAudio()
mic_stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_FRAMES)

# Queues para cada fonte
mic_queue = queue.Queue(maxsize=10)
file_queue = queue.Queue(maxsize=10)
stop_event = threading.Event()

def get_mic_audio(stop_event):
    data = b''
    while not stop_event.is_set() and data == b'':
        data = mic_stream.read(CHUNK_FRAMES)

    return data



def get_local_audio(q_local, q_mic, stop_event):
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
                q_local.put(data)
                data = get_mic_audio(stop_event)
                # Block until space is available
                q_mic.put(data)

        except Exception:
            break
        finally:
            if process.stdout:
                process.stdout.close()
            process.terminate()
            process.wait()
        file_index = (file_index + 1) % len(files)

# Iniciar threads das fontes
#mic_thread = threading.Thread(target=get_mic_audio, args=(mic_queue, stop_event))
file_thread = threading.Thread(target=get_local_audio, args=(file_queue,mic_queue, stop_event))
#mic_thread.start()
file_thread.start()

sent_count = 0   # Contador de pacotes enviados

print("Transmitindo áudio combinado (primeiros 256 local + segundos 256 voz)...")

def send_data(data):
    sock.sendto(data, (MCAST_GRP, MCAST_PORT))

try:
    while not stop_event.is_set():
        try:
            # Blocking get calls will wait for items as soon as available
            mic_data = mic_queue.get()
            file_data = file_queue.get()
        except queue.Empty:
            time.sleep(0.01)
        # Se os dados forem menores que CHUNK_BYTES, preencha com zeros
        if len(file_data) < CHUNK_BYTES:
            file_data += b'\x00' * (CHUNK_BYTES - len(file_data))
        if len(mic_data) < CHUNK_BYTES:
            mic_data += b'\x00' * (CHUNK_BYTES - len(mic_data))
        # Concatenar: primeiros 256 bytes do áudio local e depois 256 bytes do microfone
        packet = file_data[:CHUNK_BYTES] + mic_data[:CHUNK_BYTES]
        send_data(packet)
        sent_count += 1
        print(f"Pacotes enviados: {sent_count} mic: {mic_queue.qsize()} local: {file_queue.qsize()}", end="\r", flush=True)
except KeyboardInterrupt:
    stop_event.set()
finally:
    #mic_thread.join()
    file_thread.join()
    mic_stream.stop_stream()
    mic_stream.close()
    p.terminate()
    sock.close()
