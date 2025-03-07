import subprocess
import socket
import threading
import queue
import time
import struct
import os

MULTICAST_GROUP = "224.1.1.1"
UDP_IP = MULTICAST_GROUP
UDP_PORT = 5005
CONTROL_PORT = 5006
CHUNK_SIZE = 960  # Tamanho de chunk recomendado para Opus (20 ms de áudio)
PACKET_SIZE = 2 * CHUNK_SIZE
FREQ = "48000"
QUAL = "16k"

HEADER_SIZE = 256

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ttl = 1
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl))

# Canal de controle para novos recetores
control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
control_sock.bind(("0.0.0.0", CONTROL_PORT))

LOCAL_HEADER = b""
MIC_HEADER = b""

NOS = []

# Thread para detetar novos recetores e enviar cabeçalho + metadados
def handle_new_receivers():
    while True:
        data, addr = control_sock.recvfrom(1024)
        if data == b"connect":
            print(f"Novo recetor detectado: {addr}")
            NOS.append(addr)
            send_header("local", addr)
            send_header("mic", addr)

            print(f"Enviando cabeçalho para {addr}")


def send_header(source, ip=None):
    if source == 'local':
        header = bytes([1])+bytes([2+0]) + LOCAL_HEADER
    elif source == 'mic':
        header = bytes([1])+bytes([2+1]) + MIC_HEADER
    else:
        return
    
    if ip:
        sock.sendto(header, (ip[0], UDP_PORT))
    else:
        for ip in NOS:
            sock.sendto(header, (ip[0], UDP_PORT))

threading.Thread(target=handle_new_receivers, daemon=True).start()

# Configura o stdout dos processos FFmpeg para ser não bufferizado
def start_ffmpeg_process(input_file, is_mic=False):
    if is_mic:
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-f", "alsa", "-i", "default",
            "-acodec", "libopus",
            "-b:a", QUAL,
            "-ar", FREQ,
            "-ac", "1",
            "-f", "ogg",
            "pipe:1"
        ]
    else:
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
            "-f", "concat",          # Adicione esta linha
            "-safe", "0",            # Permite caminhos absolutos/relativos
            "-re",
            "-i", input_file,
            "-vn",

            
            "-acodec", "libopus",
            "-b:a", QUAL,
            "-ar", FREQ,
            "-ac", "1",
            "-f", "ogg",
            "pipe:1"
        ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=int(CHUNK_SIZE/2))
    return process

local_queue = queue.Queue()
mic_queue = queue.Queue()

# Função atualizada para percorrer os arquivos na pasta Playlist
def get_local():
    global LOCAL_HEADER

    print(f"\nReproduzindo: {"Playlists/default.txt"}")
    process = start_ffmpeg_process("Playlists/default.txt")
    # Lê o cabeçalho para o arquivo atual
    LOCAL_HEADER = process.stdout.read(HEADER_SIZE)
    print("Enviando cabeçalho para novos recetores")
    send_header("local")
    while True:
        try:
            data = process.stdout.read(CHUNK_SIZE)
            if not data:
                break
            local_queue.put((data, 'local'))
        except Exception as e:
            print(f"Erro na leitura local do arquivo {"Playlists/default.txt"}: {e}")
            break
    process.stdout.close()
    process.terminate()
    process.wait()

def get_mic():
    global MIC_HEADER
    process_mic = start_ffmpeg_process(None, is_mic=True)
    MIC_HEADER = process_mic.stdout.read(HEADER_SIZE)
    while True:
        try:
            data = process_mic.stdout.read(CHUNK_SIZE)
            if not data:
                mic_queue.put((None, 'mic'))
                break
            mic_queue.put((data, 'mic'))
        except Exception as e:
            print(f"Erro na leitura mic: {e}")
            break
    process_mic.stdout.close()
    process_mic.terminate()
    process_mic.wait()

def send_packets():

    local_data = None
    mic_data = None
    seq_local = 0
    seq_mic = 0
    count = 0
    start_time = time.time()

    while True:
        if local_data is None:
            try:
                local_data, _ = local_queue.get(timeout=0.05)
            except Exception:
                pass

        if mic_data is None:
            try:
                mic_data, _ = mic_queue.get(timeout=0.05)
            except Exception:
                pass

        if local_data is not None:
            if local_data is None:
                break
            sock.sendto(bytes([seq_local]) + bytes([0]) + local_data, (UDP_IP, UDP_PORT))
            #print(f"Enviando pacote {seq_local} de áudio local")
            seq_local = (seq_local + 1) % 256
            count += len(local_data)
            local_data = None

        if mic_data is not None:
            if mic_data is None:
                break
            sock.sendto(bytes([seq_mic]) + bytes([1]) + mic_data, (UDP_IP, UDP_PORT))
            #print(f"Enviando pacote {seq_mic} de áudio do microfone")
            seq_mic = (seq_mic + 1) % 256
            count += len(mic_data)
            mic_data = None

        print(f"\rEnviados {count} bytes, velocidade: {count/(time.time()-start_time):.2f} B/s")

local_thread = threading.Thread(target=get_local, daemon=True)
mic_thread = threading.Thread(target=get_mic, daemon=True)
sender_thread = threading.Thread(target=send_packets)

local_thread.start()
mic_thread.start()
sender_thread.start()

local_thread.join()
mic_thread.join()
sender_thread.join()

sock.close()
print("\nTransmissão concluída.")