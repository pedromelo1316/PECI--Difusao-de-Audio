import socket
import time
import pyaudio
import subprocess
import threading

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
CHUNK_SIZE = 960  # Tamanho de chunk recomendado para Opus (20 ms de áudio)
PACKET_SIZE = CHUNK_SIZE  # 2 canais de transmissão
FREQ = "48000"
HEADER_SIZE = 256

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))
MULTICAST_GROUP = "224.1.1.1"
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0"))



op = 0
while op != "0" and op != "1":
    op = input("Local(0) ou Voz(1)? ")
op = int(op)

# Adicione isso no início do receptor
control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
control_sock.sendto(b"connect", ("<broadcast>", 5006))  # Envia mensagem de conexão
control_sock.close()

p_instance = pyaudio.PyAudio()
stream = p_instance.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=int(FREQ),  # Taxa de amostragem do Opus
                         output=True,
                         frames_per_buffer=CHUNK_SIZE)

# Comando ffmpeg para decodificar Opus
ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-f", "ogg",  # Formato de entrada Opus (usar 'ogg' para Opus)
    "-i", "pipe:0",
    "-f", "s16le",  # Formato de saída PCM 16-bit
    "-acodec", "pcm_s16le",
    "-ar", FREQ,  # Taxa de amostragem de 48 kHz
    "-ac", "1",      # Mono
    "pipe:1"
]
process = None
count = 0
last_seq = None  # Variável global para o último número de sequência


def udp_receiver():
    global count, last_seq, process
    header = False

    while True:
        try:
            start_time = time.time()
            data, _ = sock.recvfrom(PACKET_SIZE + 2)  # buffer maior para o byte extra
            recv_time = time.time() - start_time
            if data:
                # Extrair o número de sequência (primeiro byte) e o dado real

                
                _type = data[1]
                packet_seq = data[0]

                if _type == 2 + op:
                    header = True
                    print("Header recebido.")
                    if process is None:
                        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        print("Processo FFmpeg iniciado.")
                    else:
                        process.stdin.close()
                        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        print("Processo FFmpeg reiniciado.")

                    process.stdin.write(data[2:])
                    process.stdin.flush()
                    continue

                if _type != op or not header:
                    continue

                audio_data = data[2:]

                if last_seq is None:
                    last_seq = packet_seq
                elif packet_seq != (last_seq + 1) % 256:
                    print(f"Pacote perdido: {last_seq} -> {packet_seq}")

                last_seq = packet_seq

                channel_data = audio_data

                process.stdin.write(channel_data)
                process.stdin.flush()

        except Exception as e:
            #print(f"\nErro na recepção: {e}")
            break

def audio_player():
    count = 0
    while True:
        try:
            if process is None:
                time.sleep(0.1)
                continue
            pcm_chunk = process.stdout.read(CHUNK_SIZE)
            count += len(pcm_chunk)
            if not pcm_chunk:
                break
            stream.write(pcm_chunk)
        except Exception as e:
            print(f"\nErro na reprodução: {e}")
            break

recv_thread = threading.Thread(target=udp_receiver, daemon=True)
play_thread = threading.Thread(target=audio_player, daemon=True)
recv_thread.start()
play_thread.start()

print("Reproduzindo áudio...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    process.stdin.close()
    process.terminate()
    recv_thread.join(1)
    play_thread.join(1)
    stream.stop_stream()
    stream.close()
    p_instance.terminate()
    sock.close()
    print("\nReprodução concluída.")