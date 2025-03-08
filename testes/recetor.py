import subprocess
import socket

# Configurações do multicast
MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5005

# Configurar socket UDP multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", MCAST_PORT))

# Entrar no grupo multicast
mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Comando FFmpeg para decodificar Opus e reproduzir com ffplay
ffplay_command = [
    "ffplay",
    "-nodisp",        # Sem janela de vídeo
    "-autoexit",      # Fecha ao terminar
    "-i", "pipe:0"    # Entrada via stdin
]

print("Escutando multicast e reproduzindo áudio...")

# Executar ffplay para reprodução
ffplay_proc = subprocess.Popen(ffplay_command, stdin=subprocess.PIPE)

channel = 0

try:
    while True:
        # Receber dados Opus via UDP
        packet, addr = sock.recvfrom(65535)  # Tamanho máximo de um pacote UDP

        if channel != packet[0]:
            continue

        opus_data = packet[1:]
        
        # Enviar dados para o ffplay decodificar e reproduzir
        ffplay_proc.stdin.write(opus_data)
        
except KeyboardInterrupt:
    print("Recepção interrompida.")
finally:
    ffplay_proc.terminate()
    sock.close()