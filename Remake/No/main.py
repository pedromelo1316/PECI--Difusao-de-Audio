import socket
import threading
import time
import no

def wait_for_info(n, port=8080):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            print("Aguardando informações...")
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                try:
                    # Exemplo esperado: "id=XXX,zona=YYY[,canal=ZZZ]"
                    if data == "Nó Removido":
                        print("Alteração: Nó removido.")
                        n.setId(None)
                        n.setZona(None)
                        n.setCanal(None)
                    elif data == "Removido da zona":
                        print("Alteração: Nó removido da zona.")
                        n.setZona(None)
                        n.setCanal(None)
                    elif data == "Canal removido":
                        print("Alteração: Canal removido.")
                        n.setCanal(None)
                    else:
                        for item in data.split(','):
                            key, value = item.split('=')
                            if key == 'id':
                                n.setId(value)
                            elif key == 'zona':
                                n.setZona(value)
                            elif key == 'canal':
                                n.setCanal(value)
                    print(f"Info atualizada: id={n.getId()}, zona={n.getZona()}, canal={n.getCanal()}")
                except ValueError as e:
                    print("Erro em wait_for_info:", e)

def listen_for_detection(detection_port=9090):
    """Escuta mensagens UDP e responde com 'hello' ao comando 'Detetar'."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', detection_port))
    print(f"Escutando detecção na porta {detection_port}...")
    while True:
        data, addr = sock.recvfrom(1024)
        if data.decode('utf-8').strip() == "Detetar":
            print(f"Recebido 'Detetar' de {addr}. Respondendo com 'hello'.")
            sock.sendto(b"hello", addr)

def play_audio(n, port=8081):
    while n.getId() is not None and n.getZona() is not None and n.getCanal() is not None:
        print("Playing audio...")
        time.sleep(1)
    print("Parando Reprodução")

def main():
    n = no.no()  
    # Thread para aguardar informações e alterações
    t_info = threading.Thread(target=wait_for_info, args=(n, 8080), daemon=True)
    t_info.start()
    # Thread para responder ao comando "Detetar"
    t_detect = threading.Thread(target=listen_for_detection, args=(9090,), daemon=True)
    t_detect.start()

    while True:
        # Aguarda o nó ficar “completo” (com todas as infos)
        if n.getId() is not None and n.getZona() is not None and n.getCanal() is not None:
            print(f"Iniciando reprodução para a zona {n.getZona()}...")
            t_audio = threading.Thread(target=play_audio, args=(n, 8081))
            t_audio.start()
            t_audio.join()  # Aguarda encerramento da reprodução quando alguma info for removida.
        time.sleep(0.5)

if __name__ == "__main__":
    main()