import subprocess
import socket
import threading
import queue
import time

UDP_IP = "255.255.255.255"
UDP_PORT = 5005
CHUNK_SIZE = 1024  # Tamanho do chunk ajustado para corresponder ao receptor

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",
    "-re",
    "-vn",
    "-i", "Playlist/audio.mp3",
    "-acodec", "libmp3lame",
    "-b:a", "64k",
    "-ar", "44100",
    "-ac", "1",
    "-write_xing", "0",  # Desabilita o cabeçalho Xing
    "-f", "mp3",
    "pipe:1"
]
process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)

packet_queue = queue.Queue()

def read_packets():
    while True:
        data = process.stdout.read(CHUNK_SIZE)
        if not data:
            packet_queue.put(None)  # Sinaliza o fim do stream
            break
        packet_queue.put(data)

def send_packets():
    count = 0
    seq = 0  # Variável para número de sequência (8 bits)
    while True:
        data = packet_queue.get()
        if data is None:
            break
        # Prefixar o pacote com o número de sequência e enviar
        packet = bytes([seq]) + data
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        count += len(data)
        print(f"\rEnviado {count} bytes", end="")
        seq = (seq + 1) % 256  # Incrementa e faz wrap a 8 bits
        time_to_sleep = len(data) / (44100 * 2)  # Ajuste fino para sincronização
        time.sleep(time_to_sleep)

reader_thread = threading.Thread(target=read_packets)
sender_thread = threading.Thread(target=send_packets)
reader_thread.start()
sender_thread.start()
reader_thread.join()
sender_thread.join()

process.stdout.close()
process.terminate()
process.wait()
sock.close()
print("\nTransmissão concluída.")