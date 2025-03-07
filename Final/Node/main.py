import socket
import uuid
import threading
import time
import node_client
import queue
import json
import pyaudio
import subprocess
import base64


UDP_IP = "0.0.0.0"
UDP_PORT = 8082
CHUNK_SIZE = 960  # Tamanho de chunk recomendado para Opus (20 ms de áudio)
FREQ = "48000"
HEADER_SIZE = 256

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))
MULTICAST_GROUP = "224.1.1.1"
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0"))

HEADER = None

LOCAL = 0
VOICE = 1
TRANSMISSION = 2

OP = 3

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



def wait_for_info(n, port=8081, stop_event=None):
    global process, HEADER, OP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        while True:
            data, addr = server_socket.recvfrom(1024)
            data = data.decode('utf-8')
            #print("Recebido de", addr, ":", data)
            try:
                dic = json.loads(data)
                if n.mac in dic.keys():
                    info = dic[n.mac]

                    if "removed" in info.keys():
                        print("Node removed")
                        stop_event.set()
                        break

                    # Se os valores forem null (None) atualiza para None explicitamente
                    channel = info["channel"] if info["channel"] is not None else None
                    volume = info["volume"] if info["volume"] is not None else None
                    _HEADER = info["header"] if info["header"] is not None else None
                    TRANSMISSION_type = info["type"] if info["type"] is not None else None
                    if TRANSMISSION_type == "LOCAL":
                        OP = LOCAL
                    elif TRANSMISSION_type == "VOICE":
                        OP = VOICE
                    elif TRANSMISSION_type == "TRANSMISSION":
                        OP = TRANSMISSION
                    else:
                        OP = 3
                    _HEADER = base64.b64decode(_HEADER) if _HEADER is not None else None
                    print("Header:", _HEADER)
                    n.setChannel(channel)
                    n.setVolume(volume)
                    if _HEADER != HEADER:
                        HEADER = _HEADER
                        print("Header atualizado.")
                        if process is None:
                            process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                            print("Processo FFmpeg iniciado.")
                            process.stdin.write(HEADER)
                            process.stdin.flush()
                        else:
                            process.stdin.close()
                            process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                            print("Processo FFmpeg reiniciado.")
                            process.stdin.write(HEADER)
                            process.stdin.flush()



                    print("Channel:", n.getChannel())
                    print("Volume:", n.getVolume())


            except ValueError as e:
                print("Error in wait_for_info:", e)


def wait_for_connection(n, port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.settimeout(5)
        while True:
            msg = f"{n.getName()},{n.getMac()}"
            client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', port))
            
            print("Sent information to manager")

            try:
                data, addr = client_socket.recvfrom(1024)
                if data == b"OK":
                    n.setHostIp(addr[0])
                    print("Connection established")
                    break
                else:
                    print("Connection refused")
                    time.sleep(5)
                    continue
            except:
                print("Connection refused")
                time.sleep(1)
        return True



def udp_receiver(stop_event = None):
    global count, last_seq, process

    while not stop_event.is_set():
        try:
            start_time = time.time()
            data, _ = sock.recvfrom(CHUNK_SIZE + 2)  # buffer maior para o byte extra
            recv_time = time.time() - start_time
            if data:
                # Extrair o número de sequência (primeiro byte) e o dado real

                packet_seq = data[0]
                _type = data[1]


                if _type != OP or not HEADER:
                    continue

                print(f"Recebido pacote {packet_seq} de {_type}")

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

def audio_player(stop_event = None):
    count = 0
    while not stop_event.is_set():
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







def main():
    nome = socket.gethostname()
    mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
    n = node_client.node_client(nome, mac)
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    t_connection = threading.Thread(target=wait_for_connection, args=(n,8080))
    t_connection.start()
    

    t_info = threading.Thread(target=wait_for_info, args=(n,8081,stop_event))
    t_info.start()

    recv_thread = threading.Thread(target=udp_receiver, args=(stop_event,))
    play_thread = threading.Thread(target=audio_player, args=(stop_event,))
    recv_thread.start()
    play_thread.start()


    t_connection.join()
    t_info.join()
    recv_thread.join()
    play_thread.join()

if __name__ == "__main__":
    main()