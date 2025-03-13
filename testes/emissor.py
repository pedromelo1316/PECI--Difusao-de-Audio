import subprocess
import signal
import sys
import socket
import os
import time

source = "default"
BITRATE = "256k"
CHANNELS = "1"

NUM_CHANNELS = 3


def start_ffmpeg(index):
    
    multicast_addresses = f"rtp://239.255.0.{index+1}:12345"
    sdp_filename = f"session{index+1}.sdp"
    
    cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re",
        "-i", f"Playlists/Songs/{index+2}.mp3",
        "-af", "apad",
        "-vn",
        "-c:a", "libopus",
        "-b:a", BITRATE,
        "-f", "rtp",
        "-ac", CHANNELS,
        "-sdp_file", sdp_filename,
        multicast_addresses
    ]
    return subprocess.Popen(cmd)

# Start 3 ffmpeg processes
processes = []
for i in range(NUM_CHANNELS):
    processes.append(start_ffmpeg(i))

def udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.bind(("", 9000))  # Bind to port 9000 for UDP
    print("SDP server listening on port 9000 (UDP)")

    while True:
        try:
            data, addr = server.recvfrom(1024)
            message = data.decode().strip()
            if message.startswith("hello"):
                channel = message.split()[1]
                if channel in ["1", "2", "3"]:
                    sdp_file = f"session{channel}.sdp"
                    with open(sdp_file, "r") as f:
                        content = f.read()
                    server.sendto(content.encode(), addr)
                    print(f"SDP file sent to {addr}")
                else:
                    server.sendto(b"Invalid channel.", addr)
            else:
                server.sendto(b"Invalid request.", addr)
        except Exception as ex:
            print("Error:", ex)

def signal_handler(sig, frame):
    print("Signal received, terminating processes.")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Start the UDP server in the main thread
udp_server()

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
    time.sleep(0.5)
    sys.exit(0)