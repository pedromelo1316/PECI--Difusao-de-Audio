import socket
import subprocess
import os
import time

def udp_server(host="192.168.53.109", port=8080, url='https://www.youtube.com/watch?v=Wjg6IUL2Pq4'):

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcasting mode
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Define broadcast address and port
    broadcast_address = ('192.168.53.255', 8080)
    message = b'Hello, network!'

    # Send the message
    sock.sendto(message, broadcast_address)
    print("Broadcast message sent on port 8080.")


    

    

if __name__ == '__main__':
    udp_server()