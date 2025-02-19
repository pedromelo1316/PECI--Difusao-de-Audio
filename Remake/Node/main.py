import socket
import threading
import time
import node_client
import queue
import pyaudio

def wait_for_info(n, port=8080):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            print("Waiting for information...")
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                print(data)
                try:
                    # Exemplo esperado: "id=XXX,zona=YYY[,Channel=ZZZ]"
                    if data == "Node Removed":
                        print("Change: Node removed.")
                        n.setId(None)
                        n.setArea(None)
                        n.setChannel(None)
                    elif data == "Area Removed":
                        print("Change: Node removed from area.")                        
                        n.setArea(None)
                        n.setChannel(None)
                    elif data == "Channel Removed":
                        print("Alteração: Channel removido.")
                        n.setChannel(None)
                    elif data.__contains__('Add Node'):
                        n.setId(data.split(' ')[2])
                        n.setName(socket.gethostname())

                        print(f"Node addded: id={n.getId()}, name={n.getName()}")
                        conn.sendall(b"Node name=" + n.getName().encode('utf-8'))
                        
                    else:
                        for item in data.split(','):
                            key, value = item.split('=')
                            if key == 'id':
                                n.setId(value)
                            elif key == 'area':
                                n.setArea(value)
                            elif key == 'channel':
                                print("work")
                                n.setChannel(value)
                    print(f"Updated info: id={n.getId()}, area={n.getArea()}, channel={n.getChannel()}")
                except ValueError as e:
                    print("Error in wait_for_info:", e)

def listen_for_detection(detection_port=9090):
    """Escuta mensagens UDP e responde com 'hello' ao comando 'Detetar'."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", detection_port))
    
    print(f"Listening for detection on port {detection_port}...")
    while True:
        data, addr = sock.recvfrom(1024)
        if data.decode('utf-8').strip() == "Detect":
            print(f"Received 'Detect' from {addr}. Responding with 'hello'.")
            try:
                sock.sendto(b"hello", addr)
                print(f"'hello' packet sent to {addr}.")
            except Exception as send_exc:
                print(f"Error sending 'hello' to {addr}: {send_exc}")



def play_audio_from_queue(audio_queue, stop_event, min_buffer_size=3000):
    """Continuously plays audio from the queue, starting only when the buffer has enough data."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)

    # Espera a fila encher até um certo ponto antes de iniciar a reprodução
    while audio_queue.qsize() < min_buffer_size and not stop_event.is_set():
        print("Waiting for buffer to fill...")
        time.sleep(0.1)

    try:
        while not stop_event.is_set():
            if not audio_queue.empty():
                data = audio_queue.get()
                stream.write(data)
                print(f"Playing audio... Queue size: {audio_queue.qsize()}")
            else:
                print("Buffer underrun, waiting for more data...")
                time.sleep(0.1)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()




def receive_broadcast(audio_queue, n, stop_event, port=8081):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    sock.settimeout(1)

    canal = n.getChannel()
    try:
        while not stop_event.is_set():

            data, addr = sock.recvfrom(3072)
            try:
                
                Channel = int(canal)
                audio = data[((Channel-1) * 1024):(1024*Channel)] if (Channel is not None and Channel > 0) else b""
                
                audio_queue.put(audio) if audio else None

            except (ValueError, AttributeError) as e:
                print("Error in processing:", e)

            except socket.timeout:
                continue

        canal = n.getChannel()

    finally:
        sock.close()
        
    print("Stopping playback")


def main():
    n = node_client.node_client() 

    audio_queue = queue.Queue()

    stop_event = threading.Event()


    # Thread para aguardar informações e alterações
    t_info = threading.Thread(target=wait_for_info, args=(n, 8080), daemon=True)
    t_info.start()
    # Thread para responder ao comando "Detetar"
    t_detect = threading.Thread(target=listen_for_detection, args=(9090,), daemon=True)
    t_detect.start()

    while True:
        # Aguarda o nó ficar “completo” (com todas as infos)
        if n.getId() is not None and n.getArea() is not None and n.getChannel() is not None:
            print(f"Starting playback for zone {n.getArea()}...")
            t_receive = threading.Thread(target=receive_broadcast, args=(audio_queue,n,stop_event ,8081) ,daemon=True)
            t_audio = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event), daemon=True)
            t_audio.start()
            t_receive.start()



            while n.getId() is not None and n.getArea() is not None and n.getChannel() is not None:
                time.sleep(0.5)
        

             # Se a informação do nó for removida, sinaliza para parar os threads de áudio
            stop_event.set()
            t_audio.join()
            t_receive.join()
            print("Reprodução interrompida. Aguardando novas informações...")
            # Reinicia o stop_event e limpa o buffer para a próxima reprodução
            stop_event.clear()
            while not audio_queue.empty():
                audio_queue.get()
        time.sleep(0.5)

if __name__ == "__main__":
    main()