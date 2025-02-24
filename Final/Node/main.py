import socket
import uuid
import threading
import time
import node_client
import queue




def wait_for_connection(n, port=8080):
    while True:
        msg = f"{n.getName()},{n.getMac()}"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.settimeout(5)
            client_socket.sendto(msg.encode('utf-8'), ('localhost', port))
            print("Sent information to manager")

            try:
                data, addr = client_socket.recvfrom(1024)
                if data == b"OK":
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

    wait_for_connection(n)


if __name__ == "__main__":
    main()