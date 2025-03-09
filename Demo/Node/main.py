import socket
import uuid
import threading
import time
import node_client
import queue
import json
import pyaudio
import subprocess
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

channel = None



def wait_for_info(n, port=8081, stop_event=None):
    global process, HEADER, OP, channel
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
                    n.setChannel(channel)
                    n.setVolume(volume)

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
    global last_seq

    # Configura o socket multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MCAST_PORT))
    mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    last_seq = None
    while not stop_event.is_set():
        try:
            while not stop_event.is_set():
                data, _ = sock.recvfrom(4096)  # buffer maior para o byte extra
                if data:
                    # Extrair o número de sequência (primeiro byte) e o dado real

                    _channel = data[0]
                    packet_seq = data[1]


                    if _channel != channel:
                        continue

                    print(f"Recebido pacote {packet_seq} de {_channel}")

                    opus_frame = data[2:]

                    if last_seq is None:
                        last_seq = packet_seq
                    elif packet_seq != (last_seq + 1) % 256:
                        print(f"Pacote perdido: {last_seq} -> {packet_seq}")

                    last_seq = packet_seq

                    pcm_frame = decoder.decode(opus_frame, FRAME_SIZE)

                    stream.write(pcm_frame)
                    
        except Exception as e:
            print(f"\nErro na recepção: {e}")
            break

        except KeyboardInterrupt:
            print("Recepção interrompida.")
            break

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            sock.close()









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

    t_connection.join()
    recv_thread = threading.Thread(target=udp_receiver, args=(stop_event,))
    recv_thread.start()
    
    t_info.join()
    recv_thread.join()

if __name__ == "__main__":
    main()