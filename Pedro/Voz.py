import pyaudio
import threading
import sys
from pydub import AudioSegment

def gravar(callback, stop_event, output_file):
    # Configuração do áudio
    chunk = 1024  # Número de frames por buffer
    sample_format = pyaudio.paInt16  # Tamanho do formato de áudio
    channels = 1  # Número de canais
    fs = 44100  # Taxa de amostragem (samples por segundo)

    # Criação do objeto de áudio
    p = pyaudio.PyAudio()

    # Abre o stream de áudio
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    print('Gravando...')

    def read_audio():
        frames = []
        while not stop_event.is_set():
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            callback(data)

        # Converte os dados de áudio em MP3
        audio_segment = AudioSegment(
            data=b''.join(frames),
            sample_width=p.get_sample_size(sample_format),
            frame_rate=fs,
            channels=channels
        )
        audio_segment.export(output_file, format="mp3")

    # Cria e inicia a thread
    audio_thread = threading.Thread(target=read_audio)
    audio_thread.start()

    # Espera a thread terminar
    audio_thread.join()

    # Para o stream
    stream.stop_stream()
    stream.close()
    # Fecha o objeto de áudio
    p.terminate()

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
    gravar(print, stop_event, 'voz.mp3')
    input_thread.join()