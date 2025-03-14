import os
import subprocess
import socket
import time
import threading

# Variáveis globais necessárias
BITRATE = "64000"
SAMPLE_RATE = "48000"
AUDIO_CHANNELS = "2"
CHUNCK_SIZE = 4096
MULTIPLICADOR = 1


# Configura o stdout dos processos FFmpeg para ser não bufferizado
def start_ffmpeg_process(source, _type):
    if (_type == "VOICE"):
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-f", "alsa", "-i", source,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            "-f", "opus",
            "pipe:1"
        ]
    elif (_type == "LOCAL"):
        playlist_path = f"Playlists/{source}.txt"
        if not os.path.exists(playlist_path):
            print(f"Playlist {playlist_path} not found")
            return None

        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
            "-f", "concat",          # Adicione esta linha
            "-safe", "0",            # Permite caminhos absolutos/relativos
            "-re",                   # Opcional (simula velocidade real)
            "-i", f"Playlists/{source}.txt",
            "-af", "apad",  # Preenche com silêncio entre as músicas
            "-vn",
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            "-packet_size", str(CHUNCK_SIZE), # Tamanho do pacote (ajuste conforme a rede)
            "-f", "opus",
            "pipe:1"
        ]
    elif (_type == "TRANSMISSION"):
        return None
    else:
        return None
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=int(CHUNCK_SIZE*2))
    return process

channels_dict = {}
# Inicia um canal exemplo; certifique-se de que o arquivo Playlists/test.txt exista.
channels_dict[0] = {"process": start_ffmpeg_process("default", "LOCAL")}

start_time = time.time()



def send_audio(port=8082, stop_event=None):
    global start_time
    MCAST_GRP = "224.1.1.1"
    MCAST_PORT = port

    count = 0
    seq = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = 2
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        while not stop_event.is_set():
            for channel in list(channels_dict.keys()):
                if channels_dict[channel] is None:
                    continue
                process = channels_dict[channel]["process"]
                if process:
                    opus_data = process.stdout.read(CHUNCK_SIZE*MULTIPLICADOR)  # Ajuste o tamanho conforme necessário
                    if not opus_data:
                        break
                    
                    dados = bytes([channel]) + bytes([seq]) + opus_data
                    sock.sendto(dados, (MCAST_GRP, MCAST_PORT))

                    #print(f"\rEnviado: {seq}, velocidade: {(count*CHUNCK_SIZE*MULTIPLICADOR)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")
                    count += 1
                
            seq = (seq + 1) % 256
            #print(f"\rEnviado: {seq}, velocidade: {(count*CHUNCK_SIZE*MULTIPLICADOR)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")

    except KeyboardInterrupt:
        print("Transmissão interrompida.")
    finally:
        sock.close()
        for channel in list(channels_dict.keys()):
            if channels_dict[channel]:
                process = channels_dict[channel]["process"]
                process.terminate()
                process.wait()
        print("Processes terminated")
        stop_event.set()

if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        send_audio(8082, stop_event)
    except Exception as e:
        print("Erro:", e)
    finally:
        stop_event.set()