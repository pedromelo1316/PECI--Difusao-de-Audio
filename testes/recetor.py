import subprocess
import socket
import pyaudio
import threading  # Adicionado threading
import struct       # Adicionado

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

MULTIPLICADOR = 20   # Ajuste conforme necessário max 65

# Configurar socket UDP multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
sock.bind(("", MCAST_PORT))

# Entrar no grupo multicast
mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

FREQ = 48000
CHUNCK_SIZE = 960

p_instance = pyaudio.PyAudio()
stream = p_instance.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=int(FREQ),  # Taxa de amostragem do Opus
                         output=True,
                         frames_per_buffer=CHUNCK_SIZE*MULTIPLICADOR)

# Comando FFmpeg para decodificar Opus e reproduzir áudio
ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner",
    "-loglevel", "error",
    # Configurações de entrada
    "-f", "ogg",
    "-i", "pipe:0",
    # Configurações de saída
    "-f", "s16le",
    "-acodec", "pcm_s16le",
    "-ar", str(FREQ),
    "-ac", "1",
    "pipe:1"
]
# Alterado para capturar a saída do ffmpeg
ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def ffmpeg_reader():
    while True:
        data = ffmpeg_proc.stdout.read(CHUNCK_SIZE*MULTIPLICADOR)
        if not data:
            break
        stream.write(data)

# Iniciar thread para ler do ffmpeg e enviar para a stream
reader_thread = threading.Thread(target=ffmpeg_reader, daemon=True)
reader_thread.start()

channel = 0
seq = None
last_seq = None
try:
    while True:
        # Receber dados Opus via UDP
        packet, addr = sock.recvfrom(CHUNCK_SIZE*MULTIPLICADOR + 5)  # Tamanho máximo de um pacote UDP

        # Desempacotar os 4 primeiros bytes para obter o canal
        packet_channel = struct.unpack('!I', packet[0:4])[0]

        print(packet_channel)

        if channel != packet_channel:
            continue

        

        seq = packet[4]
        if last_seq is not None and seq != (last_seq + 1) % 256:
            print(f"Esperado: {last_seq + 1}, recebido: {seq}")
        last_seq = seq

        opus_data = packet[5:]
        
        # Enviar dados para o ffmpeg decodificar e reproduzir
        if ffmpeg_proc.poll() is not None:
            print("ffmpeg terminou")
            break
        ffmpeg_proc.stdin.write(opus_data)
        
except KeyboardInterrupt:
    print("Recepção interrompida.")
finally:
    ffmpeg_proc.terminate()
    reader_thread.join(timeout=1)
    stream.stop_stream()
    stream.close()
    p_instance.terminate()
    sock.close()