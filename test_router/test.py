import socket
import struct

MCAST_GRP = "239.255.0.1"
PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", PORT))

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    data, addr = sock.recvfrom(2048)  # Increase buffer size for RTP payload
    if len(data) >= 12:  # RTP header is at least 12 bytes
        rtp_header = struct.unpack("!BBHII", data[:12])
        payload_type = rtp_header[1] & 0x7F  # RTP payload type
        sequence_number = rtp_header[2]  # 16-bit sequence number
        timestamp = rtp_header[3]  # RTP timestamp
        
        print(f"Received RTP packet from {addr}")
        print(f"  - Sequence Number (Frame Number): {sequence_number}")
        print(f"  - Timestamp: {timestamp}")
        print(f"  - Payload Type: {payload_type}")
