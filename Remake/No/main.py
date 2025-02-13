import socket
import threading
import time
import no

def wait_for_id(n, port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

def wait_for_zona(n, port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"Aguardando atribuição de zona na porta {port}...")
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024).decode('utf-8')
            # Espera-se mensagem no formato: "Zona: <nome>"
            try:
                zona_nome = data.split(':')[-1].strip()
                n.zona = zona_nome  # Atribuição da zona recebida
                print("Zona atribuída:", zona_nome)
            except Exception as e:
                print("Falha ao atribuir zona:", e)

def wait_no_zone(n, port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"Aguardando comando de remoção da zona na porta {port}...")
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024).decode('utf-8')
            if "Removido da zona:" in data:
                # Remoção da zona
                n.zona = None
                print("Zona removida.")

def play_audio(n, port=8081):
    # Enquanto a zona estiver atribuída, continua fazendo "algo"
    while n.getZona() is not None:
        print("Playing audio...")
        # Simulando processamento
        time.sleep(1)
    print("Parando play_audio, pois a zona foi removida.")

def main():
    n = no.no()
    
    # Aguarda atribuição do id (executado apenas uma vez)
    if n.getId() is None:
        print("Id é None")
        wait_for_id(n, port=8080)
    
    # Loop principal: aguarda atribuição da zona; assim que houver zona, inicia as threads
    while True:
        if n.getZona() is None:
            print("Zona é None")
            wait_for_zona(n, port=8080)
        else:
            print(f"Iniciando reprodução para a zona {n.getZona()}...")
            # Cria threads para esperar remoção da zona e para reproduzir áudio
            t_wait = threading.Thread(target=wait_no_zone, args=(n, 8080))
            t_audio = threading.Thread(target=play_audio, args=(n, 8081))
            t_wait.start()
            t_audio.start()
            # Aguarda a thread de remoção terminar; a partir dela, n.zona será None.
            t_wait.join()
            # A thread play_audio deve verificar a condição e encerrar quando n.zona for None.
            t_audio.join()
            print("Voltando a aguardar nova atribuição de zona.")
            
if __name__ == "__main__":
    main()