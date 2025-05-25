import json
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


def multicast_capture(dic):
    capture_file = f"{OUTPUT_CAPTURE_DIR}/comb_c{dic["channel"]}_80ms.txt"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))

    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    start_time = None
    with open(capture_file, "wb") as f:  # Open in binary mode
        while True:
            data, addr = sock.recvfrom(2048)  # Increase buffer size for RTP payload

            # Write only the rtp_header to the file
            if data and start_time is None:
                start_time = time.time()

            if start_time and time.time() - start_time > dic["time"]:  # Capture for 60 seconds
                break

            if len(data) >= 12:  # RTP header is at least 12 bytes
                rtp_header = struct.unpack("!BBHII", data[:12])
                sequence_number = rtp_header[2]  # 16-bit sequence number

                print(f"Frame Number: {sequence_number}")
                f.write(f"{sequence_number},".encode("utf-8"))
                

def analyse_packet_loss(dic):

    capture_file = f"{OUTPUT_CAPTURE_DIR}/comb_c{dic["channel"]}_80ms.txt"
    print(f"Analyzing packet loss for {capture_file}")

    if not os.path.exists(capture_file):
        print(f"File {capture_file} does not exist!")
        return

    print(1)
    with open(capture_file, "r") as f:  # Open in binary mode
        frame_numbers = f.read().split(",")  # Split by comma
        frame_numbers = [int(frame) for frame in frame_numbers if frame]  # Convert to integers

    frame_numbers.sort()

    print(2)
    received_frames = len(frame_numbers)
    lost_frames = 0
    sequecial_lost = {}
    print(frame_numbers)
    print(3)
    if len(frame_numbers) > 1:
        for i in range(1, received_frames):
            diff = frame_numbers[i] - frame_numbers[i - 1]
            if diff > 1:  # There's a gap
                lost_frames += diff - 1
                
                if (diff-1) in sequecial_lost:
                    sequecial_lost[diff-1] += 1
                else:
                    sequecial_lost[diff-1] = 1

    print(4)
    packet_loss = (lost_frames / (received_frames+lost_frames)) * 100
    print(f"Received frames: {received_frames}, Lost frames: {lost_frames}, Packet loss: {packet_loss:.2f}%")
    print(5)
    # Write on a file without deleting the previous content

    channel = dic["channel"]

    with open("statistics_80ms.txt", "a") as f:
        f.write(f"c: {channel}, Received_packets: {received_frames}, lost_packets: {lost_frames}, packet_loss: {packet_loss:.2f}%, sequencial_lost: {sequecial_lost}\n")
    
    return packet_loss


def receive_info_via_broadcast(port):
    """Receive a file name via UDP broadcast on the specified port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))

    data, addr = s.recvfrom(1024)
    info_dic = json.loads(data.decode('utf-8'))
    print(f"Received file name: {info_dic}")

    s.sendto(b"ACK", addr)
    s.close()
    return info_dic


def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    print("\nCtrl+C detected! Cleaning up...")
    sys.exit(0)

if __name__ == "__main__":
    TCP_PORT = 5000  # UDP broadcast listening port

    current_info_dic = None
    cap_process = None

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            # Receive a new file name via broadcast
            info_dic = receive_info_via_broadcast(TCP_PORT)

            # If a new file name is received, stop the ongoing capture, analyze loss, and start new capture
            if info_dic != current_info_dic:
                if current_info_dic:
                    analyse_packet_loss(current_info_dic)  # Analyze packet loss for the old file
                    '''
                    if cap_process:
                        cap_process.terminate()
                        cap_process.join()'
                    '''

                print(f"Starting new capture for {info_dic}")

                multicast_capture(info_dic)
                #cap_process = Process(target=multicast_capture, args=(file_name,))
                #cap_process.start()
                current_info_dic = info_dic

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
