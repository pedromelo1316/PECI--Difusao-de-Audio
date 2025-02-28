import subprocess
import socket
import threading
import queue
import time
import struct

MULTICAST_GROUP = "224.1.1.1"
UDP_IP = MULTICAST_GROUP
UDP_PORT = 5005
CHUNK_SIZE = 8192
PACKET_SIZE = 2 * CHUNK_SIZE

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ttl = 1
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl))

# Comando ffmpeg para capturar áudio local
ffmpeg_local_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-re",
    "-vn",
    "-i", "Playlist/audio.mp3",
    "-acodec", "libmp3lame",
    "-b:a", "64k",
    "-ar", "44100",
    "-ac", "1",
    "-write_xing", "0",
    "-f", "mp3",
    "pipe:1"
]
process_local = subprocess.Popen(ffmpeg_local_cmd, stdout=subprocess.PIPE)

# Comando ffmpeg para capturar áudio do microfone
ffmpeg_mic_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-f", "alsa", "-i", "default",
    "-acodec", "libmp3lame",
    "-b:a", "64k",
    "-ar", "44100",
    "-ac", "1",
    "-f", "mp3",
    "pipe:1"
]
process_mic = subprocess.Popen(ffmpeg_mic_cmd, stdout=subprocess.PIPE)

packet_queue = queue.Queue()

def get_local():
    while True:
        data = process_local.stdout.read(CHUNK_SIZE)
        if not data:
            packet_queue.put((None, 'local'))
            break
        packet_queue.put((data, 'local'))

def get_mic():
    while True:
        data = process_mic.stdout.read(CHUNK_SIZE)
        if not data:
            packet_queue.put((None, 'mic'))
            break
        packet_queue.put((data, 'mic'))

def send_packets():
    count = 0
    seq = 0
    local_data = None
    mic_data = None
    while True:
        if local_data is None:
            local_data, source = packet_queue.get()
            if local_data is None:
                break
        if mic_data is None:
            mic_data, source = packet_queue.get()
            if mic_data is None:
                break
        if local_data and mic_data:
            packet = bytes([seq]) + local_data + mic_data
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            count += len(local_data) + len(mic_data)
            print(f"\rEnviado {count} bytes", end="")
            seq = (seq + 1) % 256
            time_to_sleep = (len(local_data) + len(mic_data)) / (44100 * 2)
            time.sleep(time_to_sleep)
            local_data = None
            mic_data = None

local_thread = threading.Thread(target=get_local)
mic_thread = threading.Thread(target=get_mic)
sender_thread = threading.Thread(target=send_packets)
local_thread.start()
mic_thread.start()
sender_thread.start()
local_thread.join()
mic_thread.join()
sender_thread.join()

process_local.stdout.close()
process_local.terminate()
process_local.wait()
process_mic.stdout.close()
process_mic.terminate()
process_mic.wait()
sock.close()
print("\nTransmissão concluída.")