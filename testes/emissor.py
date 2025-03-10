import subprocess
import socket
import time
import struct

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurações do FFmpeg
source = "default"    # Nome do arquivo de playlist
INPUT_FILE = "default"  # Dispositivo de áudio padrão
BITRATE = "64k"        # Ajuste conforme necessário
SAMPLE_RATE = "48000"   # Opus recomenda 48kHz
CHANNELS = "1"          # Mono
CHUNCK_SIZE = 960     # Tamanho do pacote (ajuste conforme a rede)
MULTIPLICADOR = 20   # Ajuste conforme necessário max 65


# Configurar socket UDP multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Comando FFmpeg para codificar em Opus e enviar para stdout
ffmpeg_command = [
    "ffmpeg",
    "-stream_loop", "-1",
    "-hide_banner", "-loglevel", "error",
    "-re",                   # Simula tempo real
    "-f", "concat",          # Utiliza o arquivo de concatenação
    "-safe", "0",            # Permite caminhos absolutos/relativos
    "-i", f"Playlists/{source}.txt",
    "-af", "apad",           # Preenche com silêncio entre músicas
    "-vn",                  # Sem vídeo
    "-c:a", "libopus",      # Codec Opus
    "-b:a", BITRATE,        # Bitrate (ex: 64k, 128k)
    "-ar", SAMPLE_RATE,     # Taxa de amostragem
    "-ac", CHANNELS,        # Canais
    "-f", "opus",           # Formato de saída: Opus bruto
    "-packet_size", str(CHUNCK_SIZE), # Tamanho do pacote (ajuste conforme a rede)
    "pipe:1"                # Saída para stdout
]

print("Codificando áudio com FFmpeg e enviando via multicast...")


processes = {}

NUM_PROCESSES = 3


for i in range(NUM_PROCESSES):
    processes[i] = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, bufsize=CHUNCK_SIZE*MULTIPLICADOR)

# Executar FFmpeg e ler a saída

seq = 0
count = 0
start_time = time.time()

try:
    while True:
        for i in range(NUM_PROCESSES):
            # Ler dados codificados em Opus do stdout do FFmpeg
            opus_data = processes[i].stdout.read(CHUNCK_SIZE*MULTIPLICADOR)  # Ajuste o tamanho conforme necessário
            if not opus_data:
                break
            
            dados = struct.pack('!I', i) + struct.pack('!B', seq) + opus_data
            sock.sendto(dados, (MCAST_GRP, MCAST_PORT))

            print(f"\rEnviado: {seq}, velocidade: {(count*CHUNCK_SIZE*MULTIPLICADOR)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")
            count += 1

        seq = (seq + 1)%256
        
except KeyboardInterrupt:
    print("Transmissão interrompida.")
finally:
    sock.close()
    for i in range(3):
        processes[i].terminate()
        processes[i].wait()