import os
import re
import subprocess
import time
import socket

# Configurações de áudio
BITRATE = "128k"
SAMPLE_RATE = "48000"
AUDIO_CHANNELS = "1"  # Will change dynamically in the loop
FRAME_DURATIONS = [10, 20, 40, 60, 80, 100, 120]  # Frame durations
NUM_CHANNELS_LIST = [1, 5, 10, 20, 50, 100]  # Number of channels

source = "default"
TCP_IP = "127.0.0.1"  # Replace with the target IP address
TCP_PORT = 5000           # Replace with the target port

list_of_combinations_file = []

def send_file_name_via_tcp(file_path, ip, port, channel, frame_duration):

    if (channel, frame_duration) in list_of_combinations_file:
        return
    if channel in NUM_CHANNELS_LIST and frame_duration in FRAME_DURATIONS:
        list_of_combinations_file.append((channel, frame_duration))
    else:
        return

    """Send the content of a file to a specific IP address via TCP."""
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((ip, port))
            file_name = os.path.basename(file_path)
            s.sendall(file_name.encode('utf-8'))
            print(f"Sent file name {file_name} to {ip}:{port}")
        except Exception as e:
            print(f"Failed to send file name {file_name} to {ip}:{port}: {e}")



def start_ffmpeg_process(channel, frame_duration):
    multicast_address = f"rtp://239.255.0.{channel}:12345?pkt_size=5000"
    playlist_path = f"Playlists/{source}.txt"
    
    if not os.path.exists(playlist_path):
        print(f"Playlist {playlist_path} not found")
        return None

    if not os.path.exists("Session_files"):
        os.makedirs("Session_files")


    sdp_file = f"Session_files/session_c{channel}_f{frame_duration}.sdp"
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
        "-sdp_file", sdp_file,
        multicast_address
    ]
    
    process = subprocess.Popen(cmd)
    # Send the SDP file via TCP after it is created
    time.sleep(1)  # Wait for the file to be created
    return process


def run_test(frame_duration, num_channels):
    processes = []
    print(f"Running test for {num_channels} channels and frame duration {frame_duration} ms")
    sdp_file = f"Session_files/session_c{num_channels}_f{frame_duration}.sdp"
    send_file_name_via_tcp(sdp_file, TCP_IP, TCP_PORT, num_channels, frame_duration)

    time.sleep(10)
    # Start ffmpeg for each channel
    for channel in range(1, num_channels + 1):
        process = start_ffmpeg_process(channel, frame_duration)
        if process:
            processes.append(process)

    # Wait for the test to run (1 minute)
    time.sleep(60)

    # Stop the processes and count packets
    for process in processes:
        process.terminate()

    print(f"Test with Frame Duration {frame_duration} ms and {num_channels} channels completed")

if __name__ == "__main__":
    for frame_duration in FRAME_DURATIONS:
        for num_channels in NUM_CHANNELS_LIST:
            run_test(frame_duration, num_channels)
