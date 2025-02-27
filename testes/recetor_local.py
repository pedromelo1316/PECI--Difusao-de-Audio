import socket
import time
import pyaudio
import subprocess
import threading

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
CHUNK_SIZE = 1024  # Tamanho do chunk ajustado para corresponder ao emissor

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

p_instance = pyaudio.PyAudio()
stream = p_instance.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=44100,
                         output=True,
                         frames_per_buffer=CHUNK_SIZE)

ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-f", "mp3",
    "-i", "pipe:0",
    "-f", "s16le",
    "-acodec", "pcm_s16le",
    "-ar", "44100",
    "-ac", "1",
    "pipe:1"
]
process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
count = 0
last_seq = None  # Variável global para o último número de sequência

def udp_receiver():
    global count, last_seq
    while True:
        try:
            data, _ = sock.recvfrom(CHUNK_SIZE * 2 + 1)  # buffer maior para o byte extra
            if data:
                # Extrair o número de sequência (primeiro byte) e o dado real
                packet_seq = data[0]
                audio_data = data[1:]
                # Verificar pacotes perdidos
                if last_seq is not None:
                    expected_seq = (last_seq + 1) % 256
                    if packet_seq != expected_seq:
                        missing = expected_seq
                        while missing != packet_seq:
                            print(f"\nPacote {missing} foi perdido")
                            missing = (missing + 1) % 256
                last_seq = packet_seq
                count += len(audio_data)
                print(f"\rRecebido {count} bytes", end="")
                process.stdin.write(audio_data)
                process.stdin.flush()
        except Exception as e:
            print(f"\nErro na recepção: {e}")
            break

def audio_player():
    while True:
        try:
            pcm_chunk = process.stdout.read(CHUNK_SIZE)
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

print("Reproduzindo áudio local...")

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