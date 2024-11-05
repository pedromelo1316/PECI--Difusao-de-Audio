import subprocess
import yt_dlp
import pyaudio
import time
import threading

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


def play_audio(url):
    """ Reproduz continuamente o áudio a partir do fluxo de dados do FFmpeg. """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)
    
    # Define o comando FFmpeg para acessar o stream ao vivo
    command = [
        'ffmpeg',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '2',      # Reduzido para reconectar mais rápido
        '-fflags', 'nobuffer',            # Desativa o buffer
        '-i', url,
        '-vn',
        '-f', 'wav',
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '2',
        'pipe:1'
    ]

    # Loop de execução e reconexão
    while True:
        print("Starting FFmpeg stream...")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=32768)

        def log_ffmpeg_errors():
            """ Lê o stderr do ffmpeg continuamente para diagnóstico """
            for line in process.stderr:
                print(f"FFmpeg log: {line.decode('utf-8').strip()}")

        # Rodar o logger em uma thread separada
        threading.Thread(target=log_ffmpeg_errors, daemon=True).start()

        try:
            while True:
                data = process.stdout.read(8192)  # Ler dados em blocos maiores para eficiência

                if data:
                    stream.write(data)
                    print(f"Playing Audio Data size {len(data)}")
                else:
                    print("No data received, attempting to restart FFmpeg...")
                    break  # Quebra o loop para reiniciar o processo FFmpeg

        except Exception as e:
            print(f"Error during playback: {e}")
        
        finally:
            process.terminate()
            process.wait()
            print("Restarting FFmpeg stream...")
            time.sleep(1)  # Pausa curta antes de tentar reconectar
            break

    # Fechando o stream de áudio quando o loop for interrompido
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Playback terminated.")

if __name__ == '__main__':
    youtube_url = "https://www.youtube.com/live/36YnV9STBqc?si=labGt2YFC7__QGr7"
    url = get_audio_stream_url(youtube_url)
    play_audio(url)
