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

def read_audio_stream(url, audio_queue, stop_event, queue_lock):
    """ Lê o stream de áudio e armazena os dados na fila com lock. """
    command = [
        'ffmpeg',
        '-i', url,
        '-vn',  # No video
        '-f', 'wav',  # Output format
        'pipe:1'  # Output to stdout
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        while not stop_event.is_set():
            data = process.stdout.read(4096)  # Lê 4 KB de dados
            if data:
                audio_queue.put(data)
                print(f"Queue size {audio_queue.qsize()}")
    finally:
        print("Closing the process...")
        process.terminate()
        process.wait()

def play_audio_from_queue(audio_queue, stop_event, queue_lock):
    """ Reproduz continuamente o áudio a partir da fila com lock. """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)

    try:
        while not stop_event.is_set():
            if not audio_queue.empty():
                data = audio_queue.get()
            else:
                data = None
            
            if data:
                stream.write(data)
                print(f"\rPlaying audio... Queue size: {audio_queue.qsize()}", end="")

            else:
                print("Queue is empty, waiting for data...")
                while audio_queue.empty() and not stop_event.is_set():
                    time.sleep(0.1)
    finally:
        print("Closing the stream")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == '__main__':
    t1 = time.time()
    youtube_url = "https://www.youtube.com/live/36YnV9STBqc?si=labGt2YFC7__QGr7"  # URL do YouTube
    audio_queue = queue.Queue()
    stop_event = threading.Event()
    queue_lock = threading.Lock()  # Lock para sincronizar o acesso à fila

    # Obter a URL do stream de áudio
    stream_url = get_audio_stream_url(youtube_url)
    print(f"Streaming from URL: {stream_url}")

    # Inicia a thread de leitura do stream de áudio
    read_thread = threading.Thread(target=read_audio_stream, args=(stream_url, audio_queue, stop_event, queue_lock))
    read_thread.start()

    # Inicia a thread de reprodução de áudio
    playback_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event, queue_lock))

    try:
        playback_thread.start()
        playback_thread.join()
        print(f"Tempo total: {time.time() - t1:.2f} segundos")
    except KeyboardInterrupt:
        stop_event.set()
        playback_thread.join()
        read_thread.join()
        print("Playback stopped.")


    
