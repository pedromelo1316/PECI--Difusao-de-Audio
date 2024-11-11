import socket
import threading
import subprocess
import yt_dlp
import queue
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

def read_audio_stream(url, audio_queue, stop_event):
    """ Reads the audio stream and puts data into the queue. Restarts ffmpeg on error. """
    while not stop_event.is_set():
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
                data = process.stdout.read(4096)
                if not data:
                    break  # No data, likely process failed
                audio_queue.put(data)
        finally:
            process.terminate()
            process.wait()

        print("Reconnecting to audio stream...")
        time.sleep(1)

def broadcast_audio(audio_queue, stop_event, broadcast_address, packet_size=1024):
    """ Continuously sends audio data via UDP broadcast in smaller packets. """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        while not stop_event.is_set():
            try:
                data = audio_queue.get(timeout=0.5)  # Wait for up to 0.5 sec for new data
                # Split data into packets of `packet_size`
                for i in range(0, len(data), packet_size):
                    packet = data[i:i+packet_size]
                    sock.sendto(packet, broadcast_address)
                
                print(f"Broadcasting audio data... Queue size: {len(data)}")
            except queue.Empty:
                # Continue waiting for new data if queue is empty
                continue
    finally:
        sock.close()

if __name__ == '__main__':
    youtube_url = "https://www.youtube.com/live/36YnV9STBqc?si=labGt2YFC7__QGr7"
    audio_queue = queue.Queue(maxsize=50)
    stop_event = threading.Event()

    # Set broadcast address and port
    broadcast_address = ('172.20.10.15', 8080)

    # Start audio reading thread
    stream_url = get_audio_stream_url(youtube_url)
    read_thread = threading.Thread(target=read_audio_stream, args=(stream_url, audio_queue, stop_event))
    read_thread.start()

    # Start broadcasting thread
    broadcast_thread = threading.Thread(target=broadcast_audio, args=(audio_queue, stop_event, broadcast_address))
    broadcast_thread.start()

    try:
        read_thread.join()
        broadcast_thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        read_thread.join()
        broadcast_thread.join()
        print("Broadcast stopped.")
