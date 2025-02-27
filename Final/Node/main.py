import socket
import uuid
import threading
import time
import node_client
import queue
import json


def wait_for_info(n, port=8081, stop_event=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        while True:
            data, addr = server_socket.recvfrom(1024)
            data = data.decode('utf-8')
            print("Recebido de", addr, ":", data)
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


def wait_for_connection(n, port=8080, stop_event=None):
    while True:
        msg = f"{n.getName()},{n.getMac()}"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.settimeout(5)
            client_socket.sendto(msg.encode('utf-8'), ('localhost', port))
            print("Sent information to manager")

            try:
                data, addr = client_socket.recvfrom(1024)
                data = data.decode('utf-8')
                print("Received from manager:", data)
                if data == b"OK":
                    n.setHostIp(addr[0])
                    print("Connection established")
                    break
                else:
                    print("Connection refused")
                    time.sleep(5)
                    continue
            except socket.timeout:
                print("Timed out, retrying...")
                continue
    return True




def main():
    nome = socket.gethostname()
    mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
    n = node_client.node_client(nome, mac)
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    t_connection = threading.Thread(target=wait_for_connection, args=(n,8080,stop_event))
    t_connection.start()

    t_info = threading.Thread(target=wait_for_info, args=(n,8081,stop_event))
    t_info.start()


if __name__ == "__main__":
    main()