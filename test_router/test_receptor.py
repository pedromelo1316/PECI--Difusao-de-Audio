import os
import re
import socket
import struct
import subprocess
import time
import signal
import sys
import threading
from multiprocessing import Process  # <--- Add this

FREQ = 48000  # Audio sampling frequency
CHUNK_SIZE = 960  # Audio chunk size
SAMPLE_WIDTH = 2  # Bytes per sample (pcm_s16le)
PORT = 12345  # RTP port for multicast audio streaming
OUTPUT_CAPTURE_DIR = "Captures"
RECEPTOR_INTERFACE = "en0"  # Network interface for packet capture
MCAST_GRP = "239.255.0.1"  # Target multicast IP for filtering packets

# Ensure the capture directory exists
os.makedirs(OUTPUT_CAPTURE_DIR, exist_ok=True)


def multicast_capture(test_name):
    capture_file = f"{OUTPUT_CAPTURE_DIR}/{test_name.replace('.sdp', '')}.pcap"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))

    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    with open(capture_file, "wb") as f:  # Open in binary mode
        while True:
            data, addr = sock.recvfrom(2048)  # Increase buffer size for RTP payload

            # Write only the rtp_header to the file
            f.write(data[:12])

            if len(data) >= 12:  # RTP header is at least 12 bytes
                rtp_header = struct.unpack("!BBHII", data[:12])
                sequence_number = rtp_header[2]  # 16-bit sequence number
                print(f"  - Sequence Number (Frame Number): {sequence_number}")

def analyze_packet_loss(file_name):

    capture_file = "Captures/session_c20_f10.pcap"
    print(f"Analyzing packet loss for {capture_file}")

    with open(capture_file, "rb") as f:  # Open in binary mode
        data = f.read()

    # Process the data here to extract sequence numbers or analyze packet loss
    frame_numbers = []

    #has only the header
    for i in range(0, len(data), 12):  # RTP header is 12 bytes
        rtp_header = struct.unpack("!BBHII", data[i:i + 12])
        frame_numbers.append(rtp_header[2])  # Sequence number

    # Sort packet sequence numbers in ascending order
    frame_numbers.sort()

    total_frames = len(frame_numbers)
    lost_frames = 0

    for i in range(1, total_frames):
        diff = frame_numbers[i] - frame_numbers[i - 1]
        if diff > 1:  # There's a gap
            lost_frames += diff - 1

    packet_loss = (lost_frames / total_frames) * 100
    print(f"Total frames: {total_frames}, Lost frames: {lost_frames}, Packet loss: {packet_loss:.2f}%")

    # Write on a file without deleting the previous content

    channel = "20"
    frame_duration = "10"

    with open("statistics.txt", "a") as f:
        f.write(f"c: {channel}, f: {frame_duration}, total_packets: {total_frames}, lost_packets: {lost_frames}, packet_loss: {packet_loss:.2f}%\n")
    
    return packet_loss

def receive_file_name_via_broadcast(port):
    """Receive a file name via UDP broadcast on the specified port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))

    data, addr = s.recvfrom(1024)
    file_name = data.decode("utf-8").strip()
    print(f"Received file name: {file_name}")

    s.sendto(b"ACK", addr)

    return file_name


def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    print("\nCtrl+C detected! Cleaning up...")
    sys.exit(0)

if __name__ == "__main__":
    TCP_PORT = 5000  # UDP broadcast listening port

    current_file_name = None
    cap_process = None

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            # Receive a new file name via broadcast
            file_name = receive_file_name_via_broadcast(TCP_PORT)

            # If a new file name is received, stop the ongoing capture, analyze loss, and start new capture
            if file_name != current_file_name:
                if current_file_name:
                    analyze_packet_loss(current_file_name)  # Analyze packet loss for the old file
                    if cap_process:
                        cap_process.terminate()
                        cap_process.join()

                print(f"Starting new capture for {file_name}")
                cap_process = Process(target=multicast_capture, args=(file_name,))
                cap_process.start()
                current_file_name = file_name

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
