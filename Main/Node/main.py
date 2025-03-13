import socket
import uuid
import threading
import time
import node_client
import json
import pyaudio
import subprocess
import base64
import signal
import sys

FREQ = 48000
CHUNCK_SIZE = 960

SAMPLE_WIDTH = 2  # bytes por sample (pcm_s16le)
CHUNK_SIZE = 960




OP = 3
HEADER = None
player = None
ffmpeg = None
play_thread = None
channel = None



def play_audio(sdp_file):
    global ffmpeg, player
    """Plays the RTP audio stream using FFmpeg."""
    print("Playing audio stream... from", sdp_file)
    ffmpeg_cmd = [
        "ffmpeg",
        #"-hide_banner",
        #"-loglevel", "error",
        "-protocol_whitelist", "file,rtp,udp",
        "-i", sdp_file,
        "-c:a", "pcm_s16le",
        "-f", "wav",
        "pipe:1"
    ]

    player_cmd = [
        "ffplay",
        #"-hide_banner",
        #"-loglevel", "error",
        "-nodisp",
        "-autoexit",
        "-"
    ]

    # Removed signal.signal registration since signals only work in the main thread.
    ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
    player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

    try:
        player.communicate()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Terminating processes...")
        ffmpeg.terminate()
        player.terminate()
        time.sleep(0.5)



def wait_for_info(n, port=8081, stop_event=None):
    global ffmpeg, player, HEADER, OP, channel, play_thread
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        while not stop_event.is_set():
            data, addr = server_socket.recvfrom(4096)
            data = data.decode('utf-8')
            try:
                dic = json.loads(data)
                if n.mac in dic.keys():
                    info = dic[n.mac]

                    if "removed" in info.keys():
                        print("Node removed")
                        stop_event.set()
                        break

                    # Se os valores forem null (None) atualiza para None explicitamente
                    channel = info["channel"] if info["channel"] is not None else None
                    volume = info["volume"] if info["volume"] is not None else None
                    _HEADER = info["header"] if info["header"] is not None else None
                    #_HEADER = base64.b64decode(_HEADER) if _HEADER is not None else None
                    n.setChannel(channel)
                    n.setVolume(volume)
                    if _HEADER != HEADER:
                        HEADER = _HEADER
                        sync_time = info.get("sync_time", None)
                        if sync_time:
                            delay = sync_time - time.time()
                            if delay > 0:
                                print("Waiting for sync delay:", delay)
                                time.sleep(delay)
                        with open("session_received.sdp", "w") as f:
                            f.write(HEADER)
                            
                        if ffmpeg is None and player is None:
                            play_thread = threading.Thread(target=play_audio, args=("session_received.sdp",))
                            play_thread.start()
                            print("Processo FFmpeg iniciado.")
                        else:
                            ffmpeg.terminate()
                            player.terminate()
                            play_thread.join()
                            play_thread = threading.Thread(target=play_audio, args=("session_received.sdp",))
                            play_thread.start()
                            print("Processo FFmpeg reiniciado.")



                    print("Channel:", n.getChannel())
                    print("Volume:", n.getVolume())


            except ValueError as e:
                print("Error in wait_for_info:", e)

    server_socket.close()


def wait_for_connection(n, port=8080, stop_event=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.settimeout(5)
        while not stop_event.is_set():
            msg = f"{n.getName()},{n.getMac()}"
            client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', port))
            
            print("Sent information to manager")

            try:
                data, addr = client_socket.recvfrom(1024)
                if data == b"OK":
                    n.setHostIp(addr[0])
                    print("Connection established")
                    break
                else:
                    print("Connection refused")
                    time.sleep(5)
                    continue
            except:
                print("Connection refused")
                time.sleep(1)
        client_socket.close()
        return True
    
    


def main():
    global play_thread, ffmpeg, player, HEADER, OP, channel
    nome = socket.gethostname()
    mac = ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in reversed(range(0, 48, 8))])
    n = node_client.node_client(nome, mac)
    stop_event = threading.Event()

    t_connection = threading.Thread(target=wait_for_connection, args=(n,8080, stop_event))
    t_connection.start()
    

    t_info = threading.Thread(target=wait_for_info, args=(n,8081,stop_event))
    t_info.start()


    t_connection.join()
    t_info.join()
    
    if play_thread is not None:
        play_thread.join()
        
    if ffmpeg is not None:
        ffmpeg.terminate()
        
    if player is not None:
        player.terminate()
        time.sleep(0.5)
    print("Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    main()