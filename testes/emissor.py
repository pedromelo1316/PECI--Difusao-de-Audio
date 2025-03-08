import socket
import time
import subprocess
import os
import threading

import opuslib  # se continuar utilizando para outras funções

# ...existing code...
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960
BITRATE = 256000
COMPLEXITY = 10
APPLICATION = "audio"
source = "default"

# Inicializa o socket multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

playlist_path = f"Playlists/{source}.txt"
if not os.path.exists(playlist_path):
    print(f"Playlist {playlist_path} not found")
    exit()

cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-stream_loop", "-1",
    "-re",
    "-f", "concat",
    "-safe", "0",
    "-i", f"Playlists/{source}.txt",
    "-af", "apad",
    "-vn",
    "-f", "s16le",
    "-ar", str(SAMPLE_RATE),
    "-ac", str(CHANNELS),
    "pipe:1"
]

def process_stream(i):
    # Inicia o subprocess de ffmpeg e o subprocess do encoder para este fluxo
    ffmpeg_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=FRAME_SIZE * 2)
    encoder_proc = subprocess.Popen(
        ["python3", "encoder_subprocess.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    try:
        while True:
            pcm_frame = ffmpeg_proc.stdout.read(FRAME_SIZE * 2)
            if len(pcm_frame) != FRAME_SIZE * 2:
                break

            # Envia o frame PCM para o subprocess de encoder
            encoder_proc.stdin.write(pcm_frame)
            encoder_proc.stdin.flush()

            # Lê os 2 bytes do tamanho do frame codificado
            size_bytes = encoder_proc.stdout.read(2)
            if not size_bytes:
                break
            frame_size = int.from_bytes(size_bytes, byteorder='big')

            # Lê o frame codificado
            opus_frame = encoder_proc.stdout.read(frame_size)
            if len(opus_frame) != frame_size:
                break

            # Envia o frame codificado via multicast (prefixado com o id do fluxo)
            sock.sendto(bytes([i]) + opus_frame, (MCAST_GRP, MCAST_PORT))
    except Exception as e:
        print(f"Erro no fluxo {i}: {e}")
    finally:
        ffmpeg_proc.terminate()
        encoder_proc.terminate()

threads = []
for i in range(3):
    t = threading.Thread(target=process_stream, args=(i,))
    t.daemon = True
    threads.append(t)
    t.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Transmissão interrompida.")
finally:
    sock.close()