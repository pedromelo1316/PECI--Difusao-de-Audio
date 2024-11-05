import subprocess
import yt_dlp
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



def play_audio(url):
    """ Reproduz continuamente o áudio a partir da fila `audio_queue`. """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)
    


    command = [
        'ffmpeg',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-fflags', 'nobuffer',              # Desativa buffer para tentar reduzir o uso de memória e latência
        '-i', url,
        '-vn',
        '-f', 'wav',
        '-acodec', 'pcm_s16le',              # Define o codec de áudio explicitamente
        '-ar', '44100',                      # Taxa de amostragem padrão
        '-ac', '2',                          # Força áudio em estéreo
        'pipe:1'
    ]

    

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        while True:
            data = process.stdout.read(8192)  # Tenta ler blocos maiores
                
            if data:
                stream.write(data)
                print(f"Playing Audio Data size {len(data)}")

    except:
        print("Closing the process...")
        process.terminate()
        process.wait()
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Process closed")
        return

if __name__ == '__main__':
    t1 = time.time()
    youtube_url = "https://www.youtube.com/live/36YnV9STBqc?si=labGt2YFC7__QGr7"  # URL do YouTube

    url = get_audio_stream_url(youtube_url)
    

    play_audio(url)