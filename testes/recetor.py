import subprocess
import signal
import sys
import socket
import time

PORT = 9000  # SDP server port

def request_sdp(channel):
    """Requests the SDP file from the server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.settimeout(5)

    request_message = f"hello {channel}"

    for _ in range(5):  # Retry 5 times if no response
        client_socket.sendto(request_message.encode(), ('<broadcast>', PORT))
        print(f"Requesting SDP for channel {channel}...")

        try:
            data, addr = client_socket.recvfrom(4096)
            sdp_content = data.decode()
            with open("session_received.sdp", "w") as f:
                f.write(sdp_content)
            print(f"SDP received from {addr}")
            return "session_received.sdp"
        except socket.timeout:
            print("No response from server, retrying...")
    
    print("Failed to obtain SDP.")
    sys.exit(1)

def play_audio(sdp_file):
    """Plays the RTP audio stream using FFmpeg."""
    print("Playing audio stream... from", sdp_file)
    ffmpeg_cmd = [
        "ffmpeg",
        "-protocol_whitelist", "file,rtp,udp",
        "-i", sdp_file,
        "-c:a", "pcm_s16le",
        "-f", "wav",
        "pipe:1"
    ]

    player_cmd = [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-"
    ]

    def signal_handler(sig, frame):
        print('Ctrl+C pressed, terminating processes...')
        ffmpeg.terminate()
        player.terminate()
        time.sleep(0.5)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
    player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

    try:
        player.communicate()
    except KeyboardInterrupt:
        signal_handler(None, None)

def main():
    channel = input("Choose channel (1, 2, or 3): ").strip()
    if channel not in ["1", "2", "3"]:
        print("Invalid channel!")
        sys.exit(1)

    sdp_file = request_sdp(channel)
    play_audio(sdp_file)

if __name__ == "__main__":
    main()
