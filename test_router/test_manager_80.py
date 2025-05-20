import json
import os
import re
import subprocess
import time
import socket

# Configurações de áudio
BITRATE = "128k"
SAMPLE_RATE = "48000"
AUDIO_CHANNELS = "1"  # Will change dynamically in the loop
FRAME_DURATIONS = [80]  # Frame durations
NUM_CHANNELS_LIST = [100]  # Number of channels

source = "default"
BROADCAST_IP = "255.255.255.255"  # Replace with the target IP address
PORT = 5000           # Replace with the target port

TIME_PER_COMB = 60*5
TIME_SLEEP = 10

list_of_combinations_file = []

def send_info_via_broadcast(info, ip, port, channel, frame_duration):
    """Send a file name via UDP broadcast."""
    if (channel, frame_duration) in list_of_combinations_file:
        return
    if channel in NUM_CHANNELS_LIST and frame_duration in FRAME_DURATIONS:
        list_of_combinations_file.append((channel, frame_duration))
    else:
        
        return
    
    data = json.dumps(info)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2)  # Set a timeout for receiving ACK
        while True:
            try:
                s.sendto(data.encode('utf-8'), (ip, port))
                print(f"Sent file name: {info}")
                # Wait for ACK
                data, addr = s.recvfrom(1024)
                if data.decode('utf-8') == "ACK":
                    print(f"Received ACK from {addr}")
                    break
            except socket.timeout:
                print("No ACK received, resending...")

    


def start_ffmpeg_process(channel, frame_duration):
    multicast_address = f"rtp://239.255.0.{channel}:12345?pkt_size=5000"
    playlist_path = f"Playlists/{source}.txt"
    
    if not os.path.exists(playlist_path):
        print(f"Playlist {playlist_path} not found")
        return None

    if not os.path.exists("Session_files"):
        os.makedirs("Session_files")
    
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        # "-report",  # Removed to ensure logs are written to the specified file
        "-f", "concat",
        "-safe", "0",
        "-re",
        "-i", playlist_path,
        "-af", "apad",
        "-ar", SAMPLE_RATE,
        "-vn",
        "-acodec", "libopus",
        "-b:a", BITRATE,
        "-ac", AUDIO_CHANNELS,
        "-f", "rtp",
        "-frame_duration", str(frame_duration),
        "-sdp_file", "Session_files/session",
        multicast_address
    ]
    
    process = subprocess.Popen(cmd)
    # Send the SDP file via TCP after it is created
    time.sleep(1)  # Wait for the file to be created
    return process


def run_test(frame_duration, num_channels):
    processes = []
    print(f"Running test for {num_channels} channels and frame duration {frame_duration} ms")
    info_dic = {"channel": str(num_channels), "frame_duration": str(frame_duration), "time": TIME_PER_COMB}
    send_info_via_broadcast(info_dic, BROADCAST_IP, PORT, num_channels, frame_duration)

    time.sleep(TIME_SLEEP)
    # Start ffmpeg for each channel
    for channel in range(1, num_channels + 1):
        process = start_ffmpeg_process(channel, frame_duration)
        if process:
            processes.append(process)

    # Wait for the test to run (1 minute)
    time.sleep(TIME_PER_COMB)

    for process in processes:
        process.kill()  # No waiting, no warning

    print(f"Test with Frame Duration {frame_duration} ms and {num_channels} channels completed\n")

if __name__ == "__main__":
    for frame_duration in FRAME_DURATIONS:
        for num_channels in NUM_CHANNELS_LIST:
            run_test(frame_duration, num_channels)
