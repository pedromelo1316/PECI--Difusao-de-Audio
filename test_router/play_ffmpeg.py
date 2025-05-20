import socket
import json
import subprocess

BROADCAST_PORT = 5000
BUFFER_SIZE = 1024

def listen_for_test_info():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", BROADCAST_PORT))  # Listen on all interfaces

        print("Listening for broadcast messages...")
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            try:
                message = json.loads(data.decode('utf-8'))
                print(f"Received: {message} from {addr}")
                
                # Send ACK
                sock.sendto(b"ACK", addr)

                return message
            except Exception as e:
                print(f"Error decoding message: {e}")

def play_audio(channel):
    multicast_ip = f"239.255.0.{channel}"
    port = 12345

    cmd = [
        'ffplay',
        '-protocol_whitelist', 'file,rtp,udp',
        '-nodisp',
        '-i', 'Session_files/session',  # Arquivo SDP gerado pelo emissor
        '-af', f'volume={1}'  # Aplica o volume dinamicamente
    ]

    print(f"Starting ffplay for {multicast_ip}:{port}")
    subprocess.run(cmd)

if __name__ == "__main__":
    while True:
        play_audio(1)
