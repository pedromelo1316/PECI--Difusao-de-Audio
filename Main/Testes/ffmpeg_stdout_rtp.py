import sys
import subprocess
import socket
import signal

BUFFER_SIZE = 8192  # Tamanho do buffer para leitura dos dados

def shutdown(signum, frame):
    print("Shutdown signal received.")
    sys.exit(0)

def main():
    if len(sys.argv) < 4:
        print("Usage: python ffmpeg_stdout_rtp.py <dest_host> <dest_port> <ffmpeg_cmd...>")
        sys.exit(1)

    dest_host = sys.argv[1]
    try:
        dest_port = int(sys.argv[2])
    except ValueError:
        print("Destination port must be an integer.")
        sys.exit(1)

    # Constrói o comando FFmpeg a partir dos argumentos restantes
    ffmpeg_cmd = sys.argv[3:]
    print("Running ffmpeg command:", " ".join(ffmpeg_cmd))
    print(f"Sending RTP packets to {dest_host}:{dest_port}")

    # Inicia o processo FFmpeg com o stdout redirecionado
    proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=BUFFER_SIZE)
    
    # Cria um socket UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Configura o tratamento de sinais de shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    try:
        while True:
            # Lê os dados do stdout do FFmpeg
            chunk = proc.stdout.read(BUFFER_SIZE)
            if not chunk:
                break

            # Envia o chunk como um pacote UDP
            udp_socket.sendto(chunk, (dest_host, dest_port))
    except Exception as e:
        print("Error:", e)
    finally:
        proc.stdout.close()
        proc.terminate()
        udp_socket.close()

if __name__ == "__main__":
    main()