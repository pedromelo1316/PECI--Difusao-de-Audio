#!/usr/bin/env python3
import sys
import opuslib

# Configurações do Opus (mesmas do emissor)
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms
BITRATE = 256000  # 256kbps por exemplo
COMPLEXITY = 10
APPLICATION = "audio"  # ou "voip", "restricted_lowdelay"

encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, APPLICATION)
encoder.bitrate = BITRATE
encoder.complexity = COMPLEXITY

while True:
    # Lê um frame PCM do stdin (PCM 16-bit little-endian: 2 bytes por amostra)
    pcm_frame = sys.stdin.buffer.read(FRAME_SIZE * 2)
    if not pcm_frame or len(pcm_frame) < FRAME_SIZE * 2:
        break
    # Codifica o frame PCM para Opus
    opus_frame = encoder.encode(pcm_frame, FRAME_SIZE)
    # Envia o tamanho do frame codificado em 2 bytes seguido do frame
    size = len(opus_frame)
    sys.stdout.buffer.write(size.to_bytes(2, byteorder='big'))
    sys.stdout.buffer.write(opus_frame)
    sys.stdout.buffer.flush()