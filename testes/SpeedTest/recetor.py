import socket
import struct

# Configurações do multicast
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))  # Associa à porta

# Entra no grupo multicast
mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Variáveis para controle de perdas
esperado = 0
recebidos = set()

try:
    while True:
        # Recebe o pacote
        data, addr = sock.recvfrom(1922)
        seq = struct.unpack('!I', data[:4])[0]
        recebidos.add(seq)

        # Verifica se há perda de pacotes
        if seq != esperado:
            print(f"Pacote {esperado} perdido.")
            esperado = seq + 1
            while esperado in recebidos:
                esperado += 1
        else:
            esperado += 1
        
except KeyboardInterrupt:
    print("Receptor encerrado.")