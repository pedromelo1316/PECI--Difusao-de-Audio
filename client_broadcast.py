import socket
import os
from pydub import AudioSegment
from io import BytesIO
import pydub.playback


def udp_client(server_host="192.168.53.109", server_port=8080):
   

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the broadcast address and port
    sock.bind(('', 8080))

    print("Listening for broadcast messages on port 8080...")

    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received message: {data.decode()} from {addr}")

    

if __name__ == '__main__':
    udp_client()
