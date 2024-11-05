import threading
import subprocess
import yt_dlp
import queue
import wave
import pyaudio
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

def download_audio_stream(url, stop_event, conteudo_lock, conteudo_condition):
    """ Lê o stream de áudio e armazena os dados na variável compartilhada `conteudo`. """
    command = [
        'ffmpeg',
        '-i', url,
        '-vn',  # Sem vídeo
        '-f', 'wav',  # Formato de saída
        'pipe:1'  # Saída para stdout
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while not stop_event.is_set():
            data = process.stdout.read(4096)  # Lê 4 KB de dados
            if data:
                with conteudo_lock:
                    conteudo.append(data)
                    conteudo_condition.notify_all()
                    time.sleep(0.01)
                    print("Downloaded data and notified condition")
    finally:
        print("Closing the process...")
        process.terminate()
        process.wait()

def read_audio_stream(audio_queue, stop_event, queue_condition, conteudo_lock, conteudo_condition):
    """ Lê o conteúdo de áudio e adiciona à fila `audio_queue` para reprodução. """
    try:
        while not stop_event.is_set():
            with conteudo_lock:
                while not conteudo and not stop_event.is_set():
                    print("Waiting for content")
                    conteudo_condition.wait()

                local_data = b"".join(conteudo)
                conteudo.clear()
                print("Read content from global variable")

            with queue_condition:
                while audio_queue.qsize() > 10 and not stop_event.is_set():
                    print("Queue is full, waiting")
                    queue_condition.wait()
                audio_queue.put(local_data)
                queue_condition.notify_all()
                print("Added content to queue and notified condition")

    finally:
        print("Closing the reader process...")

def play_audio_from_queue(audio_queue, stop_event, queue_condition):
    """ Reproduz continuamente o áudio a partir da fila `audio_queue`. """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)

    try:
        while not stop_event.is_set():
            with queue_condition:
                while audio_queue.empty() and not stop_event.is_set():
                    print("Queue is empty, waiting")
                    queue_condition.wait()

                if not audio_queue.empty():
                    data = audio_queue.get()
                    queue_condition.notify_all()
                
            if data:
                stream.write(data)
                print(f"Playing audio... Queue size: {audio_queue.qsize()}")

    finally:
        print("Closing the stream...")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == '__main__':
    t1 = time.time()
    youtube_url = "https://www.youtube.com/live/36YnV9STBqc?si=labGt2YFC7__QGr7"  # URL do YouTube
    audio_queue = queue.Queue()
    stop_event = threading.Event()
    queue_condition = threading.Condition()
    conteudo_lock = threading.Lock()
    conteudo_condition = threading.Condition(conteudo_lock)
    conteudo = []  # Conteúdo compartilhado entre threads

    # Obter a URL do stream de áudio
    stream_url = get_audio_stream_url(youtube_url)
    print(f"Streaming from URL: {stream_url}")

    # Inicia a thread de leitura do stream de áudio
    download_thread = threading.Thread(target=download_audio_stream, args=(stream_url, stop_event, conteudo_lock, conteudo_condition))
    download_thread.start()

    # Inicia a thread de leitura do stream de áudio
    read_thread = threading.Thread(target=read_audio_stream, args=(audio_queue, stop_event, queue_condition, conteudo_lock, conteudo_condition))
    read_thread.start()

    # Inicia a thread de reprodução de áudio
    playback_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event, queue_condition))

    try:
        playback_thread.start()
        playback_thread.join()
        print(f"Tempo total: {time.time() - t1:.2f} segundos")
    except KeyboardInterrupt:
        stop_event.set()
        playback_thread.join()
        read_thread.join()
        download_thread.join()
        print(f"Tempo total: {time.time() - t1:.2f} segundos")
