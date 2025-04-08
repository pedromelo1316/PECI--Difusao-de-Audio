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
import signal
import os

# Configurações básicas de áudio e transmissão
FREQ = 48000  # Frequência de amostragem do áudio
CHUNK_SIZE = 960  # Tamanho do bloco de áudio a ser lido do stream
SAMPLE_WIDTH = 2  # Bytes por amostra (pcm_s16le)

# Variáveis globais de controle do fluxo de mídia e estado do nó
HEADER = None    # Contém o SDP recebido que define a sessão de áudio
ffmpeg = None    # Processo do ffmpeg que vai tratar do stream de áudio
play_thread = None  # Thread utilizada para reprodução do áudio
channel = None   # Canal de áudio recebido
player = None    # Objeto de player de áudio
stream = None    # Stream de áudio

global stop_event, player_stop_event
stop_event = threading.Event()
player_stop_event = threading.Event()


def terminate_routine():
    global stop_event, player_stop_event, play_thread, ffmpeg, stream, player, channel, HEADER
    
    print("Terminating processes...")
    
    try:
        if play_thread is not None:
            print("Stopping play_thread...")
            player_stop_event.set()
            play_thread.join(timeout=1)
            play_thread = None
    except Exception as e:
        print("Error stopping play_thread:", e)
    
    try:
        if ffmpeg is not None:
            print(f"Terminating ffmpeg process {ffmpeg.pid}...")
            try:
                os.killpg(os.getpgid(ffmpeg.pid), signal.SIGTERM)
                ffmpeg.wait(timeout=5)
            except ProcessLookupError:
                print(f"Process {ffmpeg.pid} already terminated.")
            except subprocess.TimeoutExpired:
                print(f"Process {ffmpeg.pid} did not terminate in time. Forcing termination...")
                try:
                    os.killpg(os.getpgid(ffmpeg.pid), signal.SIGKILL)
                    ffmpeg.wait(timeout=5)
                    print(f"Process {ffmpeg.pid} terminated.")
                except subprocess.TimeoutExpired:
                    print(f"Process {ffmpeg.pid} could not be killed.")
            ffmpeg = None
    except Exception as e:
        print("Error terminating ffmpeg:", e)
    
    try:
        if stream is not None:
            print("Closing audio stream...")
            stream.stop_stream()
            stream.close()
            stream = None
    except Exception as e:
        print("Error closing stream:", e)
    
    try:
        if player is not None:
            print("Terminating audio player...")
            player.terminate()
            player = None
    except Exception as e:
        print("Error terminating player:", e)
    
    HEADER = None
    channel = None
    print("Processes terminated.")


def shutdown_handler(sig, frame):
    print("Received SIGINT, shutting down...")
    terminate_routine()
    stop_event.set()
    os.exit(0)

def play_audio(n, sdp_file):
    global ffmpeg, player, stream, player_stop_event
    """
    Inicia a reprodução do stream de áudio via FFmpeg e pyaudio.
    Permite controle dinâmico do volume usando a configuração do nó.
    """
    print("Playing audio stream... from", sdp_file)
    # Comando ffmpeg montado para receber o stream RTP conforme o arquivo SDP
    ffmpeg_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "quiet",
        "-protocol_whitelist", "file,rtp,udp",
        "-i", sdp_file,
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-"
    ]
    # Inicia o processo ffmpeg com redirecionamento da saída padrão
    ffmpeg = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid   # Cria um novo grupo para o ffmpeg
    )
    player = pyaudio.PyAudio()
    # Abre um stream de áudio para saída; o formato é PCM com SAMPLE_WIDTH bytes e 2 canais
    stream = player.open(format=player.get_format_from_width(SAMPLE_WIDTH), channels=2, rate=FREQ, output=True)
    
    try:
        # Calcula o número de bytes por chunk (CHUNK_SIZE amostras por canal * SAMPLE_WIDTH * número de canais)
        bytes_per_chunk = CHUNK_SIZE * SAMPLE_WIDTH * 1  # Observação: comentário indica "2 channels" mas o cálculo é para 1 canal
        while not player_stop_event.is_set():
            # Lê um bloco de dados do stdout do ffmpeg
            chunk = ffmpeg.stdout.read(bytes_per_chunk)
            if not chunk:
                break
            # Converte os bytes do stream em array numpy de inteiros (int16)
            audio_data = np.frombuffer(chunk, dtype=np.int16)
            # Obtém o volume atual do nó (padrão 1.0 se não setado)
            volume = n.getVolume() if n.getVolume() is not None else 1.0
            # Aplica o fator de volume aos dados do áudio, com clipping para evitar estouro
            audio_data = np.clip(audio_data * volume, -32768, 32767).astype(np.int16)
            # Reproduz o áudio ajustado
            stream.write(audio_data.tobytes())
    except Exception as e:
        print("Error in play_audio:", e)
        
    print("Audio stream stopped.")

def wait_for_info(n, port=8081):
    global ffmpeg, HEADER, channel, play_thread, player, stream, player_stop_event, stop_event
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
                        terminate_routine()
                        stop_event.set()
                        break
                    
                    elif "suspended" in info.keys():
                        print("Node suspended")
                        terminate_routine()
                        continue
                    
                    
                    # Atualiza as configurações de canal, volume e header a partir da mensagem
                    new_channel = info["channel"] if "channel" in info.keys() else None
                    volume = info["volume"] if "volume" in info.keys() else None
                    new_HEADER = info["header"] if "header" in info.keys() else None
                    restart = info["restart"] if "restart" in info.keys() else False
                    
                    # Se volume recebido for diferente do atual, atualiza
                    if volume is not None and n.getVolume() != volume:
                        n.setVolume(float(volume))
                    
                    if restart:
                        # Se o volume for None, não altera
                        n.setVolume(None)
                        print("New header or channel received")
                        # Se houver uma thread de reprodução ativa, termina-a
                        terminate_routine()
                        player_stop_event.clear()
                        
                        # Atualiza o HEADER e o canal do nó
                        HEADER = new_HEADER 
                        # Grava o novo SDP em arquivo para que o ffmpeg o utilize
                        with open("session_received.sdp", "w") as f:
                            f.write(HEADER)
                        channel = new_channel
                        
                        # Atualiza o canal do nó
                        n.setChannel(channel)
                        
                        print("work")
                    
                            
                        # Se não houver uma thread de reprodução ativa, inicia uma nova
                        if play_thread is None:
                            print("Starting FFmpeg process...")
                            play_thread = threading.Thread(target=play_audio, args=(n, "session_received.sdp",))
                            play_thread.start()
                            print("FFmpeg process started.")
                        else:
                            # Termina a thread atual do ffmpeg e inicia uma nova, para atualizar o stream
                            print("Restarting FFmpeg process...")
                            play_thread = threading.Thread(target=play_audio, args=(n, "session_received.sdp",))
                            play_thread.start()
                            print("FFmpeg process restarted.")
                        
                        if new_HEADER is None or new_channel is None:
                            print("No new header or channel received")
                            terminate_routine()
                            player_stop_event.clear()
                            print("FFmpeg process stopped.")
                        
                        
                        
                    # Imprime as configurações atuais para debug
                    print("Channel:", n.getChannel())
                    print("Volume:", n.getVolume())

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
            except:
                print("Connection refused")
                time.sleep(1)
        client_socket.close()
        return True

def main():
    global play_thread, ffmpeg, HEADER, OP, channel, player, stream
    try:
        # Obtém o nome do host e o endereço MAC do computador atual
        nome = socket.gethostname()
        mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
        # Cria o objeto node_client com as informações do dispositivo
        n = node_client.node_client(nome, mac)

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
        
        # Se houver uma thread de reprodução ativa, espera seu término
        if play_thread is not None:
            play_thread.join()
            
        # Garante o término do processo ffmpeg se estiver ativo
        if ffmpeg is not None:
            ffmpeg.terminate()
        
        print("Exiting...")
    except Exception as e:
        print("Unhandled exception in main:", e)
    finally:
        terminate_routine()
        sys.exit(0)

if __name__ == "__main__":
    main()