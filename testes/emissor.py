import socket
import time
from pydub import AudioSegment
import opuslib
import subprocess
import os

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurações do Opus (ajuste conforme a qualidade desejada)
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms (para latência balanceada)
BITRATE = 256000  # Bitrate desejado (64kbps para voz, 256kbps para música)
COMPLEXITY = 10   # Complexidade (0-10, maior = mais CPU/melhor qualidade)
APPLICATION = "audio"  # "voip", "audio", "restricted_lowdelay"
source = "default"

# Inicializa o encoder Opus com configurações de qualidade
encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, APPLICATION)
encoder.bitrate = BITRATE
encoder.complexity = COMPLEXITY

# Configura o socket multicast
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
    "-re",                  # Lê a entrada em tempo real
    "-f", "concat",          # Utiliza o arquivo de concatenação
    "-safe", "0",            # Permite caminhos absolutos/relativos
    "-i", f"Playlists/{source}.txt",
    "-af", "apad",           # Preenche com silêncio entre músicas
    "-vn",
    "-f", "s16le",           # Saída em PCM 16-bit little-endian
    "-ar", str(SAMPLE_RATE),
    "-ac", str(CHANNELS),
    "pipe:1"
]

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=0)

print(f"Enviando áudio via multicast (Opus) - Bitrate: {BITRATE/1000}kbps...")


seq = 0
try:
    while True:
        pcm_frame = b""
        while len(pcm_frame) < FRAME_SIZE * 2:
            chunk = process.stdout.read(FRAME_SIZE * 2 - len(pcm_frame))
            pcm_frame += chunk

        if len(pcm_frame) != FRAME_SIZE * 2:
            break

        # Codifica o frame PCM para Opus
        opus_frame = encoder.encode(pcm_frame, FRAME_SIZE)
    
        # Envia o frame codificado
        sock.sendto(opus_frame, (MCAST_GRP, MCAST_PORT))
        seq = (seq + 1) % 256
        #time.sleep((FRAME_SIZE / SAMPLE_RATE)*0.9)  # Tempo proporcional ao frame (ex: 0.02s para 960 amostras)
except KeyboardInterrupt:
    print("Transmissão interrompida.")
finally:
    sock.close()
