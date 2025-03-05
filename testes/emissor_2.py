import subprocess
import socket
import threading
import queue
import time
import struct
import os

MULTICAST_GROUP = "224.1.1.1"
UDP_IP = MULTICAST_GROUP
UDP_PORT = 5005
CHUNK_SIZE = 960  # Tamanho de chunk recomendado para Opus (20 ms de áudio)
PACKET_SIZE = 2 * CHUNK_SIZE
FREQ = "48000"
QUAL = "16k"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ttl = 1
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl))

# Configura o stdout dos processos FFmpeg para ser não bufferizado
def start_ffmpeg_process(input_file, is_mic=False):
    if is_mic:
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-f", "alsa", "-i", "default",
            "-acodec", "libopus",
            "-b:a", QUAL,
            "-ar", FREQ,
            "-ac", "1",
            "-f", "opus",
            "pipe:1"
        ]
    else:
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-re",
            "-vn",
            "-i", input_file,
            "-acodec", "libopus",
            "-b:a", QUAL,
            "-ar", FREQ,
            "-ac", "1",
            "-f", "opus",
            "pipe:1"
        ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=int(CHUNK_SIZE/2))  # Desativa bufferização
    return process

# Inicializa os processos
process_local = start_ffmpeg_process("Playlist/audio.mp3")
process_mic = start_ffmpeg_process(None, is_mic=True)

local_queue = queue.Queue()
mic_queue = queue.Queue()

def get_local():
    while True:
        try:
            start_time = time.time()
            data = process_local.stdout.read(CHUNK_SIZE)
            read_time = time.time() - start_time
            #print(f"Tempo de leitura local: {read_time:.6f} segundos")
            if not data:
                local_queue.put((None, 'local'))
                break
            local_queue.put((data, 'local'))
        except Exception as e:
            print(f"Erro na leitura local: {e}")
            break

def get_mic():
    while True:
        try:
            start_time = time.time()
            data = process_mic.stdout.read(CHUNK_SIZE)
            read_time = time.time() - start_time
            #print(f"Tempo de leitura mic: {read_time:.6f} segundos")
            if not data:
                mic_queue.put((None, 'mic'))
                break
            mic_queue.put((data, 'mic'))
        except Exception as e:
            print(f"Erro na leitura mic: {e}")
            break


def send_packets():

    local_data = None
    mic_data = None
    seq_local = 0
    seq_mic = 0

    while True:

        if local_data is None:
            try:
                local_data, _ = local_queue.get(timeout=0.1)
            except Exception as e:
                pass

        if mic_data is None:
            try:
                mic_data, _ = mic_queue.get(timeout=0.1)
            except Exception as e:
                pass


        if local_data is not None:
            sock.sendto(bytes([seq_local])+bytes([0])+local_data, (UDP_IP, UDP_PORT))
            seq_local = (seq_local + 1) % 256
            print(f"Enviado pacote local {seq_local}")
            local_data = None

        if mic_data is not None:
            sock.sendto(bytes([seq_mic])+bytes([1])+mic_data, (UDP_IP, UDP_PORT))
            seq_mic = (seq_mic + 1) % 256
            print(f"Enviado pacote mic {seq_mic}")
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