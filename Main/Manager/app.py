# Importações de módulos e bibliotecas necessárias
from enum import Enum
from io import BytesIO
import wave
from flask import Flask, render_template, request, redirect, flash, jsonify, send_file, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os
from flask import request, jsonify
from werkzeug.utils import secure_filename
from youtubesearchpython import VideosSearch
import yt_dlp
import subprocess
import threading
import queue
import time
import socket
import json
import struct
import os
import base64
import signal
import sys
import socket, fcntl, struct
import shutil
from collections import defaultdict


# Inicialização do app Flask, SQLAlchemy e SocketIO
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
socketio = SocketIO(app)
processes = defaultdict(dict)
interruptions = defaultdict(dict)



# Configurações de áudio
BITRATE = "128k"  # Taxa de bits máxima
SAMPLE_RATE = "48000"  # Taxa de amostragem
CHUNCK_SIZE = 960
AUDIO_CHANNELS = "1"  # Mono

NUM_CHANNELS = 3  # Número total de canais


# Função para enviar informações atualizadas para os nós via broadcast UDP
def send_info(nodes, removed=False, suspended=False, test=False):
    dic = {}
    if not removed and not suspended:
        for node_obj in nodes: # Renomeado para evitar conflito com a variável 'node' interna
            mac = node_obj.mac
            area_id = node_obj.area_id
            # Usar db.session.get() é mais eficiente para buscar por chave primária
            area = db.session.get(Areas, area_id) if area_id is not None else None
            channel_id = area.channel_id if area else None
            channel = db.session.get(Channels, channel_id) if channel_id is not None else None
            volume = (area.volume / 50) if area else 1
            
            # O canal normal do nó, baseado na sua área
            node_channel_id = area.channel_id if area else None
            
            header_normal = None
            header_mic = None
            
            #print(f"Node MAC: {mac}, Area ID: {area_id}, Area: {area.name if area else 'None'}, Node Channel ID: {node_channel_id}")

            # Se existir canal normal, lê o arquivo SDP gerado para o canal normal
            if node_channel_id is not None and processes.get(node_channel_id) is not None:
                try:
                    # Verifica se o processo para este canal está realmente ativo
                    # e se o arquivo SDP existe. O 'process' em processes[channel_id] indica isso.
                    if processes[node_channel_id].get('process'):
                        with open(f"session_{node_channel_id}.sdp", "r") as file:
                            header_normal = file.read()
                    else:
                        #print(f"Process for normal channel {node_channel_id} not active or SDP not found for node {mac}.")
                        pass
                except FileNotFoundError:
                    print(f"SDP file session_{node_channel_id}.sdp not found for node {mac}.")
                except Exception as e:
                    print(f"Error reading session_{node_channel_id}.sdp for node {mac}: {e}")
            
            # Lógica para determinar header_mic
            active_interruption_id_for_node = None
            if area:
                # 1. Verificar interrupções ativas associadas diretamente à ÁREA do nó
                for interruption_instance in area.interruptions: # interruption_instance é um objeto Interruptions
                    if interruption_instance.state == "on":
                        # Verifica se o processo de interrupção está realmente no dict de runtime 'interruptions'
                        if interruption_instance.id in interruptions and interruptions[interruption_instance.id].get("process"):
                            active_interruption_id_for_node = interruption_instance.id
                            # print(f"Node {mac} in area '{area.name}' is affected by active interruption ID {active_interruption_id_for_node} (area direct).")
                            break # Encontrou uma interrupção ativa para a área
                        
                # 2. Se não encontrou pela área, e a área tem um canal, verificar interrupções ativas associadas ao CANAL da área
                if active_interruption_id_for_node is None and channel:
                    for interruption_instance in channel.interruptions:
                        if interruption_instance.state == "on":
                             # Verifica se o processo de interrupção está realmente no dict de runtime 'interruptions'
                            if interruption_instance.id in interruptions and interruptions[interruption_instance.id].get("process"):
                                active_interruption_id_for_node = interruption_instance.id
                                # print(f"Node {mac} in area '{area.name}' (via channel '{area.channel.name}') is affected by active interruption ID {active_interruption_id_for_node} (channel of area).")
                                break # Encontrou uma interrupção ativa para o canal da área
            
            if active_interruption_id_for_node is not None:
                try:
                    mic_sdp_file = f"mic_{active_interruption_id_for_node}.sdp"
                    if os.path.exists(mic_sdp_file):
                        with open(mic_sdp_file, "r") as file:
                            header_mic = file.read()
                        # print(f"Successfully read {mic_sdp_file} for node {mac}.")
                    else:
                        print(f"Mic SDP file {mic_sdp_file} not found for node {mac} (interruption ID {active_interruption_id_for_node}).")
                except Exception as e:
                    print(f"Error reading {mic_sdp_file} for node {mac}: {e}")

            dic[mac] = {
                "volume": volume, 
                "channel": node_channel_id, # Canal normal da área do nó
                "header_normal": header_normal, 
                "header_mic": header_mic
            }
            
    elif removed:
        # dic = {} # já inicializado
        for node_obj in nodes:
            mac = node_obj.mac
            dic[mac] = {"removed": True}
            
    elif suspended:
        # dic = {} # já inicializado
        for node_obj in nodes:
            mac = node_obj.mac
            dic[mac] = {"suspended": True}
    
    if test and not removed and not suspended: # Só adiciona 'test' se não for remoção ou suspensão
        for node_obj in nodes:
            mac = node_obj.mac
            if mac in dic: # Garante que a entrada para o mac já existe
                 dic[mac].update({"test": True})
            else: # Caso raro, mas para segurança
                 dic[mac] = {"test": True}
            
    # print("Sending info to nodes:", json.dumps(dic, indent=2)) # Usar indent para melhor leitura no log
            
    msg = json.dumps(dic)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Use a specific broadcast IP if known, otherwise '<broadcast>' might be problematic on some systems/networks.
            # Consider getting the broadcast address of a specific interface if issues persist.
            client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', 8081)) 
        # print(f"Info sent to nodes: {[n.mac for n in nodes]}")
    except Exception as e:
        print(f"Error sending UDP broadcast: {e}")

            

            
    msg = json.dumps(dic)
    # Envia mensagem via broadcast UDP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', 8081))
        
    print("Info sent to nodes:", nodes)


@app.route('/start_interruption/<int:interruption_id>', methods=['POST'])
def start_interruption(interruption_id):
    interruption = Interruptions.query.get(interruption_id)
    if not interruption:
        return jsonify({"error": "Interrupção não encontrada"}), 404

    # Verifica se alguma área associada à interrupção já tem uma interrupção ativa com outro microfone
    for area in interruption.areas:
        for active_interruption in area.interruptions:
            if active_interruption.state == "on" and active_interruption.microphone_id != interruption.microphone_id:
                return jsonify({"error": f"A área '{area.name}' já possui uma interrupção ativa com outro microfone"}), 400

    # Verifica se algum canal associado à interrupção já tem uma interrupção ativa com outro microfone
    for channel in interruption.channels:
        for active_interruption in channel.interruptions:
            if active_interruption.state == "on" and active_interruption.microphone_id != interruption.microphone_id:
                return jsonify({"error": f"O canal '{channel.name}' já possui uma interrupção ativa com outro microfone"}), 400


    print(interruptions)
    
    interruptions[interruption_id] = {
        "process": None,
        "areas": interruption.areas,
        "channels": interruption.channels
    }
    
    # Lógica para iniciar a interrupção (a lógica de início da interrupção deve ser implementada aqui)
    if interruption_id in interruptions:
        interruptions[interruption_id]["process"] = start_ffmpeg_process(interruption_id, str(interruption.microphone_id), ChannelType.VOICE)
    
        if interruptions[interruption_id]["process"] is None:
            return jsonify({"error": "Erro ao iniciar o processo FFmpeg"}), 500
    
    if interruption_id not in interruptions:
        return jsonify({"error": "Erro ao iniciar a interrupção"}), 500
    
    
        # Inicia a interrupção
    interruption.state = "on"
    db.session.commit()
    
    
    
    #mandar info para nodes pertencentes a areas e canais associados à interrupção
    nodes = []
    for area in interruption.areas:
        nodes += area.nodes
    for channel in interruption.channels:
        areas = db.session.query(Areas).filter(Areas.channel_id == channel.id).all()
        for area in areas:
            nodes += area.nodes
            
    while not os.path.exists(f"mic_{interruption_id}.sdp"):
        time.sleep(0.1)        
    
    send_info(nodes)
    
    
    return jsonify({"success": True})


@app.route('/stop_interruption/<int:interruption_id>', methods=['POST'])
def stop_interruption(interruption_id):   

    interruption = Interruptions.query.get(interruption_id)
    if not interruption:
        return jsonify({"error": "Interrupção não encontrada"}), 404


    
    # Verifica se a interrupção está ativa
    if interruption_id in interruptions:
        # Para o processo FFmpeg associado à interrupção
        if interruptions[interruption_id]["process"]:
            interruptions[interruption_id]["process"].terminate()
            interruptions[interruption_id]["process"].wait()
            interruptions[interruption_id]["process"] = None
            
            del interruptions[interruption_id]
            
            
        if os.path.exists(f"mic_{interruption_id}.sdp"):
            os.remove(f"mic_{interruption_id}.sdp")
            
    else:
        return jsonify({"error": "Erro ao parar a interrupção"}), 500
    
    # Para a interrupção (a lógica de parada da interrupção deve ser implementada aqui)
    interruption.state = "off"
    db.session.commit()
    
    nodes = []
    for area in interruption.areas:
        nodes += area.nodes
    for channel in interruption.channels:
        areas = db.session.query(Areas).filter(Areas.channel_id == channel.id).all()
        for area in areas:
            nodes += area.nodes
            
    while os.path.exists(f"mic_{interruption_id}.sdp"):
        time.sleep(0.1)        
    
    send_info(nodes)
    
    return jsonify({"success": True})


@app.route('/delete_interruption/<int:interruption_id>', methods=['DELETE'])
def delete_interruption(interruption_id):
    interruption = Interruptions.query.get(interruption_id)
    if not interruption:
        return jsonify({"error": "Interrupção não encontrada"}), 404

    # Para o processo FFmpeg associado à interrupção
    if interruption_id in interruptions:
        if interruptions[interruption_id]["process"]:
            interruptions[interruption_id]["process"].terminate()
            interruptions[interruption_id]["process"].wait()
            interruptions[interruption_id]["process"] = None
        del interruptions[interruption_id]
        
        if os.path.exists(f"mic_{interruption_id}.sdp"):
            os.remove(f"mic_{interruption_id}.sdp")
            
    # Envia informações para os nós associados à interrupção
    if interruption.state == "on":
    
        nodes = []
        for area in interruption.areas:
            nodes += area.nodes
        for channel in interruption.channels:
            areas = db.session.query(Areas).filter(Areas.channel_id == channel.id).all()
            for area in areas:
                nodes += area.nodes
                
        while os.path.exists(f"mic_{interruption_id}.sdp"):
            time.sleep(0.1)
    

        send_info(nodes)
    
    db.session.delete(interruption)
    db.session.commit()
    

    return jsonify({"success": True})


@app.route('/save_interruption', methods=['POST'])
def save_interruption():
    print("Saving interruption")
    data = request.json
    interruption_name = data.get('name')
    microphone_id = data.get('microphone_id')
    areas_ids = data.get('areas_ids')
    channels_ids = data.get('channels_ids')

    if not interruption_name or not microphone_id:
        return jsonify({"error": "Nome da interrupção e ID do microfone são obrigatórios"}), 400

    # Verifica se a interrupção já existe
    existing_interruption = Interruptions.query.filter_by(name=interruption_name).first()
    if existing_interruption:
        return jsonify({"error": "Interrupção já existe"}), 400

    new_interruption = Interruptions(name=interruption_name, microphone_id=microphone_id, state="off")
    
    # Adiciona as áreas associadas à interrupção
    if areas_ids:
        for area_id in areas_ids:
            area = Areas.query.get(area_id)
            if area:
                new_interruption.areas.append(area)

    # Adiciona os canais associados à interrupção
    if channels_ids:
        for channel_id in channels_ids:
            channel = Channels.query.get(channel_id)
            if channel:
                new_interruption.channels.append(channel)

    db.session.add(new_interruption)
    db.session.commit()
    
    return jsonify({"success": True, "id": new_interruption.id})


@app.route('/add_interruption', methods=['GET'])
def add_interruption():
    microphones = Microphone.query.all()
    channels = Channels.query.all()
    areas = Areas.query.all()
    return render_template('add_interrupt.html', microphones=microphones, channels=channels, areas=areas)


@app.route('/update_microphones', methods=['GET'])
def update_microphones():
    get_mics()
    microphones = Microphone.query.all()
    microphones_list = [
        {"id": mic.id, "name": mic.name, "device": mic.device, "card": mic.card}
        for mic in microphones
    ]
    return jsonify({"success": True, "microphones": microphones_list})


@app.route('/get_microphones', methods=['GET'])
def get_microphones():
    microphones = Microphone.query.all()
    return jsonify([
        {"card": mic.card, "device": mic.device, "name": mic.name} for mic in microphones
    ])

def parse_device_info(line):
    parts = line.split()
    card = None
    device = None
    name = None
    for i, part in enumerate(parts):
        if part == "card":
            card = parts[i + 1].strip(':')  # Remove o ':' após o número do card
        elif part == "device":
            device = parts[i + 1].strip(':')  # Remove o ':' após o número do device
            # Captura o nome do dispositivo após "device X:"
            name = " ".join(parts[i + 2:]).strip()
    return card, device, name

def get_mics():
    # Verifica se o comando 'arecord' está disponível no sistema
    if not shutil.which("arecord"):
        print("Error: 'arecord' command not found. Please install 'alsa-utils'.")
        return []

    # Lista os dispositivos de captura de áudio disponíveis
    cmd = ["arecord", "-l"]
    try:
        output = subprocess.check_output(cmd, text=True)
        lines = output.split('\n')
        devices = Microphone.query.all()  # Dispositivos já no banco de dados
        for line in lines:
            if "card" in line and "device" in line:
                card, device, name = parse_device_info(line)
                print(f"Card: {card}, Device: {device}, Name: {name}")
                # Verifica se o dispositivo já existe no banco de dados
                if not any(d.card == card and d.device == device for d in devices):
                    new_device = Microphone(card=card, device=device, name=name)
                    db.session.add(new_device)
                    db.session.commit()
                    devices.append(new_device)  # Atualiza a lista local de dispositivos
    except subprocess.CalledProcessError as e:
        print(f"Error listing audio devices: {e}")
        return []



############
PLAYLISTraiz_FOLDER = 'Playlists'
UPLOAD_FOLDER = 'Playlists/Songs'

# Ensure directories exist
if not os.path.exists(PLAYLISTraiz_FOLDER):
    os.makedirs(PLAYLISTraiz_FOLDER)
    print(f"Created directory: {PLAYLISTraiz_FOLDER}")
    
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created directory: {UPLOAD_FOLDER}")
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLAYLISTraiz_FOLDER'] = 'Playlists'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
########


@app.route('/toggle_transmission', methods=['POST'])
def toggle_transmission():
    data = request.json
    channel_id = data.get('channel_id')
    state = data.get('state')
    """
    Função para iniciar ou parar a transmissão de um canal.
    :param channel_id: ID do canal a ser controlado.
    :param action: Ação a ser realizada ("start" ou "stop").
    """
    
    if channel_id not in processes:
        return jsonify({'status': 'error', 'message': 'Canal não existe'})
    


    if processes[channel_id]['process']:
        processes[channel_id]['process'].terminate()
        processes[channel_id]['process'].wait()
        processes[channel_id]['process'] = None
        
    if os.path.exists(f"session_{channel_id}.sdp"):
        os.remove(f"session_{channel_id}.sdp")
    
        
    while os.path.exists(f"session_{channel_id}.sdp"):
        time.sleep(0.1)
        
    channel = db.session.query(Channels).filter(Channels.id == channel_id).first()
    if channel.state == 'playing':
        channel.state = 'stopped'
        
        processes[channel_id]['current_playing'] = {"playing": None}
        socketio.emit('song_changed', {'channel': channel_id, 'song': None})
    elif channel.state == 'stopped':
        # Comando FFmpeg para RTP multicast
        
        if not channel:
            return jsonify({'status': 'error', 'message': 'Canal não encontrado'})
        source = channel.source
        _type = channel.type


        # Inicia o processo FFmpeg
        processes[channel_id]['process'] = start_ffmpeg_process(channel_id, source, _type)
        
        if processes[channel_id]['process'] is None:
            return jsonify({'status': 'error', 'message': 'Erro ao iniciar o processo FFmpeg'})
        
        print(f"Canal {channel_id} iniciado")
        
        while not os.path.exists(f"session_{channel_id}.sdp"):
            time.sleep(0.1)
        
        channel.state = 'playing'

        print(f"Transmissão do canal {channel_id} iniciada com sucesso.")
    db.session.commit()
        
    areas = db.session.query(Areas).filter(Areas.channel_id == channel_id).all()
    nodes = []
    for area in areas:
        nodes += area.nodes
    
    send_info(nodes)
    return jsonify({'success': True})








def start_ffmpeg_process(channel, source, _type):
    # Define o endereço de multicast baseado no número do canal
    multicast_address = f"rtp://239.255.{'1' if _type == ChannelType.VOICE else '0'}.{channel}:12345"
    print(f"session_{channel}.sdp")
    print("source: ", source)
    print("type: ", _type)
    
    source = get_source_from_id(_type, source)
    
    if _type != ChannelType.VOICE:
        
        
        if not source:
            print("Source is empty")
            return None
        
        if processes[channel]['process']:
            processes[channel]['process'].terminate()
            processes[channel]['process'].wait()
            processes[channel]['process'] = None
            
        if os.path.exists(f"session_{channel}.sdp"):
            os.remove(f"session_{channel}.sdp")
    
    # Verifica o tipo de transmissão e configura o comando do ffmpeg apropriado
    if _type == ChannelType.VOICE:
        
        print("Channel de Microfone: " + str(channel))
        
        cmd = [
            "ffmpeg",
            "-f", "alsa",
            "-i", f"hw:{source[0]},{source[1]}",  # Dispositivo de captura
            "-vn",  # Sem vídeo
            "-hide_banner",  # Oculta informações de inicialização
            "-ar", SAMPLE_RATE,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ac", AUDIO_CHANNELS,
            "-f", "rtp",
            "-sdp_file", f"mic_{channel}.sdp",
            f"{multicast_address}"
        ]
        

    elif _type == ChannelType.LOCAL:

        # Divide o source em uma lista de músicas
        musicas = [musica.strip() for musica in source.split(",")]

        # Cria um arquivo de playlist temporário para o FFmpeg
        playlist_file_path = f"Playlists/temp_playlist_{channel}.txt"

        songlist = []
        
        with open(playlist_file_path, "w") as playlist_file:
            for musica in musicas:
                duration = get_wav_duration(f"Playlists/Songs/{musica}.wav")
                with app.app_context():
                    song = db.session.query(Songs).filter(Songs.song_hash == musica).first()
                    
                    # Adiciona a música e sua duração à lista
                    songlist.append((song.name, duration))
                playlist_file.write(f"file 'Songs/{musica}.wav'\n")

        # Comando do FFmpeg para reproduzir a playlist
        cmd = [
            "ffmpeg",
            "-stream_loop", "-1",  # Loop infinito
            "-hide_banner",  # Oculta informações de inicialização
            "-f", "concat",  # Formato de entrada como concatenação
            "-re",  # Tempo real
            "-i", playlist_file_path,  # Arquivo de playlist
            "-ar", SAMPLE_RATE,
            "-vn",  # Sem vídeo
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ac", AUDIO_CHANNELS,
            "-f", "rtp",
            "-sdp_file", f"session_{channel}.sdp",
            f"{multicast_address}"
        ]
        
        
    elif _type == ChannelType.STREAMING:
        # Transmissão via streaming com URL proveniente do yt-dlp
        
        ########3
        #source = "https://www.youtube.com/live/YDvsBbKfLPA?si=TdUqXCrxJojjNDns"
        ##############

        
        cmd = [
            "ffmpeg",
            "-i", source,
            "-vn",  # Sem vídeo
            "-hide_banner", # Oculta informações de inicialização
            #"-re",
            "-buffer_size", "4096",
            "-ar", SAMPLE_RATE,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ac", AUDIO_CHANNELS,
            "-f", "rtp",
            "-sdp_file", f"session_{channel}.sdp",
            f"{multicast_address}"
        ]
        
    else:
        return None
    # Inicia o subprocesso do ffmpeg

    # Start FFmpeg subprocess with stderr pipe
    # Start FFmpeg subprocess with stderr pipe
    
    
    print("type: ", _type)

    # Monitor output if LOCAL or STREAMING
    if _type == ChannelType.LOCAL:
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True)
        threading.Thread(target=monitor_ffmpeg_output, args=(process, songlist, channel), daemon=True).start()
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, universal_newlines=True)
        if _type == ChannelType.STREAMING:
            processes[channel]['current_playing'] = get_streaming_name(channel)
    return process



def get_streaming_name(channel):
    # Obter o nome do streaming a partir do banco de dados
    channel = db.session.query(Channels).filter(Channels.id == channel).first()
    if not channel:
        return None
    else:
        print("channel: ", channel)

    stream = db.session.query(Streaming).filter(Streaming.id == channel.source).first()
    if not stream:
        return None
    
    return {"playing": stream.name}

    

########track which song is playing
def hms_to_seconds(t):
    """Convert 'HH:MM:SS.ss' to total seconds."""
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

def monitor_ffmpeg_output(process, songlist, channel):
    current_index = 0
    time_acc = 0
    while current_index < len(songlist):
        current_song, duration_sec = songlist[current_index]
        processes[channel]['current_playing'] = {"playing": current_song}
        socketio.emit('song_changed', {'channel': channel, 'song': current_song})
        print(f"Now playing: {current_song} on channel {channel}")
        next_song = False
        duration_sec += time_acc

        while True:
            if process.poll() is not None:
                print(f"Process on channel {channel} terminated. Exiting thread.")
                return

            line = process.stderr.readline()
            if not line:
                continue  # no output yet

            line = line.strip()

            if "time=" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("time="):
                        current_time_str = part.split("=")[1]
                        current_sec = hms_to_seconds(current_time_str)

                        if current_sec >= duration_sec:
                            print(f"{current_song} finished, moving to next song.")
                            current_index += 1
                            next_song = True
                            time_acc = current_sec
                            if current_index == len(songlist):
                                return  # Done with playlist
                            break
            if next_song:
                break



def get_wav_duration(file_path):
    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
    return duration
#########


def create_default_channels():
    
    # Verifica se o número de canais no banco é diferente do esperado
    if db.session.query(Channels).count() != NUM_CHANNELS:
        db.session.query(Channels).delete()
        db.session.commit()
        # Cria os canais padrão com tipo LOCAL e fonte "default"
        for i in range(1, NUM_CHANNELS+1):
            if os.path.exists(f"session_{i}.sdp"):
                os.remove(f"session_{i}.sdp")
            new_channel = Channels(
                name=f"Channel {i}",
                type=ChannelType.LOCAL,
                state="stopped",
                source=None,
            )
            db.session.add(new_channel)
            db.session.commit()
            processes[new_channel.id] = {"process": None, "current_playing": {"playing": None}}
            print(f"{new_channel.name} started")

    else:
        for channel in db.session.query(Channels).all():
            if os.path.exists(f"session_{channel.id}.sdp"):
                os.remove(f"session_{channel.id}.sdp")
            index = channel.id
            processes[index] = {"process": None, "current_playing": {"playing": None}}  # Uncommented to start the process
            print(f"Channel {channel.id} started")
            
            

    for channel in db.session.query(Channels).all():
        channel.state = "stopped"
    db.session.commit()
    
    send_info(Nodes.query.all())  # Envia informações iniciais para os nós
            
    return processes


def convert_id_source(_type, id):
    if _type==ChannelType.STREAMING:
        stream = db.session.query(Streaming).filter(Streaming.id == id).first()
        if not stream:
            return None
        source = stream.url
        
    elif _type == ChannelType.LOCAL:
        song = db.session.query(Songs).filter(Songs.id == id).first()
        if not song:
            return None
        source = song.song_hash
        
    elif _type == ChannelType.VOICE:
        mic = db.session.query(Microphone).filter(Microphone.id == id).first()
        if not mic:
            return None
        source = f"{mic.card},{mic.device}"
    else:
        return None
    
    return source


def get_source_from_id(_type, list_ids):
    
    list_ids = str(list_ids)
    ids = list_ids.split(",")
    sources = list(map(lambda id: convert_id_source(_type, id), ids))
    sources = list(filter(lambda source: source is not None, sources))
    if len(sources) == 0:
        return None
    
    if _type == ChannelType.LOCAL:
        sources = list(map(lambda source: source.replace(" ", "_"), sources))
        sources = ",".join(sources)
    elif _type == ChannelType.STREAMING:
        try:
            # Comando para obter a URL direta do stream
            ytdl_cmd = [
            "yt-dlp",
            "-g",
            "--no-check-certificates", 
            "--socket-timeout", "15", 
            sources[0]
            ]
            direct_url = subprocess.check_output(ytdl_cmd, text=True).strip()
        except subprocess.TimeoutExpired:
            print("Timeout ao obter URL.")
            return None
        except Exception as e:
            print(f"Erro ao obter URL: {e}")
            return None
        sources = direct_url
    elif _type == ChannelType.VOICE:
        print("sources: ", sources)
        sources = sources[0].split(",")
        if len(sources) != 2:
            return None
        return (sources[0], sources[1])

    else:
        return None
    
    print("sources: ", sources)
    
    
    return sources
        
        


    
@app.route('/save_channel_configs', methods=['POST'])
def save_channel_configs():
    data = request.json
    channel_id = data.get('channel_id')
    channel_type = data.get('channel_type').upper()
    channel_reproduction = data.get('channel_reproduction')

    # Processa os dados recebidos
    print(f"ID do canal: {channel_id}")
    print(f"Tipo de transmissão: {channel_type}")
    print(f"Reprodução: {channel_reproduction}")
        
    
    #alterar na base de dados o tipo de transmissão do canal e o respetivo microfone e reiniciar o processo
    channel = db.session.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        return jsonify({"error": "Canal não encontrado"}), 404
    channel.type = channel_type
    
    if channel_reproduction == None:
        channel.source = None
        db.session.commit()
        
        if processes[channel.id]['process'] is not None:
            processes[channel.id]['process'].terminate()
            processes[channel.id]['process'].wait()
            processes[channel.id]['process'] = None
            
        if os.path.exists(f"session_{channel_id}.sdp"):
            os.remove(f"session_{channel_id}.sdp")
    
            
        while os.path.exists(f"session_{channel_id}.sdp"):
            time.sleep(0.1) 
            
        channel = db.session.query(Channels).filter(Channels.id == channel_id).first()
        channel.state = 'stopped'
        db.session.commit()
        print("Canal parado")
    else:
    
        # Reinicia o processo do canal com as novas configurações
        if channel_type == "STREAMING":
            stream = db.session.query(Streaming).filter(Streaming.name == channel_reproduction).first()
            if not stream:
                return jsonify({"error": "Streaming não encontrado"}), 404
            channel_source = stream.id
            channel.source = channel_source
            db.session.commit()
            # Reinicia o processo do canal
        elif channel_type == "LOCAL":
            #percorrer conteudo de channel_reproduction que está do genero "PLAYLIST:playlist1 SONG:musica1 PLAYLIST:playlist2 PLAYLIST:playlist3 SONG:musica2"
            #se for uma musica adicionar a musicas se for uma playlist ir á base de dados obter as musicas
            
            
            musicas = []
            for item in channel_reproduction.split(";"):
                if item.startswith("PLAYLIST:"):
                    playlist_name = item.split(":")[1]
                    playlist = db.session.query(Playlist).filter(Playlist.name == playlist_name).first()
                    if playlist:
                        for song in playlist.songs:
                            musicas.append(str(song.id))
                        


                elif item.startswith("SONG:"):
                    song_name = item.split(":")[1]
                    song = db.session.query(Songs).filter(Songs.name == song_name).first()
                    if song:
                        musicas.append(str(song.id))
                        
            print("Musicas: ", musicas)
                    
            channel_source = ", ".join(musicas)
            channel.source = channel_source
            db.session.commit()
            
        else:
            print("Tipo de canal inválido")    
            return jsonify({"error": "Tipo de canal inválido"}), 400
    

    
        if processes[channel.id]['process'] is not None:
            processes[channel.id]['process'].terminate()
            processes[channel.id]['process'].wait()
            processes[channel.id]['process'] = None
            processes[channel.id]['process'] = start_ffmpeg_process(channel.id, channel_source, channel_type)

                
            if processes[channel.id]['process'] is None:
                return jsonify({'status': 'error', 'message': 'Erro ao iniciar o processo FFmpeg'})
            
            while not os.path.exists(f"session_{channel.id}.sdp"):
                time.sleep(0.1)
                
    areas = db.session.query(Areas).filter(Areas.channel_id == channel_id).all()
    nodes = []
    for area in areas:
        nodes += area.nodes
            
            
    print("sending info to nodes")
    print(nodes)
    
    send_info(nodes)
    
    

    # Salve as configurações no banco de dados ou tome outras ações necessárias
    return jsonify({"success": True}), 200




# Definição dos modelos de dados com SQLAlchemy

# Modelo para "Áreas"
class Areas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nodes = db.relationship('Nodes', backref='area', lazy=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=True)
    volume = db.Column(db.Integer, nullable=False, default=50)

    def __repr__(self):
        return f'<Area {self.id}: {self.name}>'

# Modelo para "Nós" (Nodes)
class Nodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    mac = db.Column(db.String(200), unique=True, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    connected = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Node {self.id}: {self.name}>'
    
    
class Microphone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    device = db.Column(db.String(200), nullable=False)
    card = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Microphone {self.id}: {self.name}>'

# Enum para definir os tipos de canais permitidos
class ChannelType(str, Enum):
    LOCAL = "LOCAL"
    STREAMING = "STREAMING"
    VOICE = "VOICE"


#################################################################################
#################################################################################

# Tabela associativa para o relacionamento muitos-para-muitos
playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True)
)

# Classe Songs
class Songs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False,unique=True)
    song_hash = db.Column(db.String(200), nullable=False, unique=True)

    def __repr__(self):
        return f'<Song {self.id}: {self.name}>'

# Classe Playlist
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    songs = db.relationship(
        'Songs',
        secondary=playlist_songs,
        backref='playlist',
        lazy='subquery'
    )

    def __repr__(self):
        return f'<Playlist {self.id}: {self.name}>'

#################################################################################
#################################################################################


# Modelo para canais
class Channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    type = db.Column(db.Enum(ChannelType), nullable=False)
    source = db.Column(db.String(200), nullable=True)
    state = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Channel {self.id}: {self.name}>'
    
    
# Tabela associativa para Interruptions e Areas
interruption_areas = db.Table('interruption_areas',
    db.Column('interruption_id', db.Integer, db.ForeignKey('interruptions.id'), primary_key=True),
    db.Column('area_id', db.Integer, db.ForeignKey('areas.id'), primary_key=True)
)

# Tabela associativa para Interruptions e Channels
interruption_channels = db.Table('interruption_channels',
    db.Column('interruption_id', db.Integer, db.ForeignKey('interruptions.id'), primary_key=True),
    db.Column('channel_id', db.Integer, db.ForeignKey('channels.id'), primary_key=True)
)
    
class Interruptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    microphone_id = db.Column(db.Integer, db.ForeignKey('microphone.id'), nullable=False)  # Foreign key para Microphone
    state = db.Column(db.String(200), nullable=False)

    # Relacionamento com a tabela Microphone
    microphone = db.relationship('Microphone', backref='interruptions', lazy=True)

    # Relacionamento com Areas (muitos-para-muitos)
    areas = db.relationship('Areas', secondary=interruption_areas, backref='interruptions')

    # Relacionamento com Channels (muitos-para-muitos)
    channels = db.relationship('Channels', secondary=interruption_channels, backref='interruptions')

    def __repr__(self):
        return f'<Interruption {self.id}: {self.name}>'


###############3
class Streaming(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __init__(self, name, url):
        self.name = name
        self.url = url
        

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.id}: {self.name}>'

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('custom_login'))

@app.route('/index', methods=['GET'])
def dashboard(): 
    nodes = Nodes.query.order_by(Nodes.id).all()
    areas = Areas.query.order_by(Areas.id).all()
    channels = Channels.query.order_by(Channels.id).all()
    microphones = Microphone.query.all()
    interruptions = Interruptions.query.all()
    interruptions_areas = db.session.query(interruption_areas).all()
    interruptions_channels = db.session.query(interruption_channels).all()
    for area in areas:
        area.current_channel = next((channel.name for channel in channels if channel.id == area.channel_id), None)
    return render_template('index.html', nodes=nodes, channels=channels, areas=areas, microphones=microphones, interruptions=interruptions, interruptions_areas=interruptions_areas, interruptions_channels=interruptions_channels)



@app.route('/login', methods=['GET', 'POST'])
def custom_login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            return jsonify({"success": True, "message": "Login successful", "redirectUrl": "/index"}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    return render_template("login.html")


@app.route('/register', methods=['GET','POST'])
def custom_register():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"success": True, "message": "Registration successful"}), 201
    return render_template('register.html')


@app.route('/logout', methods=['GET'])
def logout():
    return redirect(url_for('custom_login'))


# Rota para deleção de um nó específico
@app.route('/delete/<int:id>')
def delete(id):
    node_to_delete = Nodes.query.get_or_404(id)
    try:
        db.session.delete(node_to_delete)
        db.session.commit()
        socketio.emit('update', {'action': 'delete', 'id': id})
        send_info([node_to_delete], removed=True)
        return redirect('/index')
    except:
        return 'Houve um problema ao remover o nó'
    
# Rota para atualizar a lista de nós (simples redirecionamento)
@app.route('/refresh_nodes', methods=['POST'])
def refresh_nodes():
    return redirect('/index')

# Rota para atualização dos dados de um nó
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    node = Nodes.query.get_or_404(id)
    if request.method == 'POST':
        node.name = request.form['name']
        try:
            db.session.commit()
            socketio.emit('update', {'action': 'update', 'id': id, 'name': node.name})
            return redirect('/index')
        except:
            return 'Houve um problema ao atualizar a tarefa'
    else:
        return render_template('update.html', node=node)


# Função que detecta novos nós na rede
def detect_new_nodes(stop_event, msg_buffer):
    time.sleep(0.1)
    # Cria um socket para escutar na porta 8080
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', 8080))
        server_socket.settimeout(2) 
        msg_buffer.put("Detection started")
        while not stop_event.is_set():
            try:
                data, addr = server_socket.recvfrom(1024)
                print("Received data from", addr)
            except socket.timeout:
                continue
            data = data.decode('utf-8')
            if data:
                # This would go in the Manager's app.py detect_new_nodes function
                # Add this inside the try block that handles incoming data

                if data.startswith("SHUTDOWN"):
                    _, node_name, node_mac = data.split(',')
                    print(f"Received shutdown notification from {node_name} ({node_mac})")
                    
                    with app.app_context():
                        node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                        if node:
                            node.connected = False
                            db.session.commit()
                            socketio.emit('update', {
                                'action': 'update_status',
                                'id': node.id,
                                'connected': False
                            })
                            msg_buffer.put(f"Node {node_name} disconnected")
                        else:
                            continue  # Node not found, skip to next iteration
                else:
                    # Envia confirmação para o nó
                    server_socket.sendto(b"OK", addr)
                    node_name, node_mac = data.split(',')
                    node_ip = addr[0]

                    try:
                        with app.app_context():
                            if db.session.query(Nodes).filter(Nodes.mac == node_mac).first():
                                raise Exception("MAC already in use")
                            node_name = node_name.upper()
                            node = Nodes(name=node_name, mac=node_mac, ip=node_ip, connected=True)  #remover este area_id = 1
                            db.session.add(node)
                            db.session.commit()
                        
                        socketio.emit('update', {
                            'action': 'add',
                            'id': node.id,
                            'name': node.name,
                            'mac': node.mac,
                            'ip': node.ip
                        })
                        msg_buffer.put(f"Node {node_name} connected")
                        
                    except Exception as e:
                        if str(e) == "Limit of nodes with the same name reached":
                            msg_buffer.put("Limit of nodes with the same name reached")
                            server_socket.sendto(b"Limit of nodes with the same name reached", addr)
                        elif str(e) == "MAC already in use":
                            with app.app_context():
                                node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                                node.ip = node_ip
                                node.connected = True
                                db.session.commit()

                                node_name = node.name
                            print(f"Node {node.name} already exists, updating IP {node_ip}")
                        else:
                            msg_buffer.put(f"Error: {e}")
                            server_socket.sendto(b"Error " + str(e).encode('utf-8'), addr)

                with app.app_context():
                    node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                    send_info([node])
                    socketio.emit('reload_page', namespace='/')  # Envia comando para recarregar a página

# Rota para renomear um nó
@app.route('/rename_node/<int:id>', methods=['POST'])
def rename_node(id):
    new_name = request.form['name']
    try:
        node = Nodes.query.get_or_404(id)
        node.name = new_name
        db.session.commit()
        socketio.emit('reload_page', namespace='/')
        return redirect('/index')
    except Exception as e:
        return str(e), 500

# Rota para adicionar uma nova área
@app.route('/add_area', methods=['POST'])
def add_area():
    data = request.json  
    area_name = data.get('name')
    if not area_name:
        return jsonify({"error": "Nome da área é obrigatório"}), 400
    if Areas.query.filter_by(name=area_name).first():
        return jsonify({"error": "Área já existe"}), 400
    try:
        new_area = Areas(name=area_name, volume=50)
        db.session.add(new_area)
        db.session.commit()
        socketio.emit('reload_page', namespace='/index')
        return jsonify({"success": True, "id": new_area.id, "name": new_area.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para remover uma área
@app.route('/remove_area', methods=['POST'])
def remove_area():
    area_name = request.form.get('name')
    if not area_name:
        flash("Area name is required", "error")
        return jsonify({"error": "Area name is required"}), 400
    try:
        area = Areas.query.filter_by(name=area_name).first()
        if not area:
            flash("Area not found", "error")
            return jsonify({"error": "Area not found"}), 404
        
        print(f"Removing area: {area_name} with ID: {area.id}")
        # Remove a associação dos nós à área antes de removê-la
        nodes_in_area = Nodes.query.filter_by(area_id=area.id).all()
        for node in nodes_in_area:
            node.area_id = None  
            db.session.add(node)

        db.session.delete(area)
        db.session.commit()
        send_info(nodes_in_area)
        flash(f"Area {area_name} removed", "success")
        
        return redirect('/index')
    except Exception as e:
        flash(str(e), "error")
        return jsonify({"error": str(e)}), 500

# Rota para atualizar o volume de uma área
@app.route('/update_volume', methods=['POST'])
def update_volume():
    area_name = request.form.get('name')
    new_volume = float(request.form.get('volume', 0))
    area = Areas.query.filter_by(name=area_name).first()
    if not area:
        flash("Area not found", "error")
        return redirect('/index')
    try:
        area.volume = new_volume
        print(f"Volume updated to {new_volume} for area {area_name}")
        db.session.commit()
        send_info(Nodes.query.filter_by(area_id=area.id).all())
        return redirect('/index')
    except Exception as e:
        return redirect('/index')

# Rota para obter nós que não estão associados a nenhuma área
@app.route('/get_free_nodes')
def get_nodes():
    nodes = Nodes.query.filter_by(area_id=None).all()
    return jsonify([{"id": node.id, "name": node.name} for node in nodes])

# Rota para associar um nó a uma área específica
@app.route('/associate_node', methods=['POST'])
def associate_node():
    data = request.get_json()
    zone_name = data.get("zone_name")
    node_id = data.get("node_id")
    # Busca a área e o nó no banco de dados
    area = Areas.query.filter_by(name=zone_name).first()
    node = Nodes.query.get(node_id)
    if not area or not node:
        return jsonify({"success": False, "error": "Zona ou nó inválido"}), 400
    if node.area_id:
        return jsonify({"success": False, "error": "Este nó já está associado a uma zona!"}), 400

    # Realiza a associação e salva no banco de dados
    node.area_id = area.id
    db.session.commit()

    socketio.emit('reload_page', namespace='/')
    return jsonify({"success": True})

# Rota para adicionar uma coluna (nó) a uma zona (área)
@app.route("/add_column_to_zone", methods=["POST"])
def add_column_to_zone():
    data = request.get_json()
    zone_name = data.get("zone_name")
    column_name = data.get("column_name")
    
    if not zone_name or not column_name:
        return jsonify({"error": "Zona e coluna são obrigatórias"}), 400

    area = Areas.query.filter_by(name=zone_name).first()
    column = Nodes.query.filter_by(name=column_name).first()
    if not area:
        return jsonify({"error": "Zona não encontrada"}), 404
    if not column:
        return jsonify({"error": "Coluna não encontrada"}), 404
    if column.area_id:
        return jsonify({"error": "Essa coluna já está associada a outra zona"}), 400

    column.area_id = area.id
    print(f"Column {column_name} associated with zone {zone_name}")
    db.session.commit()
    send_info([column])
    socketio.emit('reload_page', namespace='/index')
    return jsonify({"success": "Coluna associada com sucesso!"}), 200




# Rota para remover uma coluna de uma zona
@app.route("/remove_column_from_zone", methods=["POST"])
def remove_column_from_zone():
    data = request.get_json()
    if not data or "zone_name" not in data or "column_name" not in data:
        return jsonify({"error": "Zone and column are required"}), 400
    zone_name = data["zone_name"]
    column_name = data["column_name"]
    area = Areas.query.filter_by(name=zone_name).first()
    if not area:
        return jsonify({"error": "Zone not found"}), 404
    column = Nodes.query.filter_by(name=column_name, area_id=area.id).first()
    if not column:
        return jsonify({"error": "Column not found"}), 404
    try:       
        column.area_id = None  
        db.session.commit()
        send_info([column])
        print(f"Column {column_name} removed from zone {zone_name}")
        socketio.emit('reload_page', namespace='/index')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_names_from_ids(channel_type, source):
    if channel_type == ChannelType.LOCAL:
        song_ids = source.split(",")
        songs = db.session.query(Songs).filter(Songs.id.in_(song_ids)).all()
        return [song.name for song in songs]
    elif channel_type == ChannelType.STREAMING:
        stream = db.session.query(Streaming).filter(Streaming.id == source).first()
        return [stream.name] if stream else []
    elif channel_type == ChannelType.VOICE:
        mic = db.session.query(Microphone).filter(Microphone.id == source).first()
        return [mic.name] if mic else []
    else:
        return []




@app.route('/edit_channels')
def edit_channels():
    channel_id = request.args.get('channel_id', type=int)
    channel = Channels.query.get_or_404(channel_id)

    playlists = Playlist.query.all()
    playlist_songs = {
        playlist.name: [song.name for song in playlist.songs]
        for playlist in playlists
    }
    all_songs = ",".join(str(song.id) for song in Songs.query.all())
    all_songs = get_names_from_ids(ChannelType.LOCAL, all_songs) 
    streamings = Streaming.query.all()
    streaming_sources = [streaming.name for streaming in streamings]

    associated_stream = None
    associated_songs = []
    if channel.source:
        if channel.type == ChannelType.LOCAL:
            associated_songs = get_names_from_ids(channel.type, channel.source)
            
        elif channel.type == ChannelType.STREAMING:
            associated_stream_id = channel.source
            associated_stream = Streaming.query.get(associated_stream_id).name if associated_stream_id else None
            

    return render_template(
        'edit_channels.html',
        channel=channel,
        playlists=playlist_songs.keys(),
        playlist_songs=playlist_songs,
        all_songs=all_songs,
        streaming_sources=streaming_sources,
        associated_songs=associated_songs,  # Passa as músicas associadas ao canal
        associated_stream=associated_stream,  # Passa o streaming associado ao canal
        channel_type=channel.type,
        channel_source=channel.source
    )
    
    
    
@app.route('/test-device/<int:node_id>', methods=['POST'])
def test_device(node_id):
    """
    Função para testar um dispositivo enviando um som de teste (pi) por 5 segundos.
    """
    node = Nodes.query.get(node_id)
    if not node:
        return jsonify({"error": "Dispositivo não encontrado"}), 404

    # Configuração do tom de teste
    test_tone_frequency = 1000  # Frequência do tom em Hz
    test_duration = 5  # Duração do teste em segundos
    multicast_address = f"rtp://239.255.2.{node_id}:12345"  # Endereço multicast para o teste
    
    
    send_info([node], test=True)



    return jsonify({"success": True, "message": "Teste concluído com sucesso"}), 200

@app.route('/update_channel_name/<int:channel_id>', methods=['POST'])
def update_channel_name(channel_id):
    new_name = request.form.get('channel_name')
    if not new_name:
        return "Nome inválido", 400



    # Recupera o canal
    channel = Channels.query.get_or_404(channel_id)
    old_name = channel.name
    channel.name = new_name

    try:
        # Atualiza o nome no banco de dados
        db.session.commit()

        # Emite um evento para a atualização do nome na interface
        socketio.emit('update_channel_names', {'new_name': new_name, 'old_name': old_name}, namespace='/')

        return redirect(url_for('edit_channels', channel_id=channel_id))
    
    except Exception as e:
        return f"Erro ao atualizar o nome do canal: {e}", 500



# Rota para verificar se o nome do canal já existe
@app.route('/check_channel_name', methods=['POST'])
def check_channel_name():
    data = request.json
    new_name = data.get('name')
    channel_id = data.get('channel_id')  # Opcional: ignorar o próprio canal

    if not new_name:
        return jsonify({'exists': False})

    existing_channel = Channels.query.filter(Channels.name == new_name).first()

    # Se existir canal com o mesmo nome E for diferente do canal atual
    if existing_channel and existing_channel.id != channel_id:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})




# Rota para atualizar o canal associado a uma área
@app.route('/update_area_channel', methods=['POST'])
def update_area_channel():
    area_name = request.form.get('name')
    new_channel_id = request.form.get('channel_id')
    print(f"Updating channel for area {area_name} to {new_channel_id}")
    area = Areas.query.filter_by(name=area_name).first()
    if not area:
        flash("Area not found", "error")
        return redirect('/index')
    try:
        area.channel_id = new_channel_id
        print(f"Channel updated to {new_channel_id} for area {area_name}")
        db.session.commit()
        send_info(Nodes.query.filter_by(area_id=area.id).all())
        socketio.emit('reload_page', namespace='/')
        return redirect('/index')
    except Exception as e:
        flash(str(e), "error")
        socketio.emit('reload_page', namespace='/')
        return redirect('/index')







@app.route('/secundaria')
def secundaria():
    playlists = Playlist.query.all()  
    Streamings = Streaming.query.all()
    songs = Songs.query.all()
    Microphones = Microphone.query.all()
    return render_template('secundaria.html', playlists=playlists, streamings=Streamings, songs=songs, microfones=Microphones)


@app.route('/save_stream_url', methods=['POST'])
def save_stream_url():
    try:
        data = request.json
        stream_name = data.get('stream_name')
        stream_url = data.get('stream_url')

        if not stream_name or not stream_url:
            return jsonify({"error": "Nome e URL são obrigatórios"}), 400

        # Validação adicional do URL
        if not stream_url.startswith("http://") and not stream_url.startswith("https://"):
            return jsonify({"error": "URL inválido"}), 400
        
        if Streaming.query.filter_by(name=stream_name).first():
            return jsonify({"error": "Stream name already exists"}), 400
        

        
        # Salvar no banco de dados
        new_stream = Streaming(name=stream_name, url=stream_url)
        db.session.add(new_stream)
        db.session.commit()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    




################3
# playlist
####################

import hashlib


# Gera um hash único baseado no conteúdo ou metadados da música
def generate_hash_name(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


# Rota para obter todas as músicas
@app.route('/songs', methods=['GET'])
def get_songs():
    songs = Songs.query.order_by(Songs.id).all()
    return jsonify([{"id": song.id, "name": song.name} for song in songs])




# Função para adicionar novas músicas
@app.route('/add_songs', methods=['POST'])
def add_songs():
    files = request.files.getlist('files[]')
    print("files: ", files)
    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    # Chama a função para salvar as músicas
    response = save_songs(files)
    return jsonify(response[0]), response[1]


def save_songs(files):
    if not files:
        print("Arquivos de música são obrigatórios")
        return {"error": "Arquivos de música são obrigatórios"}, 400

    if not files or all(file.filename == '' for file in files):
        print("Nenhum arquivo selecionado")
        return {"error": "Nenhum arquivo selecionado"}, 400

    added_songs = []
    errors = []

    for file in files:
        if not allowed_file(file.filename):
            errors.append({"file": file.filename, "error": "Formato de arquivo não suportado"})
            continue

        song_name = os.path.splitext(file.filename)[0]
        print("song_name: ", song_name)
        if not song_name:
            errors.append({"file": file.filename, "error": "Nome da música é obrigatório"})
            continue

        if Songs.query.filter_by(name=song_name).first():
            errors.append({"file": file.filename, "error": "Já existe uma música com esse nome"})
            continue

        try:
            # Salvar o arquivo original
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)

            # Se o arquivo não for .wav, converte para .wav usando ffmpeg
            ext = os.path.splitext(filename)[1].lower()
            if ext != '.wav':
                wav_filename = f"{song_name}.wav"
                wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
                print("wav_path: ", wav_path)
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", original_path, wav_path],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao converter o arquivo: {e.stderr.decode()}")
                    errors.append({"file": file.filename, "error": "Erro ao converter o arquivo para .wav"})
                    os.remove(original_path)
                    continue

                # Remover o arquivo original (opcional)
                os.remove(original_path)
            else:
                wav_path = original_path

            song_hash = generate_hash_name(wav_path)
            wav_filename = f"{song_hash}.wav"
            print("song_hash: ", song_hash)

            existing_song = Songs.query.filter_by(song_hash=song_hash).first()
            if existing_song:
                os.remove(wav_path)
                print(f"Já existe essa música: {existing_song.name}")
                errors.append({"file": file.filename, "error": f"Já existe essa música: {existing_song.name}"})
                continue
            else:
                if os.path.exists(wav_path):
                    new_wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
                    os.rename(wav_path, new_wav_path)
                    wav_path = new_wav_path
                else:
                    print("Arquivo wav não encontrado")
                    errors.append({"file": file.filename, "error": "Arquivo wav não encontrado"})
                    continue

            # Salvar no banco de dados
            new_song = Songs(name=song_name, song_hash=song_hash)
            db.session.add(new_song)
            db.session.commit()

            print("Nova música adicionada:", new_song.name)
            added_songs.append({"id": new_song.id, "name": new_song.name})
        except Exception as e:
            errors.append({"file": file.filename, "error": str(e)})

    response = {"success": True, "added_songs": added_songs}
    if errors:
        response["errors"] = errors

    return response, 200 if added_songs else 400

# Rota para editar uma música
@app.route('/update_song/<int:song_id>', methods=['POST'])
def update_song(song_id):
    # Recupera o novo nome da música enviado pelo frontend
    new_name = request.json.get('new_name')
    if not new_name:
        return jsonify({"error": "O novo nome da música é obrigatório"}), 400
    
    # Verifica se o novo nome já existe
    existing_song = Songs.query.filter_by(name=new_name).first()
    if existing_song and existing_song.id != song_id:
        return jsonify({"error": "Já existe uma música com esse nome"}), 400

    # Verifica se a música existe no banco de dados
    song = Songs.query.get(song_id)
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404

    # Atualiza o nome da música
    try:
        song.name = new_name
        db.session.commit()
        return jsonify({"success": True, "id": song.id, "name": song.name}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Rota para excluir uma música
@app.route('/delete_song/<string:song_name>', methods=['DELETE'])
def delete_song(song_name):
    print(f"Eliminar música: {song_name}")
    song = Songs.query.filter_by(name=song_name).first()
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404
    
    try:
        # Verificar se a música está associada a algum canal
        channels = Channels.query.filter(Channels.source.like(f"%{song.id}%"), Channels.type == ChannelType.LOCAL).all()
        for channel in channels:
            # Remover a música da lista de fontes do canal
            sources = channel.source.split(",")
            sources = [src for src in sources if src != str(song.id)]
            channel.source = ",".join(sources) if sources else None
            db.session.commit()
            
            if channel.state == "playing":
                # Se o canal estiver tocando, reinicie o canal
                
                
                print(processes)
                
                #stop ffmpeg process
                if processes[channel.id]["process"] is not None:
                    processes[channel.id]["process"].terminate()
                    processes[channel.id]["process"].wait()
                    processes[channel.id]["process"] = None
                
                if channel.source:
                    processes[channel.id]["process"] = start_ffmpeg_process(channel.id, channel.source, channel.type)
                else:
                    channel.state = "stopped"
                    db.session.commit()
                    
                    
                print(f"Canal {channel.name} reiniciado após remoção da música.")
                
                

        # Remover o arquivo da música
        song_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{song.song_hash}.wav")
        if os.path.exists(song_path):
            os.remove(song_path)
        else:
            print(f"Aviso: Ficheiro '{song_path}' não encontrado. A eliminar só da base de dados.")

        # Remover a música do banco de dados
        db.session.delete(song)
        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

    

@app.route('/playlists', methods=['GET'])
def get_playlists():
    playlists = Playlist.query.all()
    return jsonify([{"id": playlist.id, "name": playlist.name} for playlist in playlists])

# add playlist

@app.route('/add_playlist', methods=['POST'])
def add_playlist():
    data = request.json
    playlist_name = data.get('name')

    if not playlist_name:
        return jsonify({"error": "Nome da playlist é obrigatório"}), 400

    if Playlist.query.filter_by(name=playlist_name).first():
        return jsonify({"error": "Playlist already exists"}), 400

    try:
        # Criar a playlist no banco de dados
        new_playlist = Playlist(name=playlist_name)
        db.session.add(new_playlist)
        db.session.commit()


        return jsonify({"success": True, "id": new_playlist.id, "name": new_playlist.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# delete playlist
@app.route('/delete_playlist/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404
    try:
        db.session.delete(playlist)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#edit playlist NAME
@app.route('/edit_playlist_by_name', methods=['POST'])
def edit_playlist_by_name():
    data = request.json
    current_name = data.get('current_name')
    new_name = data.get('new_name')

    if not current_name or not new_name:
        return jsonify({"error": "Os nomes atual e novo são obrigatórios"}), 400

    # Busca a playlist pelo nome atual
    playlist = Playlist.query.filter_by(name=current_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    try:
        # Atualiza o nome da playlist
        playlist.name = new_name
        db.session.commit()
        return jsonify({"success": True, "id": playlist.id, "name": playlist.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# edit playlist -> html


@app.route('/edit_playlist/<int:playlist_id>', methods=['GET'])
def edit_playlist(playlist_id):
    # Busca a playlist pelo ID
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return "Playlist não encontrada", 404

    # Busca as músicas da playlist e todas as músicas disponíveis
    playlist_name = playlist.name
    playlist_songs = [song.name for song in playlist.songs]  # Músicas na playlist
    all_songs = [song.name for song in Songs.query.all()]  # Todas as músicas disponíveis

    return render_template(
        'edit_playlist.html',
        playlist_name=playlist_name,
        playlist_songs=playlist_songs,
        all_songs=all_songs
    )

@app.route('/remove_song_from_playlist', methods=['POST'])
def remove_song_from_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    song_name = data.get('song_name')

    if not playlist_name or not song_name:
        return jsonify({"error": "Nome da playlist e da música são obrigatórios"}), 400

    # Busca a playlist e a música no banco de dados
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    song = Songs.query.filter_by(name=song_name).first()

    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404

    try:
        # Remove a música da playlist
        if song in playlist.songs:
            playlist.songs.remove(song)
            db.session.commit()
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Música não está na playlist"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/add_song_to_playlist', methods=['POST'])
def add_song_to_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    song_name = data.get('song_name')

    if not playlist_name or not song_name:
        return jsonify({"error": "Nome da playlist e da música são obrigatórios"}), 400

    # Busca a playlist e a música no banco de dados
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    song = Songs.query.filter_by(name=song_name).first()

    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404

    try:
        # Adiciona a música à playlist
        if song not in playlist.songs:
            playlist.songs.append(song)
            db.session.commit()

            # Copiar o arquivo da música para a pasta da playlist
            song_path = os.path.join(app.config['PLAYLISTraiz_FOLDER'], f"{song.name}.wav")
            playlist_folder = os.path.join(app.config['PLAYLISTraiz_FOLDER'], playlist_name)
            if os.path.exists(song_path):
                shutil.copy(song_path, playlist_folder)

            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Música já está na playlist"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/import_playlist', methods=['POST'])
def import_playlist():
    playlist_name = request.form.get('playlist_name')
    files = request.files.getlist('files[]')  # Obtém os arquivos enviados
    print("files: ", files)

    if not playlist_name or not files:
        return jsonify({"error": "Nome da playlist e arquivos de música são obrigatórios"}), 400

    # Verifica se a playlist existe
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    # Salva as músicas usando a função save_songs
    response, status_code = save_songs(files)
    if status_code != 200:
        return jsonify(response), status_code

    # Adiciona as músicas salvas à playlist
    added_songs = response.get("added_songs", [])
    for song_data in added_songs:
        song = Songs.query.get(song_data["id"])
        if song and song not in playlist.songs:  # Fix: Replace '&&' with 'and'
            playlist.songs.append(song)

    db.session.commit()
    return jsonify({"success": True, "playlist_name": playlist_name, "added_songs": added_songs}), 200


@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    updated_songs = data.get('songs')

    if not playlist_name or updated_songs is None:
        return jsonify({"error": "Nome da playlist e lista de músicas são obrigatórios"}), 400

    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    try:
        playlist.songs = []
        db.session.commit()
        for song_name in updated_songs:
            song = Songs.query.filter_by(name=song_name).first()
            if song:
                playlist.songs.append(song)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/playlist_order/<playlist_name>')
def playlist_order(playlist_name):
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    ordered_songs = [song.name for song in playlist.songs]
    return jsonify({"songs": ordered_songs})


@app.route('/export_conf', methods=['GET'])
def export_conf():
    nodes = Nodes.query.all()
    areas = Areas.query.all()
    config_data = {
        "nodes": [{"name": node.name, "mac": node.mac, "area": node.area.name if node.area else None} for node in nodes],
        "areas": [{"name": area.name, "volume": area.volume, "channel": area.channel_id} for area in areas]
    }

    json_data = json.dumps(config_data)
    print("Configuration exported")
    memory_file = BytesIO(json_data.encode('utf-8'))
    memory_file.seek(0)
    return send_file(memory_file, as_attachment=True, download_name="config.json", mimetype="application/json")


@app.route('/import_conf', methods=['POST'])
def import_conf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_content = file.read()
    data = json.loads(file_content)

    new_nodes = data.get("nodes", [])
    new_areas = data.get("areas", [])

    db_nodes = Nodes.query.all()
    db_areas = Areas.query.all()

    # Convert for easier lookup
    db_nodes_by_mac = {node.mac: node for node in db_nodes}
    db_area_names = {area.name for area in db_areas}
    new_area_names = {area['name'] for area in new_areas}

    # Output categories
    fresh_nodes = []
    renamed_nodes = []
    inferred_areas = []
    updated_areas = []

    # Build inferred areas from new_nodes that aren’t in newAreas
    for node in new_nodes:
        node_area = node.get('area')
        if node_area and node_area not in new_area_names:
            inferred_areas.append({"name": node_area, "volume": 50, "channel": None})
            new_area_names.add(node_area)  # Prevent duplicates

    # Compare new_nodes to db_nodes
    for node in new_nodes:
        db_node = db_nodes_by_mac.get(node['mac'])
        if not db_node:
            fresh_nodes.append(node)
        elif db_node.name != node['name']:
            renamed_nodes.append({"old": db_node, "new": node})

    # Track area membership changes
    for area in new_areas + inferred_areas:
        area_name = area['name']
        current_nodes = [n for n in db_nodes if n.area and n.area.name == area_name]
        future_nodes = [n for n in new_nodes if n.get('area') == area_name]

        removed = [n for n in current_nodes if n.mac not in {fn['mac'] for fn in future_nodes}]
        added = [fn for fn in future_nodes if fn['mac'] not in {n.mac for n in current_nodes}]

        if added or removed:
            updated_areas.append({
                "area": area,
                "added_nodes": added,
                "removed_nodes": removed
            })

    # Separate all areas (new + inferred) into existing or new
    existing_areas = []
    new_areas_only = []

    for area in new_areas + inferred_areas:
        if area['name'] in db_area_names:
            existing_areas.append(area)
        else:
            new_areas_only.append(area)

    return render_template(
        'import_conf.html',
        newNodes=new_nodes,
        freshNodes=fresh_nodes,
        renamedNodes=renamed_nodes,
        existingAreas=existing_areas,
        newAreas=new_areas_only,
        updatedAreas=updated_areas,
        nodes=db_nodes,
        areas=db_areas
    )



@app.route('/submit_import', methods=['POST'])
def submit_import():
    new_nodes = request.form.getlist('nodes')
    renamed_nodes = request.form.getlist('renamed_nodes')
    changes_in_existing_areas = request.form.getlist('existing_areas')
    new_areas = request.form.getlist('new_areas')
    process_areas = request.form.getlist('process_area[]')
    
    area_changes = {}
    for area_name in process_areas:
        added_nodes = request.form.getlist(f'area_changes[{area_name}][added_nodes][]')
        removed_nodes = request.form.getlist(f'area_changes[{area_name}][removed_nodes][]')
        
        area_changes[area_name] = {
            'added_nodes': added_nodes,
            'removed_nodes': removed_nodes
        }

    # Process Renamed Nodes
    for renamed_node in renamed_nodes:
        old_name, new_name, mac = eval(renamed_node)  # Convert string tuple to actual tuple
        node = Nodes.query.filter_by(mac=mac).first()
        if node:
            node.name = new_name
            db.session.commit()

    # Process New Nodes
    for new_node in new_nodes:
        name, mac = eval(new_node)
        if not Nodes.query.filter_by(mac=mac).first():
            new_node_obj = Nodes(name=name, mac=mac)
            db.session.add(new_node_obj)

    # Process New Areas
    for new_area in new_areas:
        name, volume, _ = eval(new_area)
        if not Areas.query.filter_by(name=name).first():
            new_area_obj = Areas(name=name, volume=volume)
            db.session.add(new_area_obj)

    # Process Changes in Existing Areas
    for area_name in changes_in_existing_areas:
        area = Areas.query.filter_by(name=area_name).first()
        if area:
            # Update volume
            volume = request.form.get(f'volume_{area_name}')
            if volume:
                area.volume = int(volume)
                db.session.commit()

    # Process Existing Areas and Node Assignments
    for area_name, changes in area_changes.items():
        area = Areas.query.filter_by(name=area_name).first()
        if area:
            # Add nodes
            for node_mac in changes['added_nodes']:
                node = Nodes.query.filter_by(mac=node_mac).first()
                if node and node.area_id != area.id:
                    node.area_id = area.id
                    db.session.commit()
            # Remove nodes
            for node_mac in changes['removed_nodes']:
                node = Nodes.query.filter_by(mac=node_mac).first()
                if node and node.area_id == area.id:
                    node.area_id = None
                    db.session.commit()

    db.session.commit()
    return redirect('/index')
#######################################
#############
#YOUTUBE#####
#############

def search_youtube(query, max_results=10):
    results = []
    try:
        # Search using youtubesearchpython (searches for videos on YouTube)
        videos_search = VideosSearch(query, limit=max_results)
        search_results = videos_search.result().get('result', [])
        for item in search_results:
            title = item.get('title', 'Sem título')
            url = item.get('link', 'Sem link')
            thumbnail = item.get('thumbnails', [{}])[0].get('url', '')  # Extracting the thumbnail URL
            author_info = item.get('channel', {})
            author = author_info.get('name', 'Unknown')  # Extracting the author (channel name)
            duration = item.get('duration', '00:00')  # Extracting the video duration
            results.append({
                "title": title,
                "url": url,
                "thumbnail": thumbnail,  # Include the thumbnail URL
                "author": author,        # Include the author name
                "duration": duration     # Include the duration
            })
    except Exception as e:
        print(f"Error occurred: {e}")
    return results


def search_youtube_live(query, max_results=30):
    results = []
    try:
        videos_search = VideosSearch(query, limit=max_results)
        search_results = videos_search.result().get('result', [])
        for item in search_results:
            duration = item.get('duration', None)
            # Verifica se é uma stream (duration == None)
            if duration is None:
                title = item.get('title', 'Sem título')
                url = item.get('link', 'Sem link')
                thumbnail = item.get('thumbnails', [{}])[0].get('url', '')
                author_info = item.get('channel', {})
                author = author_info.get('name', 'Desconhecido')
                results.append({
                    "title": title,
                    "url": url,
                    "thumbnail": thumbnail,
                    "author": author,
                })
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    return results

#################
@app.route("/current_playing", methods=["GET"])
def current_playing():
    channel_id = request.args.get('channel_id')
    if channel_id:
        with db.session() as session:
            channel = session.get(Channels, channel_id)
        if channel and channel.id in processes:
            current_song = processes[channel.id]['current_playing']["playing"]
            return jsonify({
                "current_song": str(current_song) if current_song else None
            })
    return jsonify({"current_song": None})


@app.route("/search_suggestions", methods=["GET"])
def search_suggestions():
    query = request.args.get('query')
    if query:
        results = search_youtube(query, max_results=5)  # Limit the number of results
        return jsonify(results)
    return jsonify([])

@app.route("/stream_search_suggestions", methods=["GET"])
def stream_search_suggestions():
    query = request.args.get('query')
    if query:
        print("query: ", query)
        results = search_youtube_live(query, max_results=5)
        return jsonify(results)
    return jsonify([])


@app.route("/select", methods=["POST"])
def select_song_to_download():
    title = request.form.get("title").strip()
    url = request.form.get("url")
    print(f"Selected video: {title} - {url}")
    song_name = title
    safe_filename = song_name.replace(' ', '_')
    # Create a hash from the song name (you can also use the full path if needed)
    song_hash = hashlib.sha256(safe_filename.encode()).hexdigest()
    # Generate the final .wav filename using the hash
    wav_filename = os.path.join(UPLOAD_FOLDER, f"{song_hash}.wav")
    # Download the selected YouTube audio in a separate thread to avoid blocking Flask
    threading.Thread(target=download_youtube_audio, args=(url, wav_filename)).start()
    save_yt_song(song_name, song_hash)
    return redirect(url_for('secundaria'))

@app.route("/select_stream", methods=["POST"])
def select_stream_to_save():
    title = request.form.get("title").strip()
    url = request.form.get("url")
    print(f"Selected stream: {title} - {url}")

    # verificar se já existe na base de dados o link, se não existe adicionar
    existing_stream = Streaming.query.filter_by(name=title).first()
    if existing_stream:
        print(f"Stream already exists: {existing_stream.name}")
        return redirect(url_for('secundaria'))

    # Salvar no banco de dados
    new_stream = Streaming(name=title, url=url)
    db.session.add(new_stream)
    db.session.commit()
    print("Nova stream adicionada:", new_stream.name)
    return redirect(url_for('secundaria'))

@app.route('/rename_streaming', methods=['POST'])
def rename_streaming():
    data = request.get_json()
    streaming_id = data.get('id')
    new_name = data.get('new_name')

    if not streaming_id or not new_name:
        return jsonify({'success': False, 'message': 'ID e novo nome são obrigatórios'}), 400
    streaming = Streaming.query.get(streaming_id)
    if not streaming:
        return jsonify({'success': False, 'message': 'Streaming não encontrado'}), 404
    streaming.name = new_name
    db.session.commit()

    return jsonify({'success': True, 'message': 'Nome atualizado com sucesso'})

@app.route('/delete_streaming', methods=['POST'])
def delete_streaming():
    data = request.get_json()
    streaming_id = data.get('id')

    if not streaming_id:
        return jsonify({'success': False, 'message': 'ID não fornecido'}), 400
    streaming = Streaming.query.get(streaming_id)
    if not streaming:
        return jsonify({'success': False, 'message': 'Streaming não encontrado'}), 404

    try:
        # Verificar se o streaming está associado a algum canal
        channels = Channels.query.filter(Channels.source == str(streaming_id), Channels.type == ChannelType.STREAMING).all()
        for channel in channels:
            channel.source = None
            db.session.commit()

            if channel.state == "playing":
                # Parar o processo FFmpeg associado ao canal
                if processes[channel.id]['process'] is not None:
                    processes[channel.id]['process'].terminate()
                    processes[channel.id]['process'].wait()
                    processes[channel.id]['process'] = None

                if os.path.exists(f"session_{channel.id}.sdp"):
                    os.remove(f"session_{channel.id}.sdp")

                channel.state = "stopped"
                db.session.commit()

        # Deletar o streaming
        db.session.delete(streaming)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Streaming deletado com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def save_yt_song(song_name, song_hash):
    with app.app_context():
        # Verifica se a música já existe no banco de dados
        existing_song = Songs.query.filter_by(song_hash=song_hash).first()
        if existing_song:
            print(f"Song already exists: {existing_song.name}")
            return
        # Salvar no banco de dados
        new_song = Songs(name=song_name, song_hash=song_hash)
        db.session.add(new_song)
        db.session.commit()
        print("Nova música adicionada:", new_song.name)

def download_youtube_audio(youtube_url, wav_filename):
    """
    Extracts audio from a YouTube video and saves it as a WAV file
    without downloading the video.
    """


    # Configure yt-dlp to fetch the best audio stream URL
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'quiet': True,               # Suppress logs
        'extract_audio': True,       # Extract audio (not strictly needed here)
    }
    # Get the direct audio stream URL
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        audio_url = info['url']  # Direct stream URL of the audio

    # Stream the audio directly to ffmpeg and save as WAV
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', audio_url,           # Input stream URL
        '-vn',                     # Disable video (audio only)
        '-acodec', 'pcm_s16le',    # Audio codec for WAV format
        '-ar', '44100',            # Set audio sample rate to 44.1kHz (WAV standard)
        '-ac', '2',                # Set audio channels to stereo (2 channels)
        '-y',                      # Overwrite output if exists
        wav_filename
    ]

    # Run FFmpeg with stdout and stderr suppressed
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Downloaded and converted {youtube_url} to {wav_filename}")
    
#################################################################################

#################################################################################

def shutdown_handler(stop_event):
    stop_event.set()
    sys.exit(0)


# Função para obter o IP local do host
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta a um servidor externo
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Error: {e}"


def remove_trash():
    # apagar ficheiros sdp, txt
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.endswith('.sdp') or file.endswith('.txt'):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
            print(f"Removed temporary file: {file}")
            
    db.session.query(Interruptions).update({Interruptions.state: 'off'})
    db.session.commit()
    db.session.query(Nodes).update({Nodes.connected: False})
    db.session.commit()

# Bloco principal de execução
if __name__ == '__main__':
    stop_event = threading.Event()  # Evento para interromper a thread
    msg_buffer = queue.Queue()  # Fila para mensagens de status
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados, se ainda não existirem        
        remove_trash()  # Remove arquivos temporários    
        create_default_channels()  # Inicializa os canais padrão
        get_mics()

    # Associa o sinal SIGINT ao shutdown_handler para tratamento de Ctrl+C
    signal.signal(signal.SIGINT, lambda signum, frame: shutdown_handler(stop_event))    
    # Inicia a thread para detectar novos nós    
    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()





    socketio.run(app, host=get_host_ip() ,debug=False, port=5000)


