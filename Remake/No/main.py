import socket
import threading
import time
import no

# Alteramos wait_for_info para rodar continuamente em uma porta (8080)
def wait_for_info(n, port=8080):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            # ...aguarda conexão para atribuição de infos (id e zona, mesmo que canal venha depois)...
            print("Aguardando informações...")
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                try:
                    # Exemplo: "id=XXX,zona=YYY[,canal=ZZZ]"

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



def play_audio(n, port=8081):
    while n.getId() is not None and n.getZona() is not None and n.getCanal() is not None:
        print("Playing audio...")
        time.sleep(1)
    
    print("Parando Reprodução")


def main():
    n = no.no()  
    # Inicia as threads que aguardam informações e alterações. Estas ficam ativas durante toda a execução.
    t_info = threading.Thread(target=wait_for_info, args=(n,8080), daemon=True)
    t_info.start()

    while True:
        # Aguarda o nó ficar “completo”. Pode ser que canal ainda não tenha sido atribuído.
        if n.getId() is not None and n.getZona() is not None and n.getCanal() is not None:
            print(f"Iniciando reprodução para a zona {n.getZona()}...")
            t_audio = threading.Thread(target=play_audio, args=(n,8081))
            t_audio.start()
            t_audio.join()  # Aguarda encerramento da reprodução quando zona (ou outro info) for removido.
        time.sleep(0.5)

if __name__ == "__main__":
    main()