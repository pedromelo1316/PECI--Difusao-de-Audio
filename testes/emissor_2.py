import subprocess
import socket
import threading
import queue
import time
import struct

MULTICAST_GROUP = "224.1.1.1"
UDP_IP = MULTICAST_GROUP
UDP_PORT = 5005
CHUNK_SIZE = 960*2  # Tamanho de chunk recomendado para Opus (20 ms de áudio)
PACKET_SIZE = 2 * CHUNK_SIZE
FREQ = "48000"
QUAL =  "16k"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ttl = 1
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl))

# Comando ffmpeg para capturar áudio local (codificado em Opus)
ffmpeg_local_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-re",
    "-vn",
    "-i", "Playlist/audio.mp3",
    "-acodec", "libopus",  # Usando Opus
    "-b:a", QUAL,         # Taxa de bits de 64 kbps
    "-ar", FREQ,        # Taxa de amostragem de 48 kHz
    "-ac", "1",            # Mono
    "-f", "opus",          # Formato de saída Opus
    "pipe:1"
]
process_local = subprocess.Popen(ffmpeg_local_cmd, stdout=subprocess.PIPE)

# Comando ffmpeg para capturar áudio do microfone (codificado em Opus)
ffmpeg_mic_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-f", "alsa", "-i", "default",
    "-acodec", "libopus",  # Usando Opus
    "-b:a", QUAL,         # Taxa de bits de 64 kbps
    "-ar", FREQ,        # Taxa de amostragem de 48 kHz
    "-ac", "1",            # Mono
    "-f", "opus",          # Formato de saída Opus
    "pipe:1"
]
process_mic = subprocess.Popen(ffmpeg_mic_cmd, stdout=subprocess.PIPE)

local_queue = queue.Queue()
mic_queue = queue.Queue()

def get_local():
    while True:
        start_time = time.time()
        data = process_local.stdout.read(CHUNK_SIZE)
        read_time = time.time() - start_time
        print(f"Tempo de leitura local: {read_time:.6f} segundos")
        if not data:
            local_queue.put((None, 'local'))
            break
        local_queue.put((data, 'local'))

def get_mic():
    while True:
        start_time = time.time()
        data = process_mic.stdout.read(CHUNK_SIZE)
        read_time = time.time() - start_time
        print(f"Tempo de leitura mic: {read_time:.6f} segundos")
        if not data:
            mic_queue.put((None, 'mic'))
            break
        mic_queue.put((data, 'mic'))

def send_packets():
    count = 0
    seq = 0
    local_data = None
    mic_data = None
    tempo = time.time()
    while True:
        if local_data is None:
            local_data, source = local_queue.get()
            if local_data is None:
                break
        if mic_data is None:
            mic_data, source = mic_queue.get()
            if mic_data is None:
                break
        if local_data and mic_data:
            packet = bytes([seq]) + local_data + mic_data
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            count += len(local_data) + len(mic_data)
            print(f"{seq} ->>>> {time.time() - tempo}")
            tempo = time.time()
            seq = (seq + 1) % 256
            time_to_sleep = (CHUNK_SIZE / int(FREQ)) - (time.time() - tempo)
            print(f"Tempo de espera calculado: {time_to_sleep:.6f} segundos")
            time.sleep(time_to_sleep)
            local_data = None
            mic_data = None

local_thread = threading.Thread(target=get_local, daemon=True)
mic_thread = threading.Thread(target=get_mic, daemon=True)
sender_thread = threading.Thread(target=send_packets)
local_thread.start()
mic_thread.start()
sender_thread.start()
local_thread.join()
mic_thread.join()
sender_thread.join()

process_local.stdout.close()
process_local.terminate()
process_local.wait()
process_mic.stdout.close()
process_mic.terminate()
process_mic.wait()
sock.close()
print("\nTransmissão concluída.")