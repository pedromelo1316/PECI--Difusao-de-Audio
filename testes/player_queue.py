import os
import subprocess
import time
import queue
import threading
import numpy as np
import pyaudio

def get_local(q, stop_event=None):
    playlist_dir = "Playlist"  # Pasta com arquivos .mp3
    files = [os.path.join(playlist_dir, f) for f in os.listdir(playlist_dir) if f.lower().endswith(".mp3")]
    if not files:
        if stop_event:
            stop_event.set()
        return

    file_index = 0
    while not (stop_event and stop_event.is_set()):
        current_file = files[file_index]
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", current_file,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "1",
            "pipe:1"
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while not (stop_event and stop_event.is_set()):
                try:
                    data = process.stdout.read(1024)
                except OSError:
                    break
                if not data:
                    break
                q.put(data)
        except Exception:
            pass
        finally:
            if process.stdout:
                process.stdout.close()
            process.terminate()
            process.wait()
        file_index = (file_index + 1) % len(files)

def wait_queue(audio_queue, stop_event, min_buffer_size=10):
    while audio_queue.qsize() < min_buffer_size and not (stop_event and stop_event.is_set()):
        print(f"Waiting for buffer to fill... Queue size: {audio_queue.qsize()}")
        time.sleep(0.1)

class VolumeControl:
    # Exemplo de classe para controle de volume
    def __init__(self, volume=1.0):
        self.volume = volume
    def getVolume(self):
        return self.volume

def play_audio_from_queue(audio_queue, stop_event, n, min_buffer_size=2):
    p_instance = pyaudio.PyAudio()
    stream = p_instance.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=44100,
                             output=True,
                             frames_per_buffer=1024)
    # Espera a fila encher até o mínimo desejado
    wait_queue(audio_queue, stop_event, min_buffer_size)
    print("Starting audio playback...")

    try:
        while not (stop_event and stop_event.is_set()):
            if not audio_queue.empty():
                data = audio_queue.get()
                volume = n.getVolume()
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_data = np.clip(audio_data * volume, -32768, 32767).astype(np.int16)
                adjusted_data = audio_data.tobytes()
                stream.write(adjusted_data)
                print(f"Playing audio... Queue size: {audio_queue.qsize()}")
            else:
                print(f"Buffer underrun, waiting for more data... {audio_queue.qsize()}")
                wait_queue(audio_queue, stop_event, min_buffer_size)
    finally:
        stream.stop_stream()
        stream.close()
        p_instance.terminate()

if __name__ == "__main__":
    audio_queue = queue.Queue()
    stop_event = threading.Event()
    volume_control = VolumeControl(1.0)  # Ajuste o volume conforme necessário

    getter_thread = threading.Thread(target=get_local, args=(audio_queue, stop_event))
    player_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event, volume_control))

    getter_thread.start()
    player_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()

    getter_thread.join()
    player_thread.join()
