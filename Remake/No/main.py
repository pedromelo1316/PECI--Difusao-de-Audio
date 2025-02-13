import socket
import no

def wait_for_id(n, port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"Aguardando atribuição de id na porta {port}...")
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024).decode('utf-8')
            # Espera-se mensagem no formato: "Conexão estabelecida com o manager: <id>"
            try:
                new_id = int(data.split(':')[-1].strip())
                n.id = new_id  # Atribuição do id recebido
                print("Id atribuído:", new_id)
            except Exception as e:
                print("Falha ao atribuir id:", e)

def wait_for_zona(n, port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"Aguardando atribuição de zona na porta {port}...")
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024).decode('utf-8')
            # Espera-se mensagem no formato: "Zona: <nome>"
            try:
                zona_nome = data.split(':')[-1].strip()
                n.zona = zona_nome  # Atribuição da zona recebida (supondo que o nó possua este atributo)
                print("Zona atribuída:", zona_nome)
            except Exception as e:
                print("Falha ao atribuir zona:", e)

def main():
    # Criação do nó. Certifique-se de que o construtor de no.no() permita não passar parâmetros,
    # ou modifique conforme necessário.
    n = no.no()
    
    # Checa e aguarda atribuição do id, se ainda não tiver sido definido.
    if n.getId() is None:
        print("Id é None")
        wait_for_id(n, port=12345)
            
    # Checa e aguarda atribuição da zona, se ainda não tiver sido definido.
    if n.getZona() is None:
        print("Zona é None")
        wait_for_zona(n, port=12345)

if __name__ == "__main__":
    main()