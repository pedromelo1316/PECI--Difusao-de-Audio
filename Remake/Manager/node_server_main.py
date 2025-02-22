import socket
from node_server import node_server

def start_server():
    HOST = '0.0.0.0'  # Ouvindo em todas as interfaces de rede
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if message.startswith("Add Node"):
                    node_id = message.split()[-1]
                    node = node_server(addr[0])
                    response = f"NodeName={node.getName()}"
                    conn.sendall(response.encode('utf-8'))
                elif message.startswith("Remove Node"):
                    node_id = message.split()[-1]
                    if addr[0] in node_server._ips:
                        node_server._ips.remove(addr[0])
                        response = "Node Removed"
                        conn.sendall(response.encode('utf-8'))
                elif message.startswith("Add Area"):
                    area_name = message.split()[-1]
                    node = node_server(addr[0])
                    node.set_area(area_name)
                    response = f"AreaName={area_name}"
                    conn.sendall(response.encode('utf-8'))
                elif message.startswith("Remove Area"):
                    area_name = message.split()[-1]
                    node = node_server(addr[0])
                    node.set_area(None)
                    response = "Area Removed"
                    conn.sendall(response.encode('utf-8'))
                

if __name__ == "__main__":
    start_server()