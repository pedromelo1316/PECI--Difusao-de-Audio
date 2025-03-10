import socket
import pyaudio
import opuslib  # Instale via pip: pip install opuslib

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurações do Opus (devem coincidir com o emissor)
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms

# Inicializa o decoder Opus
decoder = opuslib.Decoder(SAMPLE_RATE, CHANNELS)

# Configura o PyAudio para reprodução
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True,
    frames_per_buffer=FRAME_SIZE
)

# Configura o socket multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", MCAST_PORT))

# Junta-se ao grupo multicast
mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

print("Escutando multicast (Opus)...")

try:
    while True:
        opus_frame, addr = sock.recvfrom(4096)  # Tamanho típico de um frame Opus
        
        # Decodifica o frame Opus para PCM
        pcm_frame = decoder.decode(opus_frame, FRAME_SIZE)
        
        # Reproduz o áudio
        stream.write(pcm_frame)
        
except KeyboardInterrupt:
    print("Recepção interrompida.")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    sock.close()