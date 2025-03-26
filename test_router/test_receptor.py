import os
import re
import socket
import subprocess
import time
import signal
import sys
import threading

FREQ = 48000  # Audio sampling frequency
CHUNK_SIZE = 960  # Audio chunk size
SAMPLE_WIDTH = 2  # Bytes per sample (pcm_s16le)
OUTPUT_CAPTURE_DIR = "Captures"
#RECEPTOR_INTERFACE = "en0"  # Network interface for packet capture
MULTICAST_IP = "239.255.0.1"  # Target multicast IP for filtering packets

# Ensure the capture directory exists
os.makedirs(OUTPUT_CAPTURE_DIR, exist_ok=True)

def get_wifi_interface():
    """Automatically detect the Wi-Fi network interface."""
    try:
        result = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True)
        interfaces = result.stdout.split("\n")
        wifi_interface = None
        for i, line in enumerate(interfaces):
            if "Wi-Fi" in line:
                wifi_interface = interfaces[i + 1].split(":")[1].strip()
                break
        return wifi_interface
    except Exception as e:
        print(f"Error detecting Wi-Fi interface: {e}")
        return None

# Auto-detect Wi-Fi interface
RECEPTOR_INTERFACE = get_wifi_interface()


def start_tshark_capture(test_name):
    """Start a tshark capture and enforce a 60-second limit from first packet detection."""
    capture_file = f"{OUTPUT_CAPTURE_DIR}/{test_name.replace('.sdp', '')}.pcap"
    print(f"Starting packet capture: {capture_file}")

    cmd = [
        "tshark",
        "-i", RECEPTOR_INTERFACE,
        "-f", f"udp and dst host {MULTICAST_IP}",
        "-T", "fields",
        "-e", "frame.number"
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    def read_output():
        with open(capture_file, "w") as f:
            for line in process.stdout:
                frame_number = line.strip()
                f.write(frame_number + ",")

    threading.Thread(target=read_output, daemon=True).start()

    return process


def analyze_packet_loss(file_name):
    """Analyse packet loss from the captured packets."""
    capture_file = f"{OUTPUT_CAPTURE_DIR}/{file_name.replace('.sdp', '')}.pcap"
    print(f"Analyzing packet loss for {capture_file}")

    with open(capture_file, "r") as f:
        frame_numbers = f.read().strip().split(",")
        frame_numbers = [int(x) for x in frame_numbers if x]

    total_frames = len(frame_numbers)
    lost_frames = 0

    for i in range(1, total_frames):
        if frame_numbers[i] != frame_numbers[i - 1] + 1:
            lost_frames += frame_numbers[i] - frame_numbers[i - 1] - 1

    packet_loss = (lost_frames / total_frames) * 100
    print(f"Total frames: {total_frames}, Lost frames: {lost_frames}, Packet loss: {packet_loss:.2f}%")

    #write on a file without deleting the previous content
    split = re.split(r'_|\.', file_name)
    channel = split[1][1:]
    frame_duration = split[2][1:]

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

def cleanup(capture_process):
    """Ensure the capture process stops immediately after the test duration."""
    if capture_process and capture_process.poll() is None:
        print("Stopping capture process...")
        capture_process.terminate()
        try:
            capture_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            capture_process.kill()
        print("Capture process terminated.")

if __name__ == "__main__":
    TCP_PORT = 5000  # UDP broadcast listening port

    current_file_name = None
    capture_process = None

    def signal_handler(sig, frame):
        """Handle Ctrl+C signal."""
        print("\nCtrl+C detected! Cleaning up...")
        cleanup(capture_process)
        sys.exit(0)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            file_name = receive_file_name_via_broadcast(TCP_PORT)

            if file_name != current_file_name:
                if current_file_name:
                    cleanup(capture_process)
                    analyze_packet_loss(current_file_name)

                print(f"Starting new capture for {file_name}")
                capture_process = start_tshark_capture(file_name)
                current_file_name = file_name

        except Exception as e:
            print(f"Error: {e}")
            cleanup(capture_process)
            sys.exit(1)
