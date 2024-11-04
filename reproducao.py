import threading
import subprocess
import yt_dlp
from pydub import AudioSegment
from io import BytesIO
import pydub.playback
import time

def get_audio_stream_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        formats = info_dict.get('formats', [info_dict])
        for f in formats:
            if f.get('acodec') != 'none':
                return f['url']
    raise Exception("No audio stream found")

def read_audio_stream(url, buffer, buffer_lock, stop_event):
    """ Lê o stream de áudio e armazena os dados no buffer. """
    command = [
        'ffmpeg',
        '-i', url,
        '-vn',  # No video
        '-f', 'mp3',  # Output format
        'pipe:1'  # Output to stdout
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        while not stop_event.is_set():
            data = process.stdout.read(512)  # Lê 4 KB de dados
            
            if not data:
                break
            
            with buffer_lock:
                buffer.extend(data)  # Adiciona dados ao buffer
                print("Buffer size:", len(buffer))  
    finally:
        process.terminate()
        process.wait()

def play_audio(buffer, buffer_lock, stop_event):
    """ Reproduz continuamente o áudio a partir do buffer. """
    while not stop_event.is_set():
        time.sleep(0.1)  # Pequeno atraso para gerenciar o fluxo

        with buffer_lock:
            if len(buffer) >= 256:  # Verifica se há dados suficientes
                audio_data = bytes(buffer)  # Junta todos os dados do buffer
                audio_segment = AudioSegment.from_file(BytesIO(audio_data), format="mp3")
                pydub.playback.play(audio_segment)
                buffer.clear()  # Limpa o buffer após reproduzir
            elif len(buffer) > 0:
                print("Not enough data in buffer for playback, waiting for more...")
            

if __name__ == '__main__':
    youtube_url = "https://www.youtube.com/watch?v=mix9YfaaNa0&ab_channel=twentyonepilots"  # URL do YouTube
    buffer = bytearray()
    buffer_lock = threading.Lock()
    stop_event = threading.Event()

    # Obter a URL do stream de áudio
    stream_url = get_audio_stream_url(youtube_url)
    print(f"Streaming from URL: {stream_url}")

    # Inicia a thread de leitura do stream de áudio
    read_thread = threading.Thread(target=read_audio_stream, args=(stream_url, buffer, buffer_lock, stop_event))
    read_thread.start()

    # Inicia a thread de reprodução de áudio
    playback_thread = threading.Thread(target=play_audio, args=(buffer, buffer_lock, stop_event))
    playback_thread.start()

    try:
        while True:
            time.sleep(1)  # Mantém o programa em execução
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()

    read_thread.join()
    playback_thread.join()
    print("Program terminated.")
