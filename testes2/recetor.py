import subprocess
import signal
import sys
import socket

# Solicita canal ao usuário e obtém SDP via socket
channel = input("Escolha o canal (1, 2 ou 3): ").strip()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 9000))  # Altere se o emissor estiver em outra máquina
s.sendall(channel.encode())
session_data = s.recv(4096).decode()
s.close()
with open("session_received.sdp", "w") as f:
    f.write(session_data)
sdp_file = "session_received.sdp"

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
    print('Ctrl+C pressionado, terminando processos...')
    ffmpeg.terminate()
    player.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

try:
    player.communicate()
except KeyboardInterrupt:
    signal_handler(None, None)