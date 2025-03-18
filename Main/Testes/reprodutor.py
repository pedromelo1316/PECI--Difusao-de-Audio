import socket
import subprocess
import pyaudio
import sys
import threading
import queue

# Configurações de multicast
MULTICAST_IP = "239.255.0.1"  # Endereço multicast
MULTICAST_PORT = 12345         # Porta multicast
BUFFER_SIZE = 4096             # Tamanho do buffer para receber pacotes

# Configurações de áudio
FORMAT = pyaudio.paInt16       # Formato de áudio PCM 16 bits
CHANNELS = 1                   # Mono
RATE = 48000                   # Taxa de amostragem de 48 kHz

# Fila para compartilhar dados entre threads
audio_queue = queue.Queue(maxsize=10)  # Limita o tamanho da fila para evitar atrasos

def receive_audio():
    """Recebe pacotes UDP multicast e os coloca na fila."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(("", MULTICAST_PORT))
    mreq = socket.inet_aton(MULTICAST_IP) + socket.inet_aton("0.0.0.0")
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Recebendo áudio multicast em {MULTICAST_IP}:{MULTICAST_PORT}...")
    try:
        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            print(f"Recebido {len(data)} bytes de {addr}")
            audio_queue.put(data)
    except KeyboardInterrupt:
        print("Recepção de áudio interrompida.")
    finally:
        udp_socket.close()

def feed_ffmpeg(ffmpeg_process):
    """Thread que envia os dados da fila ao stdin do ffmpeg."""
    try:
        while True:
            data = audio_queue.get()
            if not data:
                break
            ffmpeg_process.stdin.write(data)
    except KeyboardInterrupt:
        print("Feed de áudio interrompido.")
    finally:
        try:
            ffmpeg_process.stdin.close()
        except Exception:
            pass

def play_decoded_audio(ffmpeg_process, stream):
    """Thread que lê a saída do ffmpeg e reproduz o áudio."""
    try:
        while True:
            decoded_data = ffmpeg_process.stdout.read(BUFFER_SIZE)
            if not decoded_data:
                break
            stream.write(decoded_data)
    except KeyboardInterrupt:
        print("Reprodução de áudio interrompida.")

def decode_audio(stream):
    """
    Inicia o ffmpeg para decodificar o fluxo OGG Opus e
    cria duas threads: uma para enviar dados ao ffmpeg e outra para ler a saída.
    """
    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "ogg",          # Formato de entrada: OGG (saída do ffmpeg_stdout_rtp.py)
            "-i", "pipe:0",       
            "-f", "s16le",        # Saída: PCM 16 bits
            "-ar", str(RATE),
            "-ac", str(CHANNELS),
            "pipe:1"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Threads para enviar dados ao ffmpeg e reproduzir a saída
    feed_thread = threading.Thread(target=feed_ffmpeg, args=(ffmpeg_process,))
    play_thread = threading.Thread(target=play_decoded_audio, args=(ffmpeg_process, stream))

    feed_thread.start()
    play_thread.start()

    feed_thread.join()
    play_thread.join()

    ffmpeg_process.terminate()

def main():
    global stream

    # Inicializa o PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True,
        frames_per_buffer=BUFFER_SIZE
    )

    # Thread para receber áudio multicast
    receiver_thread = threading.Thread(target=receive_audio)
    # Thread para decodificar e reproduzir áudio
    decoder_thread = threading.Thread(target=decode_audio, args=(stream,))

    receiver_thread.start()
    decoder_thread.start()

    try:
        receiver_thread.join()
        decoder_thread.join()
    except KeyboardInterrupt:
        print("Receptor interrompido pelo usuário.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()