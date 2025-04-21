import socket
import uuid
import threading
import time
import node_client  # Módulo customizado para a classe node_client
import json
import pyaudio
import subprocess
import base64
import signal
import sys
import numpy as np
import os

# Configurações básicas de áudio e transmissão
FREQ = 48000  # Frequência de amostragem do áudio
CHUNK_SIZE = 960  # Tamanho do bloco de áudio a ser lido do stream
SAMPLE_WIDTH = 2  # Bytes por amostra (pcm_s16le)

# Variáveis globais de controle do fluxo de mídia e estado do nó
HEADER = None    # Contém o SDP recebido que define a sessão de áudio
ffmpeg = None    # Processo do ffmpeg que vai tratar do stream de áudio
channel = None   # Canal de áudio recebido


global stop_event
stop_event = threading.Event()


def shutdown_handler(sig, frame):
    if ffmpeg:
        ffmpeg.terminate()
        ffmpeg.wait()
    stop_event.set()
    print("Exiting...")
    sys.exit(0)



def wait_for_info(n, port=8081):
    global HEADER, channel, stop_event, ffmpeg
    """
    Aguarda informações de controle do nó através de um socket UDP.
    Esse socket recebe mensagens JSON que alteram configurações como header, canal e volume.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        # Permite reutilização do endereço para evitar erros de "address already in use"
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.settimeout(1)
        while not stop_event.is_set():
            try:
                data, addr = server_socket.recvfrom(4096)
                data = data.decode('utf-8')
                dic = json.loads(data)
                # Verifica se a mensagem contém a chave que representa o MAC do nó
                if n.mac in dic.keys():
                    info = dic[n.mac]
                    print("Received info:", info)

                    # Verifica se a informação indica que o nó foi removido
                    if "removed" in info.keys():
                        print("Node removed")

                    
                    elif "suspended" in info.keys():
                        print("Node suspended")
                        
                    elif "test" in info.keys():
                        print("Test mode activated")
                        
                        # Parar o processo ffplay atual
                        if ffmpeg is not None:
                            ffmpeg.terminate()
                            ffmpeg.wait()
                            ffmpeg = None
                        
                        # Reproduzir um som de "pi" por 5 segundos
                        p = pyaudio.PyAudio()
                        stream = p.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=FREQ,
                                        output=True)
                        
                        # Gerar um tom de 440 Hz (nota A4) por 5 segundos
                        try:
                            duration = 2  # segundos
                            frequency = 440.0  # Hz
                            samples = (np.sin(2 * np.pi * np.arange(FREQ * duration) * frequency / FREQ)).astype(np.float32)
                            stream.write(samples.tobytes())
                        except Exception as e:
                            print(f"Error generating tone: {e}")
                        finally:
                            # Garantir que o stream e o PyAudio sejam fechados corretamente
                            if stream.is_active():
                                stream.stop_stream()
                            stream.close()
                            p.terminate()
                            
                        time.sleep(1)
                        
                        # Reiniciar o processo ffplay
                        if os.path.exists('session_received.sdp'):
                            cmd = [
                                'ffplay',
                                '-protocol_whitelist', 'file,rtp,udp',
                                '-nodisp',
                                '-i', 'session_received.sdp',
                                '-af', f'volume={n.getVolume()}'
                            ]
                            ffmpeg = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            print("Resumed ffplay process")
                        else:
                            print("SDP file not found, cannot restart ffplay")

                    
                    
                    # Atualiza as configurações de canal, volume e header a partir da mensagem
                    new_channel = info["channel"] if "channel" in info.keys() else None
                    volume = info["volume"] if "volume" in info.keys() else None
                    new_HEADER = info["header_normal"] if "header_normal" in info.keys() else None
                    new_mic_HEADER = info["header_mic"] if "header_mic" in info.keys() else None
                    
                    
                    n.setVolume(float(volume))
                
                
                    if ffmpeg is not None:
                        ffmpeg.terminate()
                        ffmpeg.wait()
                        ffmpeg = None
                    
                    HEADER = new_HEADER
                    channel = new_channel
                    n.setChannel(new_channel)
                    if new_HEADER is not None:
                        with open('session_received.sdp', 'w') as f:
                            f.write(new_HEADER)
                    else:
                        if os.path.exists('session_received.sdp'):
                            os.remove('session_received.sdp')
                            
                    if new_mic_HEADER is not None:
                        with open('session_received_mic.sdp', 'w') as f:
                            f.write(new_mic_HEADER)
                    else:
                        if os.path.exists('session_received_mic.sdp'):
                            os.remove('session_received_mic.sdp')
                            
                            
                    print("Updated channel and header")
                    
                    

                        
                        
                    #se ficheiro SDP já existe 
                    if os.path.exists('session_received_mic.sdp'):
                        cmd = [
                            'ffplay',
                            '-protocol_whitelist', 'file,rtp,udp',
                            '-nodisp',
                            '-i', 'session_received_mic.sdp',  # Arquivo SDP gerado pelo emissor
                            '-af', f'volume={volume}'  # Aplica o volume dinamicamente
                        ]
                    elif os.path.exists('session_received.sdp'):
                        cmd = [
                            'ffplay',
                            '-protocol_whitelist', 'file,rtp,udp',
                            '-nodisp',
                            '-i', 'session_received.sdp',  # Arquivo SDP gerado pelo emissor
                            '-af', f'volume={volume}'  # Aplica o volume dinamicamente
                        ]
                    else:
                        print("SDP file not found")
                        continue
                    
                    ffmpeg = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print("Restarting ffmpeg with new header, channel, and volume")
                    # Atualiza o header e o canal


            except socket.timeout:
                continue
            except ValueError as e:
                print("Error in wait_for_info:", e)

    # Fecha o socket ao finalizar o processo
    server_socket.close()

def wait_for_connection(n, port=8080):
    global stop_event
    """
    Estabelece uma conexão com o gerenciador através de broadcast UDP.
    Envia periodicamente informações do nó e aguarda uma resposta de "OK".
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        # Habilita o envio de broadcast
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.settimeout(1)  # Timeout de 5 segundos para a resposta
        while not stop_event.is_set():
            # Monta a mensagem com nome do host e MAC
            msg = f"{n.getName()},{n.getMac()}"
            client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', port))
            print("Sent information to manager")
            try:
                # Aguarda a resposta do gerenciador
                data, addr = client_socket.recvfrom(1024)
                if data == b"OK":
                    n.setHostIp(addr[0])
                    print("Connection established")
                    break
                else:
                    print("Connection refused")
                    time.sleep(5)
                    continue
            except Exception as e:  # Improved exception handling
                print(f"Connection error: {e}")
                time.sleep(1)
        client_socket.close()
        return True

def main():
    global ffmpeg, HEADER, channel
    try:
        # Obtém o nome do host e o endereço MAC do computador atual
        nome = socket.gethostname()
        mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
        # Cria o objeto node_client com as informações do dispositivo
        n = node_client.node_client(nome, mac)
        
        if os.path.exists('session_received.sdp'):
            os.remove('session_received.sdp')
            
        while os.path.exists('session_received.sdp'):
            time.sleep(1)

        # Associa o sinal SIGINT ao shutdown_handler para tratamento de Ctrl+C
        signal.signal(signal.SIGINT, shutdown_handler)


        # Cria e inicia a thread responsável por estabelecer a conexão com o gerenciador
        t_connection = threading.Thread(target=wait_for_connection, args=(n, 8080))
        t_connection.start()    
        
        # Cria e inicia a thread que ficará aguardando informações para controle do stream
        t_info = threading.Thread(target=wait_for_info, args=(n, 8081))
        t_info.start()

        # Aguarda o término das threads de conexão e recebimento de informações
        t_connection.join()
        t_info.join()
            
        # Garante o término do processo ffmpeg se estiver ativo
        if ffmpeg is not None:
            ffmpeg.terminate()
            ffmpeg.wait()
        
        print("Exiting...")
    except Exception as e:
        print("Unhandled exception in main:", e)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()