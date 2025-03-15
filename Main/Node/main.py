import socket
import uuid
import threading
import time
import node_client
import json
import pyaudio
import subprocess
import base64
import signal
import sys
import numpy as np

FREQ = 48000
CHUNK_SIZE = 960
SAMPLE_WIDTH = 2  # bytes per sample (pcm_s16le)

OP = 3
HEADER = None
ffmpeg = None
play_thread = None
channel = None

def play_audio(n, sdp_file):
    global ffmpeg, play_thread
    """Plays the RTP audio stream using FFmpeg and pyaudio with dynamic volume control."""
    print("Playing audio stream... from", sdp_file)
    ffmpeg_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-protocol_whitelist", "file,rtp,udp",
        "-i", sdp_file,
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-"
    ]
    ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
    p = pyaudio.PyAudio()
    # Assuming a stereo stream; adjust channels if needed.
    stream = p.open(format=p.get_format_from_width(SAMPLE_WIDTH), channels=2, rate=FREQ, output=True)
    
    try:
        # Calculate bytes to read per chunk (CHUNK_SIZE samples per channel x channels)
        bytes_per_chunk = CHUNK_SIZE * SAMPLE_WIDTH * 1  # 2 channels
        while True:
            chunk = ffmpeg.stdout.read(bytes_per_chunk)
            if not chunk:
                break
            # Convert raw bytes to numpy array of int16 samples
            audio_data = np.frombuffer(chunk, dtype=np.int16)
            # Get the current volume from the node (default to 1.0 if not set)
            volume = n.getVolume() if n.getVolume() is not None else 1.0
            # Multiply samples by volume factor (with clipping to avoid overflow)
            audio_data = np.clip(audio_data * volume, -32768, 32767).astype(np.int16)
            stream.write(audio_data.tobytes())
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Terminating playback...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        ffmpeg.terminate()

def wait_for_info(n, port=8081, stop_event=None):
    global ffmpeg, HEADER, OP, channel, play_thread
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        while not stop_event.is_set():
            data, addr = server_socket.recvfrom(4096)
            data = data.decode('utf-8')
            try:
                dic = json.loads(data)
                if n.mac in dic.keys():
                    info = dic[n.mac]
                    print("Received info:", info)

                    if "removed" in info.keys():
                        print("Node removed")
                        if play_thread is not None:
                            ffmpeg.terminate()
                            play_thread.join()
                            print("FFmpeg process terminated.")
                        stop_event.set()
                        break

                    channel = info["channel"] if info["channel"] is not None else None
                    volume = info["volume"] if info["volume"] is not None else None
                    new_HEADER = info["header"] if info["header"] is not None else None
                    
                    if volume is not None and n.getVolume() != volume:
                        n.setVolume(float(volume))
                    if (new_HEADER is not None and HEADER != new_HEADER) or (channel is not None and channel != n.getChannel()):
                        HEADER = new_HEADER 
                        with open("session_received.sdp", "w") as f:
                            f.write(HEADER)
                        n.setChannel(channel)
                            
                        if play_thread is None:
                            play_thread = threading.Thread(target=play_audio, args=(n, "session_received.sdp",))
                            play_thread.start()
                            print("FFmpeg process started.")
                        else:
                            # Terminate and restart playback for updated stream
                            ffmpeg.terminate()
                            play_thread.join()
                            play_thread = threading.Thread(target=play_audio, args=(n, "session_received.sdp",))
                            play_thread.start()
                            print("FFmpeg process restarted.")
                            
                    if channel is None or HEADER is None:
                        if play_thread is not None:
                            ffmpeg.terminate()
                            play_thread.join()
                            play_thread = None
                            print("FFmpeg process terminated due to missing channel/header.")

                    print("Channel:", n.getChannel())
                    print("Volume:", n.getVolume())

            except ValueError as e:
                print("Error in wait_for_info:", e)

    server_socket.close()

def wait_for_connection(n, port=8080, stop_event=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.settimeout(5)
        while not stop_event.is_set():
            msg = f"{n.getName()},{n.getMac()}"
            client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', port))
            print("Sent information to manager")
            try:
                data, addr = client_socket.recvfrom(1024)
                if data == b"OK":
                    n.setHostIp(addr[0])
                    print("Connection established")
                    break
                else:
                    print("Connection refused")
                    time.sleep(5)
                    continue
            except:
                print("Connection refused")
                time.sleep(1)
        client_socket.close()
        return True

def main():
    global play_thread, ffmpeg, HEADER, OP, channel
    nome = socket.gethostname()
    mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
    n = node_client.node_client(nome, mac)
    stop_event = threading.Event()

    t_connection = threading.Thread(target=wait_for_connection, args=(n,8080, stop_event))
    t_connection.start()    
    t_info = threading.Thread(target=wait_for_info, args=(n,8081, stop_event))
    t_info.start()

    t_connection.join()
    t_info.join()
    
    if play_thread is not None:
        play_thread.join()
        
    if ffmpeg is not None:
        ffmpeg.terminate()
        
    print("Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    main()