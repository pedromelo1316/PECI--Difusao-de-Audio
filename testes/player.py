import time
import queue
import threading
from pydub import AudioSegment
import pyaudio

CHUNK_SIZE = 1024  # Tamanho do chunk em bytes

# Carregar arquivo MP3 e converter para PCM com parâmetros fixos (44100 Hz, 2 canais, 16 bits)
audio = AudioSegment.from_mp3("audio.mp3")
raw_data = audio.raw_data

# Configurar parâmetros de áudio
sample_width = audio.sample_width
channels = audio.channels
frame_rate = audio.frame_rate

# Calcular intervalo de tempo entre chunks (informativo apenas, removido no envio)
bytes_per_frame = sample_width * channels
chunk_frames = CHUNK_SIZE // bytes_per_frame
time_per_chunk = chunk_frames / frame_rate

# Inicializar queue para armazenar os chunks de áudio
audio_queue = queue.Queue()

# Configurar PyAudio
p = pyaudio.PyAudio()
stream = p.open(
    format=p.get_format_from_width(sample_width),
    channels=channels,
    rate=frame_rate,
    output=True
)

# Worker para reprodução do áudio
def playback_worker():
    while True:
        data = audio_queue.get()
        if data is None:  # Sentinel para término
            break
        stream.write(data)

playback_thread = threading.Thread(target=playback_worker)
playback_thread.start()

# Enfileirar todos os chunks de áudio sem pausa (stream.write sincroniza a reprodução)
for i in range(0, len(raw_data), CHUNK_SIZE):
    chunk = raw_data[i:i+CHUNK_SIZE]
    if len(chunk) < CHUNK_SIZE:
        chunk += b'\x00' * (CHUNK_SIZE - len(chunk))
    audio_queue.put(chunk)
    # Removido o time.sleep para não desincronizar a reprodução:
    time.sleep(time_per_chunk/2)

# Sinalizar término e aguardar worker finalizar
audio_queue.put(None)
playback_thread.join()

stream.stop_stream()
stream.close()
p.terminate()
