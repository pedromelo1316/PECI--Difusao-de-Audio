import socket
import struct
import subprocess

MCAST_GRP = "224.1.1.1"
PORT = 8082

# Configura o socket multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", PORT))
mreq = struct.pack("4sL", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Inicia o ffplay lendo do pipe (stdin)
ffplay_cmd = [
    "ffplay",
    "-nodisp",
    "-autoexit",
    "-fflags", "nobuffer",
    "-i", "pipe:0"
]
ffplay_proc = subprocess.Popen(ffplay_cmd, stdin=subprocess.PIPE)

try:
    while True:
        data, addr = sock.recvfrom(65536)
        # Remove os 2 primeiros bytes (cabeçalho: channel e seq)
        if len(data) > 2:
            opus_data = data[2:]
            ffplay_proc.stdin.write(opus_data)
            ffplay_proc.stdin.flush()
except KeyboardInterrupt:
    pass
finally:
    sock.close()
    ffplay_proc.stdin.close()
    ffplay_proc.wait()
