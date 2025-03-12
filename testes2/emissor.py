import subprocess
import signal
import sys
import threading
import socket

source = "default"
BITRATE = "128k"
CHANNELS = "2"

multicast_addresses = ["rtp://239.255.0.1:12345", "rtp://239.255.0.2:12345", "rtp://239.255.0.3:12345"]
sdp_files = ["session1.sdp", "session2.sdp", "session3.sdp"]

def start_ffmpeg(index, addr, sdp_filename):
    cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re",
        #"-f", "concat",
        #"-safe", "0",
        "-i", f"Playlists/Songs/{index+2}.mp3",
        "-af", "apad",
        "-vn",
        "-c:a", "libopus",
        "-b:a", BITRATE,
        "-f", "rtp",
        "-ac", CHANNELS,
        "-sdp_file", sdp_filename,
        addr
    ]
    return subprocess.Popen(cmd)

# Inicia 3 processos ffmpeg
processes = []
for i in range(3):
    processes.append(start_ffmpeg(i, multicast_addresses[i], sdp_files[i]))

def socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", 9000))
    server.listen(1)
    print("Servidor SDP do emissor escutando na porta 9000")
    while True:
        conn, addr = server.accept()
        try:
            data = conn.recv(1024).decode().strip()
            if data in ["1", "2", "3"]:
                idx = int(data)-1
                with open(sdp_files[idx], "r") as f:
                    content = f.read()
                conn.sendall(content.encode())
            else:
                conn.sendall(b"Selecao invalida.")
        except Exception as ex:
            print("Erro:", ex)
        finally:
            conn.close()

server_thread = threading.Thread(target=socket_server, daemon=True)
server_thread.start()

def signal_handler(sig, frame):
    print("Signal recebido, terminando processos.")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
    sys.exit(0)