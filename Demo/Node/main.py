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
import struct


MCAST_GRP = "224.1.1.1"
MCAST_PORT = 8082

MULTIPLICADOR = 10   # Ajuste conforme necessário max 65

FREQ = 48000
CHUNCK_SIZE = 960

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
sock.bind(("", MCAST_PORT))

mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

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
                         frames_per_buffer=CHUNCK_SIZE*MULTIPLICADOR)

# Comando ffmpeg para decodificar Opus
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
process = None
count = 0
last_seq = None  # Variável global para o último número de sequência
channel = None



def wait_for_info(n, port=8081, stop_event=None):
    global process, HEADER, OP, channel
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        while not stop_event.is_set():
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
                    _HEADER = base64.b64decode(_HEADER) if _HEADER is not None else None
                    n.setChannel(channel)
                    n.setVolume(volume)
                    if _HEADER != HEADER:
                        HEADER = _HEADER
                        print("Header:", _HEADER)
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

    server_socket.close()


def wait_for_connection(n, port=8080, stop_event=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.settimeout(5)
        while not stop_event.is_set():
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
        client_socket.close()
        return True
    
    



def udp_receiver(stop_event = None):
    global last_seq, process

    try:
        while not stop_event.is_set():
            # Receber dados Opus via UDP
            packet, addr = sock.recvfrom(CHUNCK_SIZE*MULTIPLICADOR + 2)  # Tamanho máximo de um pacote UDP


            if not process:
                continue

            # Desempacotar os 4 primeiros bytes para obter o canal
            packet_channel = packet[0]

            if channel != packet_channel:
                continue

            seq = packet[1]

            print(f"Recebido: {seq}")

            if last_seq is not None and seq != (last_seq + 1) % 256:
                print(f"Esperado: {last_seq + 1}, recebido: {seq}")
            last_seq = seq

            opus_data = packet[2:]
            
            # Enviar dados para o ffmpeg decodificar e reproduzir
            if process.poll() is not None:
                print("ffmpeg terminou")
                break
            process.stdin.write(opus_data)
            
    except KeyboardInterrupt:
        print("Recepção interrompida.")
    finally:
        process.terminate()
        stop_event.set()

def ffmpeg_reader(stop_event = None):
    global process
    while not stop_event.is_set():
        if process:
            data = process.stdout.read(CHUNCK_SIZE*MULTIPLICADOR)
                
            if not data:
                break

            stream.write(data)

    stream.stop_stream()
    stream.close()





def main():
    nome = socket.gethostname()
    mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
    n = node_client.node_client(nome, mac)
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    t_connection = threading.Thread(target=wait_for_connection, args=(n,8080, stop_event))
    t_connection.start()
    

    t_info = threading.Thread(target=wait_for_info, args=(n,8081,stop_event))
    t_info.start()

    recv_thread = threading.Thread(target=udp_receiver, args=(stop_event,))
    play_thread = threading.Thread(target=ffmpeg_reader, args=(stop_event,))
    recv_thread.start()
    play_thread.start()


    t_connection.join()
    t_info.join()
    recv_thread.join()
    play_thread.join()

if __name__ == "__main__":
    main()