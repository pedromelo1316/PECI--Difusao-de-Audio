import socket
import queue
import threading
import pyaudio
import time

def play_audio_from_queue(audio_queue, stop_event, min_buffer_size=3000):
    """ Continuously plays audio from the queue, starting only when the buffer has data. """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)

    # Espera a fila encher até um certo ponto antes de iniciar a reprodução
    while audio_queue.qsize() < min_buffer_size and not stop_event.is_set():
        print("Waiting for buffer to fill...")
        time.sleep(0.1)

    try:
        while not stop_event.is_set():
            if not audio_queue.empty():
                data = audio_queue.get()
                stream.write(data)
                print(f"Playing audio... Queue size: {audio_queue.qsize()}")
            else:
                print("Buffer underrun, waiting for more data...")
                time.sleep(0.05)  # Pequena espera para evitar travamentos
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def receive_broadcast(audio_queue, stop_event, port=8080):
    """ Receives broadcasted audio data and puts it in the queue. """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    sock.settimeout(1)
    print("Connected to port 8080")
    try:
        while not stop_event.is_set():
            try:
                data, _ = sock.recvfrom(4096)
                audio_queue.put(data)
                print("Received audio data... Queue size:", audio_queue.qsize())
            except socket.timeout:
                continue
    finally:
        sock.close()

if __name__ == '__main__':
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    # Start thread for receiving broadcasted audio
    receive_thread = threading.Thread(target=receive_broadcast, args=(audio_queue, stop_event))
    receive_thread.start()

    # Start thread for playing received audio
    play_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, stop_event))
    play_thread.start()

    try:
        receive_thread.join()
        play_thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        receive_thread.join()
        play_thread.join()
        print("Audio playback stopped.")
