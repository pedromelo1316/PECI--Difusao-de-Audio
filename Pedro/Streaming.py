import threading
import subprocess
import yt_dlp
import sys

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

def record_stream(url, stop_event, callback, output_file):
    # Comando ffmpeg para capturar o áudio da transmissão ao vivo
    command = [
        'ffmpeg',
        '-i', url,
        '-vn',  # Sem vídeo
        '-f', 'mp3',  # Formato de saída
        'pipe:1'  # Saída para stdout
    ]
    # Inicia o processo ffmpeg
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(output_file, 'wb') as f:
        while not stop_event.is_set():
            data = process.stdout.read(1024)
            if not data:
                break
            f.write(data)
            callback(data)

    # Envia o sinal de término ao processo ffmpeg
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    # Lê e imprime o stderr para verificar erros
    #stderr = process.stderr.read().decode()
    #print(stderr)

def streaming(url, callback, stop_event, output_file):
    youtube_url = url
    # Obtém o URL direto do stream de áudio
    stream_url = get_audio_stream_url(youtube_url)
    print(f"Stream URL: {stream_url}")
    # Inicia a gravação do stream de áudio
    record_stream(stream_url, stop_event, callback, output_file)
    print('Gravação concluída')

def check_input(stop_event):
    while True:
        line = sys.stdin.read(1)
        if line.upper() == 'S':
            print('Parando a gravação...')
            stop_event.set()
            break

if __name__ == '__main__':
    stop_event = threading.Event()
    input_thread = threading.Thread(target=check_input, args=(stop_event,))
    input_thread.start()
    streaming("https://www.youtube.com/live/jfKfPfyJRdk?si=RE1Wmy099eHkcH7y", print, stop_event, 'streaming.mp3')
    input_thread.join()