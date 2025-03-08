import subprocess
import socket

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurações do FFmpeg
source = "default"    # Nome do arquivo de playlist
INPUT_FILE = "default"  # Dispositivo de áudio padrão
BITRATE = "128k"        # Ajuste conforme necessário
SAMPLE_RATE = "48000"   # Opus recomenda 48kHz
CHANNELS = "1"          # Mono
CHUNCK_SIZE = 960     # Tamanho do pacote (ajuste conforme a rede)

# Configurar socket UDP multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Comando FFmpeg para codificar em Opus e enviar para stdout
ffmpeg_command = [
    "ffmpeg",
    "-stream_loop", "-1",
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


for i in range(50):
    processes[i] = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, bufsize=CHUNCK_SIZE*2)

# Executar FFmpeg e ler a saída

try:
    while True:
        for i in range(50):
            # Ler dados codificados em Opus do stdout do FFmpeg
            opus_data = processes[i].stdout.read(CHUNCK_SIZE*2)  # Ajuste o tamanho conforme necessário
            if not opus_data:
                break
            
            # Enviar via UDP multicast
            sock.sendto(bytes([i]) + opus_data, (MCAST_GRP, MCAST_PORT))
        
except KeyboardInterrupt:
    print("Transmissão interrompida.")
finally:
    sock.close()
    for i in range(3):
        processes[i].terminate()
        processes[i].wait()