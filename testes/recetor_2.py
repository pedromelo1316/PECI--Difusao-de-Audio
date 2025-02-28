import socket
import time
import pyaudio
import subprocess
import threading

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
HELP_PORT = 5006
CHUNK_SIZE = 1024  # Tamanho do chunk ajustado para corresponder ao emissor
PACKET_SIZE = 2 * CHUNK_SIZE # 2 canais de transmissão

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))
MULTICAST_GROUP = "224.1.1.1"
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0"))

op = 0
while op != "1" and op != "2":
    op = input("Local(1) ou Voz(2)? ")

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
process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
count = 0
last_seq = None  # Variável global para o último número de sequência

# Buffer circular para armazenar pacotes
buffer_size = 256
audio_buffer = [None] * buffer_size
buffer_lock = threading.Lock()
buffer_condition = threading.Condition(buffer_lock)

def udp_receiver():
    global count, last_seq
    while True:
        try:
            data, _ = sock.recvfrom(PACKET_SIZE + 1)  # buffer maior para o byte extra
            if data:
                # Extrair o número de sequência (primeiro byte) e o dado real
                packet_seq = data[0]
                print(f"\nRecebido pacote {packet_seq}")
                audio_data = data[1:]
                # Verificar pacotes perdidos
                if last_seq is not None:
                    expected_seq = (last_seq + 1) % 256
                    if packet_seq != expected_seq:
                        missing = expected_seq
                        while missing != packet_seq:
                            print(f"\n----------------->Pacote {missing} foi perdido")
                            request_help(missing, "local" if op == "1" else "mic")
                            missing = (missing + 1) % 256
                last_seq = packet_seq
                count += len(audio_data)
                #print(f"\rRecebido {count} bytes", end="")

                # Dividir os dados de áudio em local e voz
                local_data = audio_data[:CHUNK_SIZE]
                voice_data = audio_data[CHUNK_SIZE:]

                with buffer_lock:
                    if op == "1":
                        audio_buffer[packet_seq] = local_data
                    else:
                        audio_buffer[packet_seq] = voice_data
                    buffer_condition.notify()  # Notifica o player_audio que um novo pacote está disponível

        except Exception as e:
            print(f"\nErro na recepção: {e}")
            break

def request_help(seq, source):
    help_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    help_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    help_message = f"HELP: {seq}".encode()
    help_sock.sendto(help_message, ('<broadcast>', HELP_PORT))
    help_sock.close()

def handle_help_responses():
    help_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    help_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    help_sock.bind(('', HELP_PORT))
    while True:
        data, addr = help_sock.recvfrom(PACKET_SIZE)
        if data:
            seq = data[0]
            with buffer_lock:
                audio_buffer[seq] = data[1:]
                buffer_condition.notify()  # Notifica o player_audio que um novo pacote está disponível

def converter():
    silence = b'\x00' * CHUNK_SIZE
    index = 0
    while True:
        try:
            with buffer_condition:
                while audio_buffer[index] is None:
                    buffer_condition.wait()  # Espera até que um novo pacote esteja disponível
                data = audio_buffer[index]
                audio_buffer[index] = None  # Limpa o buffer após a leitura
                buffer_condition.notify()  # Notifica o player_audio que o buffer foi atualizado
            if data is None:
                data = silence
            index = (index + 1) % buffer_size
            process.stdin.write(data)
        except Exception as e:
            print(f"\nErro na reprodução: {e}")
            break

def player_audio():
    while True:
        try:
            data = process.stdout.read(CHUNK_SIZE)
            if not data:
                break
            stream.write(data)
            with buffer_condition:
                buffer_condition.notify()  # Notifica o converter que o player_audio leu um pacote
        except Exception as e:
            print(f"\nErro na reprodução: {e}")
            break

recv_thread = threading.Thread(target=udp_receiver, daemon=True)
converter_thread = threading.Thread(target=converter, daemon=True)
player_audio_thread = threading.Thread(target=player_audio, daemon=True)
help_thread = threading.Thread(target=handle_help_responses, daemon=True)
recv_thread.start()
converter_thread.start()
player_audio_thread.start()
help_thread.start()

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
    converter_thread.join(1)
    player_audio_thread.join(1)
    help_thread.join(1)
    stream.stop_stream()
    stream.close()
    p_instance.terminate()
    sock.close()
    print("\nReprodução concluída.")