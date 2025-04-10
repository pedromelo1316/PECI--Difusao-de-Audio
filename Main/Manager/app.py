# Importações de módulos e bibliotecas necessárias
from enum import Enum
from io import BytesIO
from flask import Flask, render_template, request, redirect, flash, jsonify, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os
from flask import request, jsonify
from werkzeug.utils import secure_filename
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

# Configurações de áudio
BITRATE = "128k"  # Taxa de bits máxima
SAMPLE_RATE = "48000"  # Taxa de amostragem
CHUNCK_SIZE = 960
AUDIO_CHANNELS = "1"  # Mono

NUM_CHANNELS = 3  # Número total de canais

@app.route('/update_microphones', methods=['GET'])
def update_microphones():
    get_mics()
    microphones = Microphone.query.all()
    microphones_list = [
        {"id": mic.id, "name": mic.name, "device": mic.device, "card": mic.card, "short_cut": mic.short_cut}
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
    
    send_info(nodes, restart=True)
    return jsonify({'success': True})

def start_ffmpeg_process(channel, source, _type):
    # Define o endereço de multicast baseado no número do canal
    multicast_address = f"rtp://239.255.0.{channel}:12345"
    print(f"session_{channel}.sdp")
    print("source: ", source)
    print("type: ", _type)
    
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
        
        mic = {"card": "1", "device": "0"}  #usar no terminal arecord -l  # Lista dispositivos de captura (microfones) 
        
        # Comando do FFmpeg para transmissão de microfone
        pass

    elif _type == ChannelType.LOCAL:
        
        # Transmissão local utilizando uma lista de músicas
        print("source: ", source)

        # Divide o source em uma lista de músicas
        musicas = [musica.strip() for musica in source.split(",")]

        # Cria um arquivo de playlist temporário para o FFmpeg
        playlist_file_path = f"Playlists/temp_playlist_{channel}.txt"
        with open(playlist_file_path, "w") as playlist_file:
            for musica in musicas:
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
    process = subprocess.Popen(cmd)
    return process

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
            )
            db.session.add(new_channel)
            db.session.commit()
            processes[new_channel.id] = {"process": None}
            print(f"{new_channel.name} started")

    else:
        for channel in db.session.query(Channels).all():
            if os.path.exists(f"session_{channel.id}.sdp"):
                os.remove(f"session_{channel.id}.sdp")
            index = channel.id
            processes[index] = {"process": None}  # Uncommented to start the process
            print(f"Channel {channel.id} started")
            
            

    for channel in db.session.query(Channels).all():
        channel.state = "stopped"
    db.session.commit()
    
    send_info(Nodes.query.all(), restart=True)  # Envia informações iniciais para os nós
            
    return processes

@app.route('/save_channel_configs', methods=['POST'])
def save_channel_configs():
    data = request.json
    channel_id = data.get('channel_id')
    channel_type = data.get('channel_type').upper()
    channel_reproduction = data.get('channel_reproduction')
    channel_microfone = data.get('channel_microfone')

    # Processa os dados recebidos
    print(f"ID do canal: {channel_id}")
    print(f"Tipo de transmissão: {channel_type}")
    print(f"Microfone: {channel_microfone}")
    print(f"Reprodução: {channel_reproduction}")
    #alterar na base de dados o tipo de transmissão do canal e o respetivo microfone e reiniciar o processo
    channel = db.session.query(Channels).filter(Channels.id == channel_id).first()
    if not channel:
        return jsonify({"error": "Canal não encontrado"}), 404
    channel.type = channel_type
    channel.microphone = channel_microfone
    
    # Reinicia o processo do canal com as novas configurações
    if channel_type == "STREAMING":
        stream = db.session.query(Streaming).filter(Streaming.name == channel_reproduction).first()
        if not stream:
            return jsonify({"error": "Streaming não encontrado"}), 404
        channel_source = stream.url
        channel.source = channel_source
        db.session.commit()
        # Reinicia o processo do canal
    elif channel_type == "LOCAL":
        #percorrer conteudo de channel_reproduction que está do genero "PLAYLIST:playlist1 SONG:musica1 PLAYLIST:playlist2 PLAYLIST:playlist3 SONG:musica2"
        #se for uma musica adicionar a musicas se for uma playlist ir á base de dados obter as musicas
        
        
        musicas = []
        for item in channel_reproduction.split():
            if item.startswith("PLAYLIST:"):
                playlist_name = item.split(":")[1]
                playlist = db.session.query(Playlist).filter(Playlist.name == playlist_name).first()
                if playlist:
                    for song in playlist.songs:
                        musicas.append(song.name)
                    


            elif item.startswith("SONG:"):
                song_name = item.split(":")[1]
                musicas.append(song_name)
                
        channel_source = ", ".join(musicas)
        channel.source = channel_source
        db.session.commit()
        

        #change_channel_process(channel.id, channel_source, ChannelType.LOCAL)
    else:
        print("Tipo de canal inválido")    
    
    
        return jsonify({"error": "Tipo de canal inválido"}), 400
    
    
    if processes[channel.id]['process'] is not None:
        processes[channel.id]['process'].terminate()
        processes[channel.id]['process'].wait()
        processes[channel.id]['process'] = None
        processes[channel.id]['process'] = start_ffmpeg_process(channel.id, channel_source, channel_type)
        
        areas = db.session.query(Areas).filter(Areas.channel_id == channel_id).all()
        nodes = []
        for area in areas:
            nodes += area.nodes
            
        if processes[channel.id]['process'] is None:
            return jsonify({'status': 'error', 'message': 'Erro ao iniciar o processo FFmpeg'})
        
        while not os.path.exists(f"session_{channel.id}.sdp"):
            time.sleep(0.1)
            
            
        print("sending info to nodes")
        print(nodes)
        
        send_info(nodes, restart=True)
    
    

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

    def __repr__(self):
        return f'<Node {self.id}: {self.name}>'
    
    
class Microphone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    device = db.Column(db.String(200), nullable=False)
    card = db.Column(db.String(200), nullable=False)
    short_cut = db.Column(db.String(200), nullable=True)

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

    def __repr__(self):
        return f'<Song {self.id}: {self.name}>'

# Classe Playlist
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    songs = db.relationship('Songs', secondary=playlist_songs, backref='playlist', lazy=True)

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
    microphone = db.Column(db.String(200),nullable=True)
    state = db.Column(db.String(200), nullable=False, default="stopped")

    def __repr__(self):
        return f'<Channel {self.id}: {self.name}>'


###############3
class Streaming(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __init__(self, name, url):
        self.name = name
        self.url = url
        

# Rota principal (index) que renderiza a página inicial com os nós, áreas e canais
@app.route('/', methods=['GET'])
def index():
    nodes = Nodes.query.order_by(Nodes.id).all()
    areas = Areas.query.order_by(Areas.id).all()
    channels = Channels.query.order_by(Channels.id).all()

    #
    # playlists = get_playlists()  # Função que retorna as playlists
    #songs = get_songs()  # Função que retorna as músicas
    #return render_template('index.html', playlists=playlists, songs=songs)
    ####
    #playlist = db.session.query(Playlist).first()  # Substitua por lógica específica, se necessário

    ###

    return render_template("index.html", nodes=nodes, areas=areas, channels=channels)
# Rota para deleção de um nó específico
@app.route('/delete/<int:id>')
def delete(id):
    node_to_delete = Nodes.query.get_or_404(id)
    try:
        db.session.delete(node_to_delete)
        db.session.commit()
        socketio.emit('update', {'action': 'delete', 'id': id})
        send_info([node_to_delete], removed=True)
        return redirect('/')
    except:
        return 'Houve um problema ao remover o nó'
    
# Rota para atualizar a lista de nós (simples redirecionamento)
@app.route('/refresh_nodes', methods=['POST'])
def refresh_nodes():
    return redirect('/')

# Rota para atualização dos dados de um nó
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    node = Nodes.query.get_or_404(id)
    if request.method == 'POST':
        node.name = request.form['name']
        try:
            db.session.commit()
            socketio.emit('update', {'action': 'update', 'id': id, 'name': node.name})
            return redirect('/')
        except:
            return 'Houve um problema ao atualizar a tarefa'
    else:
        return render_template('update.html', node=node)

# Função para enviar informações atualizadas para os nós via broadcast UDP
def send_info(nodes, removed=False, suspended=False, restart=False):
    if not removed and not suspended:
        dic = {}
        for node in nodes:
            mac = node.mac
            area_id = node.area_id
            area = db.session.get(Areas, area_id) if area_id is not None else None
            volume = (area.volume/50) if area else 1
            channel = area.channel_id if area else None
            header = None
            
            print("Channel ID:", channel)
            
            # Se existir canal, lê o arquivo SDP gerado
            #if processes[channel] != None:
            if channel is not None and processes.get(channel) is not None:
                try:
                    with open(f"session_{channel}.sdp", "r") as file:
                        header = file.read()
                except:
                    pass
            
            dic[mac] = {"volume": volume, "channel": channel, "header": header}
    elif removed:
        dic = {}
        for node in nodes:
            mac = node.mac
            dic[mac] = {"removed": True}
            
    elif suspended:
        dic = {}
        for node in nodes:
            mac = node.mac
            dic[mac] = {"suspended": True}
            
    if restart:
        for node in nodes:
            mac = node.mac
            dic[mac].update({"restart": True})
            

            
    msg = json.dumps(dic)
    # Envia mensagem via broadcast UDP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', 8081))
        
    print("Info sent to nodes:", nodes)

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
                # Envia confirmação para o nó
                server_socket.sendto(b"OK", addr)
                node_name, node_mac = data.split(',')
                node_ip = addr[0]

                try:
                    with app.app_context():
                        if db.session.query(Nodes).filter(Nodes.mac == node_mac).first():
                            raise Exception("MAC already in use")
                        node_name = node_name.upper()
                        node = Nodes(name=node_name, mac=node_mac, ip=node_ip, area_id=1)  #remover este area_id = 1
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
                            db.session.commit()

                            node_name = node.name
                        print(f"Node {node.name} already exists, updating IP {node_ip}")
                    else:
                        msg_buffer.put(f"Error: {e}")
                        server_socket.sendto(b"Error " + str(e).encode('utf-8'), addr)

                with app.app_context():
                    node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                    send_info([node], restart=True)
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
        return redirect('/')
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
        socketio.emit('reload_page', namespace='/')
        return jsonify({"success": True, "id": new_area.id, "name": new_area.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para remover uma área
@app.route('/remove_area', methods=['POST'])
def remove_area():
    area_name = request.form.get('name')
    if not area_name:
        flash("Area name is required", "error")
        return redirect('/')
    try:
        area = Areas.query.filter_by(name=area_name).first()
        if not area:
            flash("Area not found", "error")
            return redirect('/')
        
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
        
        socketio.emit('reload_page', namespace='/')
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')

# Rota para atualizar o volume de uma área
@app.route('/update_volume', methods=['POST'])
def update_volume():
    area_name = request.form.get('name')
    new_volume = float(request.form.get('volume', 0))
    area = Areas.query.filter_by(name=area_name).first()
    if not area:
        flash("Area not found", "error")
        return redirect('/')
    try:
        area.volume = new_volume
        print(f"Volume updated to {new_volume} for area {area_name}")
        db.session.commit()
        send_info(Nodes.query.filter_by(area_id=area.id).all(), restart=True)
        return redirect('/')
    except Exception as e:
        return redirect('/')

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
    socketio.emit('reload_page', namespace='/')
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
        socketio.emit('reload_page', namespace='/')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/edit_channels')
def edit_channels():
    channel_id = request.args.get('channel_id', type=int)
    channel = Channels.query.get_or_404(channel_id)

    playlists = Playlist.query.all()
    playlist_songs = {
        playlist.name: [song.name for song in playlist.songs]
        for playlist in playlists
    }
    all_songs = [song.name for song in Songs.query.all()]
    streamings = Streaming.query.all()
    streaming_sources = [streaming.name for streaming in streamings]
    
    
    return render_template(
        'edit_channels.html',
        channel=channel,
        playlists=playlist_songs.keys(),
        playlist_songs=playlist_songs,
        all_songs=all_songs,
        streaming_sources=streaming_sources 
        
    )

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




# Rota para atualizar o canal associado a uma área
@app.route('/update_area_channel', methods=['POST'])
def update_area_channel():
    area_name = request.form.get('name')
    new_channel_id = request.form.get('channel_id')
    print(f"Updating channel for area {area_name} to {new_channel_id}")
    area = Areas.query.filter_by(name=area_name).first()
    if not area:
        flash("Area not found", "error")
        return redirect('/')
    try:
        area.channel_id = new_channel_id
        print(f"Channel updated to {new_channel_id} for area {area_name}")
        db.session.commit()
        send_info(Nodes.query.filter_by(area_id=area.id).all())
        socketio.emit('reload_page', namespace='/')
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        socketio.emit('reload_page', namespace='/')
        return redirect('/')







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
        
        try:
            # Comando para obter a URL direta do stream
            
            ytdl_cmd = [
            "yt-dlp",
            "-g",
            "-f", "bestaudio",
            "-o",
            "--no-check-certificates", 
            "--socket-timeout", "15", 
            stream_url
            ]
            direct_url = subprocess.check_output(ytdl_cmd, text=True).strip()
        except subprocess.TimeoutExpired:
            print("Timeout ao obter URL.")
            return None
        except Exception as e:
            print(f"Erro ao obter URL: {e}")
            return None
        
        # Salvar no banco de dados
        new_stream = Streaming(name=stream_name, url=direct_url)
        db.session.add(new_stream)
        db.session.commit()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    




################3
# playlist
####################

# Rota para obter todas as músicas
@app.route('/songs', methods=['GET'])
def get_songs():
    songs = Songs.query.order_by(Songs.id).all()
    return jsonify([{"id": song.id, "name": song.name} for song in songs])

# Rota para adicionar uma nova música
@app.route('/add_song', methods=['POST'])
def add_song():
    
    if 'file' not in request.files:
        print("Arquivo de música é obrigatório")
        return jsonify({"error": "Arquivo de música é obrigatório"}), 400

    file = request.files['file']
    if file.filename == '':
        print("Nenhum arquivo selecionado")
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    if not allowed_file(file.filename):
        print("Formato de arquivo não suportado")
        return jsonify({"error": "Formato de arquivo não suportado"}), 400

    song_name = request.form.get('name')
    print("song_name: ", song_name)
    if not song_name:
        print("Nome da música é obrigatório")
        return jsonify({"error": "Nome da música é obrigatório"}), 400

    if Songs.query.filter_by(name=song_name).first():
        return jsonify({"error": "Song already exists."}), 400

    try:
        print("Dados recebidos:", request.form)
        # Salvar o arquivo original
        filename = secure_filename(file.filename)
        filename = f"{song_name}{os.path.splitext(filename)[1]}"
        print("filename: ", filename)
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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            except subprocess.CalledProcessError as e:
                print(f"Erro ao converter o arquivo: {e.stderr.decode()}")
                return jsonify({"error": "Erro ao converter o arquivo para .wav"}), 500

            # Remover o arquivo original (opcional)
            os.remove(original_path)
        else:
            wav_path = original_path

        # Salvar no banco de dados
        new_song = Songs(name=song_name)
        db.session.add(new_song)
        db.session.commit()

        print("Nova música adicionada:", new_song.name)

        return jsonify({"success": True, "id": new_song.id, "name": new_song.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    print(f"Eleminar musica {song_name}")
    song = Songs.query.filter_by(name=song_name).first()
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404
    try:
        db.session.delete(song)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
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

        # Criar a pasta da playlist
        save_playlist_file(playlist_name)


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
    
@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    updated_songs = data.get('songs')  # Lista de músicas atualizadas

    if not playlist_name or updated_songs is None:
        return jsonify({"error": "Nome da playlist e lista de músicas são obrigatórios"}), 400

    # Busca a playlist pelo nome
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    try:
        # Atualiza as músicas da playlist
        playlist.songs = Songs.query.filter(Songs.name.in_(updated_songs)).all()
        db.session.commit()

        save_playlist_file(playlist_name)

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def save_playlist_file(playlist_name):
    # Caminho do arquivo da playlist
    
    playlist_file_path = os.path.join(app.config['PLAYLISTraiz_FOLDER'], f"{playlist_name}.txt")

    # Busca a playlist pelo nome
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        raise Exception("Playlist não encontrada")

    # Gera o conteúdo do arquivo com as músicas da playlist
    lines = []
    for song in playlist.songs:
        song_path = os.path.join("Songs", f"{song.name}.wav")
        lines.append(f"file {song_path}")

    # Cria o arquivo da playlist e escreve o conteúdo
    with open(playlist_file_path, "w") as playlist_file:
        playlist_file.write("\n".join(lines))

    print(f"Arquivo da playlist {playlist_name} salvo em {playlist_file_path}")


#################################################################################


@app.route('/export_conf', methods=['GET'])
def export_conf():
    nodes = Nodes.query.all()
    areas = Areas.query.all()
    
    config_data = {
        "nodes": [{"name": node.name, "mac": node.mac, "area": node.area.name if node.area else None} for node
                  in nodes],
        "areas": [{"name": area.name, "volume": area.volume, "channel": area.channel_id} for area in areas]
    }

    json_data = json.dumps(config_data)

    # Create a file-like object in memory
    memory_file = BytesIO(json_data.encode('utf-8'))
    memory_file.seek(0)

    print("Configuration exported")
    # Send the file for download
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


    nodes = data.get("nodes", [])
    areas = data.get("areas", [])

    for area_data in areas:
        area = Areas.query.filter_by(name=area_data['name']).first()
        if area:
            area.volume = area_data['volume']
            area.channel_id = area_data['channel']
            db.session.commit()
        else:
            new_area = Areas(name=area_data['name'], volume=area_data['volume'], channel_id=area_data['channel'])
            db.session.add(new_area)
            db.session.commit()

    for node_data in nodes:
        node = Nodes.query.filter_by(mac=node_data['mac']).first()
        if node:
            node.name = node_data['name']
            node.area_id = Areas.query.filter_by(name=node_data['area']).first().id if node_data['area'] else None
            db.session.commit()
        else:
            if node_data['area']:
                area = Areas.query.filter_by(name=node_data['area']).first()
                new_node = Nodes(name=node_data['name'], mac=node_data['mac'], area_id=area.id)
            else:
                new_node = Nodes(name=node_data['name'], mac=node_data['mac']) 
            db.session.add(new_node)
            db.session.commit()

    print("Configuration imported")
    return jsonify({"success": True})

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

# Bloco principal de execução
if __name__ == '__main__':
    stop_event = threading.Event()  # Evento para interromper a thread
    msg_buffer = queue.Queue()  # Fila para mensagens de status
    

    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados, se ainda não existirem
        create_default_channels()  # Inicializa os canais padrão
        get_mics()

        
        
    # Associa o sinal SIGINT ao shutdown_handler para tratamento de Ctrl+C
    signal.signal(signal.SIGINT, lambda signum, frame: shutdown_handler(stop_event))

    # Inicia a thread para detectar novos nós
    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()
    
    # Inicia o servidor Flask com SocketIO
    socketio.run(app, host=get_host_ip() ,debug=False, port=5000)
    #socketio.run(app, debug=False)

