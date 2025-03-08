import socket
import pyaudio
import threading
import opuslib

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurações de áudio (PCM raw)
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms de áudio
BYTES_PER_FRAME = FRAME_SIZE * 2 # 2 bytes por amostra (16-bit)

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
mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

print("Escutando multicast (PCM raw)...")


def receive_and_play():
    last_seq = -1
    try:
        while True:
            # Recebe um pacote que contém um frame PCM (FRAME_SIZE * 2 bytes)
            opus_frame, addr = sock.recvfrom(4096)
            '''if not packet:
                break

            seq = packet[0]
            if last_seq == -1:
                last_seq = seq
            if seq != last_seq + 1:
                for i in range(last_seq + 1, seq):
                    print(f"Perdido: {i}")
            last_seq = seq'''
            #opus_frame = opus_frame[1:]  # Remove o byte de sequência
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

recv_thread = threading.Thread(target=receive_and_play)
recv_thread.start()
recv_thread.join()