import socket
import time
import struct

# Configurações do multicast
MCAST_GRP = '224.1.1.1'  # Endereço multicast
MCAST_PORT = 5005         # Porta
PACKET_SIZE_BITS = 1922   # Tamanho do pacote em bits (128 bytes)
RATE_MBPS = 5          # Taxa de transmissão desejada (20 Mbps)

# Calcula o intervalo entre pacotes (em segundos)
intervalo = (PACKET_SIZE_BITS*8) / (RATE_MBPS * 1e6)  # Bits / (bits/segundo)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # TTL=2

seq_num = 0  # Número de sequência inicial


start_time = time.time()
count = 0
try:
    while True:
        # Monta o pacote: 4 bytes (seq_num) + 124 bytes de dados
        dados = struct.pack('!I', seq_num) + b'\x00' * (PACKET_SIZE_BITS - 4)
        sock.sendto(dados, (MCAST_GRP, MCAST_PORT))
        seq_num = seq_num + 1
        time.sleep(intervalo)  # Intervalo para controle de taxa
        print(f"\rEnviado: {seq_num}, velocidade: {(seq_num*PACKET_SIZE_BITS)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")
except KeyboardInterrupt:
    print("Emissor encerrado.")