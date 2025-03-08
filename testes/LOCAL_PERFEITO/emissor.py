import socket
import time
from pydub import AudioSegment
import opuslib
import subprocess

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Carrega e converte o áudio para formato compatível com Opus (48kHz, mono, 16-bit)
audio = AudioSegment.from_mp3("audio.mp3")
audio = audio.set_channels(1).set_frame_rate(48000).set_sample_width(2)  # Opus recomenda 48kHz
raw_data = audio.raw_data

# Configurações do Opus (ajuste conforme a qualidade desejada)
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms (para latência balanceada)
BITRATE = 128000  # Bitrate desejado (64kbps para voz, 256kbps para música)
COMPLEXITY = 10   # Complexidade (0-10, maior = mais CPU/melhor qualidade)
APPLICATION = "audio"  # "voip", "audio", "restricted_lowdelay"

# Inicializa o encoder Opus com configurações de qualidade
encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, APPLICATION)
encoder.bitrate = BITRATE
encoder.complexity = COMPLEXITY

# Configura o socket multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)


print(f"Enviando áudio via multicast (Opus) - Bitrate: {BITRATE/1000}kbps...")

try:
    for i in range(0, len(raw_data), FRAME_SIZE * 2):  # 2 bytes por amostra (16-bit)
        pcm_frame = raw_data[i:i + FRAME_SIZE * 2]
        
        # Codifica o frame PCM para Opus
        opus_frame = encoder.encode(pcm_frame, FRAME_SIZE)
        
        # Envia o frame codificado
        sock.sendto(opus_frame, (MCAST_GRP, MCAST_PORT))
        time.sleep((FRAME_SIZE / SAMPLE_RATE)*0.9)  # Tempo proporcional ao frame (ex: 0.02s para 960 amostras)
        
except KeyboardInterrupt:
    print("Transmissão interrompida.")
finally:
    sock.close()