import subprocess
import socket
import threading
import queue
import time
import struct

MULTICAST_GROUP = "224.1.1.1"
UDP_IP = MULTICAST_GROUP
UDP_PORT = 5005
HELP_PORT = 5006
CHUNK_SIZE = 1024
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

local_queue = queue.Queue()
mic_queue = queue.Queue()



circular_buffer = [None] * 256

def get_local():
    while True:
        data = process_local.stdout.read(CHUNK_SIZE)
        if not data:
            local_queue.put((None, 'local'))
            break
        local_queue.put((data, 'local'))

def get_mic():
    while True:
        data = process_mic.stdout.read(CHUNK_SIZE)
        if not data:
            mic_queue.put((None, 'mic'))
            break
        mic_queue.put((data, 'mic'))



def send_packets():
    seq = 0
    count = 0
    count_packets = 0
    local_data = None
    mic_data = None
    start_time = time.time()
    while True:
        if local_data is None:
            local_data, source = local_queue.get()
            if local_data is None:
                break
            
        if mic_data is None:
            mic_data, source = mic_queue.get()
            if mic_data is None:
                break
        if local_data and mic_data:
            packet = bytes([seq]) + local_data + mic_data
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            count += len(local_data) + len(mic_data)
            count_packets += 1
            t = time.time() - start_time
            start_time = time.time()
            print(f"{count_packets} -> Enviado {count} bytes com {(len(local_data) + len(mic_data))/t} bytes/s", flush=True)
            seq = (seq + 1) % 256
            time_to_sleep = (len(local_data) + len(mic_data)) / (44100 * 2)
            time.sleep(time_to_sleep)
            local_data = None
            mic_data = None



def handle_help_requests():
    help_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    help_sock.bind(('', HELP_PORT))
    while True:
        data, addr = help_sock.recvfrom(1024)
        if data.startswith(b"HELP:"):
            try:
                _, seq = data.decode().split()
                seq = int(seq)
                entry = circular_buffer[seq]
                response = None
                if entry:
                    response = bytes([seq]) + entry
                if response:
                    help_sock.sendto(response, addr)
            except Exception as e:
                print(f"Erro ao processar pedido de ajuda: {e}")





local_thread = threading.Thread(target=get_local)
mic_thread = threading.Thread(target=get_mic)
sender_thread = threading.Thread(target=send_packets)
help_thread = threading.Thread(target=handle_help_requests, daemon=True)

local_thread.start()
mic_thread.start()
sender_thread.start()
help_thread.start()


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