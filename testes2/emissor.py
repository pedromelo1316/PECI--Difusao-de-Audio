import subprocess
import signal
import sys

def signal_handler(sig, frame):
    print("Signal received, terminating process.")
    process.terminate()
    sys.exit(0)

multicast_address = "rtp://239.255.0.1:12345"

source = "default"    # Nome do arquivo de playlist
INPUT_FILE = "default"  # Dispositivo de áudio padrão
BITRATE = "128k"        # Ajuste conforme necessário
SAMPLE_RATE = "48000"   # Opus recomenda 48kHz
CHANNELS = "1"          # Mono
CHUNCK_SIZE = 960     # Tamanho do pacote (ajuste conforme a rede)Z

ffmpeg_cmd = [
    "ffmpeg",
    "-stream_loop", "-1",
    #"-hide_banner", "-loglevel", "error",
    "-re",                   # Simula tempo real
    "-f", "concat",          # Utiliza o arquivo de concatenação
    "-safe", "0",            # Permite caminhos absolutos/relativos
    "-i", f"Playlists/{source}.txt",
    "-af", "apad",           # Preenche com silêncio entre músicas
    "-vn",                  # Sem vídeo
    "-c:a", "libopus",      # Codec Opus
    "-b:a", BITRATE,        # Bitrate (ex: 64k, 128k)
    "-f", "rtp",             # Formato RTP
    #"-ar", SAMPLE_RATE,     # Taxa de amostragem
    "-ac", CHANNELS,        # Canais
    "-sdp_file", "session.sdp",  # Gera arquivo SDP (opcional)
    multicast_address        # Endereço multicast
]
signal.signal(signal.SIGINT, signal_handler)
process = subprocess.Popen(ffmpeg_cmd)

try:
    process.wait()
except KeyboardInterrupt:
    process.terminate()
    process.wait()
    print("Processo interrompido pelo usuário.")