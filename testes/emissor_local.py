import os, subprocess, time, socket, threading, queue
import pyaudio

# Configurações UDP
UDP_IP = "192.168.1.3"  # ajuste conforme necessário
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Parâmetros de áudio
RATE = 44100
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_FRAMES = 256  
CHUNK_BYTES = CHUNK_FRAMES * 2      # 256 bytes

# Queue para áudio local e controle de sincronização
file_queue = queue.Queue()
stop_event = threading.Event()
file_condition = threading.Condition()

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
                else:
                    q.put(data)
                    time_to_sleep = len(data) / (RATE * 1.9)
                    time.sleep(time_to_sleep)
        finally:
            if process.stdout:
                process.stdout.close()
            process.terminate()
            process.wait()
        file_index = (file_index + 1) % len(files)

# Iniciar thread para áudio local
file_thread = threading.Thread(target=get_local_audio, args=(file_queue, stop_event))
file_thread.start()

sent_count = 0
print("Transmitindo áudio local...")

try:
    while not stop_event.is_set():
        file_data = file_queue.get()
        if len(file_data) < CHUNK_BYTES:
            file_data += b'\x00' * (CHUNK_BYTES - len(file_data))
        sock.sendto(file_data, (UDP_IP, UDP_PORT))
        sent_count += 1
        print(f"Pacotes enviados: {sent_count} [Fila: {file_queue.qsize()}]", end="\r", flush=True)
except KeyboardInterrupt:
    stop_event.set()
finally:
    file_thread.join()
    sock.close()
