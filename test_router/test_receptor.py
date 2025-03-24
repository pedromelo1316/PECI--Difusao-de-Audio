import os
import socket
import subprocess
import time
import signal
import sys

FREQ = 48000  # Frequência de amostragem do áudio
CHUNK_SIZE = 960  # Tamanho do bloco de áudio a ser lido do stream
SAMPLE_WIDTH = 2  # Bytes por amostra (pcm_s16le)
OUTPUT_CAPTURE_DIR = "Captures"
RECEPTOR_INTERFACE = "en0"  # Interface de rede para captura de pacotes

# Ensure the capture directory exists
if not os.path.exists(OUTPUT_CAPTURE_DIR):
    os.makedirs(OUTPUT_CAPTURE_DIR)

def start_tshark_capture(test_name):
    """Start a tshark capture for the given test name."""
    capture_file = f"{OUTPUT_CAPTURE_DIR}/{test_name.replace('.sdp', '')}.pcap"
    print(f"Starting packet capture: {capture_file}")
    
    # Define the multicast IP address to filter by
    multicast_ip = "239.255.0.1"
    
    # Build the tshark command with a filter for UDP packets sent to the multicast IP
    cmd = [
        "tshark",
        "-i", RECEPTOR_INTERFACE,  # Interface to capture packets
        "-f", f"udp and dst host {multicast_ip}",  # Filter for UDP packets sent to the multicast IP
        "-w", capture_file,  # Output capture file
        "-c", "1000000"  # Capture a large number of packets
    ]
    
    return subprocess.Popen(cmd)

def analyze_packet_loss(test_name):
    capture_file = f"{OUTPUT_CAPTURE_DIR}/{test_name.replace('.sdp', '')}.pcap"
    
    base_name = test_name.replace("session_c", "").replace(".sdp", "")
    parts = base_name.split("_f")
    channel = int(parts[0])
    frame_duration = int(parts[1])

    multicast_ip = "239.255.0.1"

    # Extract RTP sequence numbers from the capture file using tshark
    cmd_sequence = f"tshark -r {capture_file} -Y 'ip.dst == {multicast_ip} and rtp' -T fields -e rtp.seq"
    result_sequence = subprocess.run(cmd_sequence, shell=True, capture_output=True, text=True)
    
    sequence_numbers = result_sequence.stdout.strip().split("\n")
    sequence_numbers = [int(num) for num in sequence_numbers if num.isdigit()]

    # Detect packet loss by looking for gaps in sequence numbers
    lost_packets = 0
    for i in range(1, len(sequence_numbers)):
        if sequence_numbers[i] != sequence_numbers[i - 1] + 1:
            lost_packets += sequence_numbers[i] - sequence_numbers[i - 1] - 1

    print(f"Detected packet loss: {lost_packets} packets")
    
    # Get the total data received (sum of frame lengths)
    cmd_size = f"tshark -r {capture_file} -Y 'ip.dst == {multicast_ip}' -T fields -e frame.len"
    result_size = subprocess.run(cmd_size, shell=True, capture_output=True, text=True)
    
    frame_sizes = result_size.stdout.strip().split("\n")
    total_data_received = sum(int(size) for size in frame_sizes if size.isdigit())  # Sum frame sizes

    print(f"Total Data Received: {total_data_received / 1024:.2f} KB")
    
    return total_data_received

def receive_file_name_via_tcp(ip, port):
    """Receive a file name via TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ip, port))
        s.listen(1)
        print(f"Listening for incoming connections on {ip}:{port}...")
        conn, addr = s.accept()
        with conn:
            print(f"Connection established with {addr}")
            file_name = conn.recv(1024).decode('utf-8')
            print(f"Received file name: {file_name}")
            return file_name

def cleanup(capture_process):
    """Terminate the capture process if running."""
    if capture_process:
        print("Stopping capture process...")
        capture_process.terminate()
        capture_process.wait()
        print("Capture process terminated.")

if __name__ == "__main__":
    TCP_IP = "127.0.0.1"  # Replace with the receiver's IP address
    TCP_PORT = 5000  # Replace with the receiver's TCP port

    current_file_name = None
    capture_process = None

    def signal_handler(sig, frame):
        """Handle Ctrl+C signal."""
        print("\nCtrl+C detected! Cleaning up...")
        cleanup(capture_process)
        sys.exit(0)

    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            # Listen for a new file name from the emitter
            file_name = receive_file_name_via_tcp(TCP_IP, TCP_PORT)

            # If a new file name is received, start or stop capturing
            if file_name != current_file_name:
                if current_file_name:
                    # If capture is ongoing, stop the previous capture and analyze
                    cleanup(capture_process)
                    analyze_packet_loss(current_file_name)

                # Start new packet capture
                print(f"Starting new capture for {file_name}")
                capture_process = start_tshark_capture(file_name)
                current_file_name = file_name

            # Sleep or wait for a short time before checking for the next file name
            time.sleep(2)
        except Exception as e:
            print(f"An error occurred: {e}")
            cleanup(capture_process)
            sys.exit(1)
