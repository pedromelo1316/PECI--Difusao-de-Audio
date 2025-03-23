# Importações de módulos e bibliotecas necessárias
from enum import Enum
from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
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

# Inicialização do app Flask, SQLAlchemy e SocketIO
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Configurações de áudio
BITRATE = "128k"  # Taxa de bits máxima
SAMPLE_RATE = "48000"  # Taxa de amostragem
CHUNCK_SIZE = 960
AUDIO_CHANNELS = "1"  # Mono

NUM_CHANNELS = 3  # Número total de canais

# Função para iniciar o processo do ffmpeg para um canal específico
def start_ffmpeg_process(channel, source, _type):
    # Define o endereço de multicast baseado no número do canal
    multicast_address = f"rtp://239.255.0.{channel}:12345"
    print(f"session_{channel}.sdp")
    print("source: ", source)
    print("type: ", _type)
    
    # Verifica o tipo de transmissão e configura o comando do ffmpeg apropriado
    if _type == ChannelType.VOICE:
        # Transmissão de voz via dispositivo de áudio (alsa)
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-f", "alsa", "-i", source,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            #"-frame_duration", "120",  # Frames de 40 ms
            "-f", "rtp",
            "-sdp_file", f"session_{channel}.sdp",
            f"{multicast_address}"
        ]
    elif _type == ChannelType.LOCAL:
        # Transmissão local utilizando um arquivo de playlist
        playlist_path = f"Playlists/{source}.txt"
        if not os.path.exists(playlist_path):
            print(f"Playlist {playlist_path} not found")
            return None
        
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
            "-f", "concat",
            "-safe", "0",
            "-re",
            "-i", f"Playlists/{source}.txt",
            "-af", "apad",
            "-ar", SAMPLE_RATE,
            "-vn",
            "-acodec", "libopus",
            "-b:a", BITRATE,
            #"-frame_duration", "120",  # Frames de 40 ms
            "-ac", AUDIO_CHANNELS,
            "-f", "rtp",
            "-sdp_file", f"session_{channel}.sdp",
            f"{multicast_address}"
        ]
    elif _type == ChannelType.STREAMING:
        # Transmissão via streaming com URL proveniente do yt-dlp
        source = "https://www.youtube.com/live/YDvsBbKfLPA?si=TdUqXCrxJojjNDns"
        
        try:
            # Comando para obter a URL direta do stream
            ytdl_cmd = [
            "yt-dlp",
            "-g",
            "-f", "bestaudio[protocol!=m3u8_native]/bestaudio",
            "--no-check-certificates", 
            "--socket-timeout", "15", 
            source
            ]
            direct_url = subprocess.check_output(ytdl_cmd, text=True).strip()
        except subprocess.TimeoutExpired:
            print("Timeout ao obter URL.")
            return None
        except Exception as e:
            print(f"Erro ao obter URL: {e}")
            return None
        

        # Comando do ffmpeg utilizando a URL obtida
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "fatal",  # Modo silencioso (altere para 'error' para testar)
            "-re",  # Força a leitura no tempo real para streams
            "-analyzeduration", "10M",  # Reduz o tempo de análise inicial
            "-probesize", "10M",
            #"-rw_timeout", "5000000",  # Timeout de leitura
            "-vn",
            "-i", direct_url,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            "-buffer_size", "1024",  # Aumenta o buffer de saída
            "-max_delay", "200000",  # Limita o atraso máximo
            "-f", "rtp",
            #"-frame_duration", "120",  # Frames de 120 ms
            "-sdp_file", f"session_{channel}.sdp",
            "-muxdelay", "0.1",  # Reduz o atraso de muxagem
            "-muxpreload", "0.1",
            f"{multicast_address}"
        ]
    else:
        return None
    # Inicia o subprocesso do ffmpeg
    process = subprocess.Popen(cmd)
    return process

# Função para trocar o processo do canal (reinicia se necessário)
def change_channel_process(channel, source, transmission_type):
    global processes

    print("Changing channel...")
    
    # Se já existir um processo para o canal, termina-o
    if processes[channel]:
        print("Terminating process...")
        processes[channel].terminate()
        processes[channel].wait()
        processes[channel] = None
        
    print("channel: ", channel)
    print("transmission_type: ", transmission_type)
    
     # Após a mudança, envia informações atualizadas para os nós
    with app.app_context():
        areas = db.session.query(Areas).filter(Areas.channel_id == channel).all()
        nodes = []
        for area in areas:
            nodes += area.nodes
        send_info(nodes)
    
    
        
    # Inicia o novo processo para o canal com os parâmetros fornecidos
    process = start_ffmpeg_process(channel, source, transmission_type)
    if process:
        processes[channel] = process
        print(f"Channel {channel} started")
    else:
        processes[channel] = None
        
    # Após a mudança, envia informações atualizadas para os nós
    with app.app_context():
        areas = db.session.query(Areas).filter(Areas.channel_id == channel).all()
        nodes = []
        for area in areas:
            nodes += area.nodes
        send_info(nodes)
    
    print(processes)

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
    ip = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    mac = db.Column(db.String(200), unique=True, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)

    def __repr__(self):
        return f'<Node {self.id}: {self.name}>'

# Enum para definir os tipos de canais permitidos
class ChannelType(str, Enum):
    LOCAL = "LOCAL"
    STREAMING = "STREAMING"
    VOICE = "VOICE"


#################################################################################
#################################################################################

# Modelo para "Playlist"
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    items = db.Column(db.Text, nullable=True)  

    def __repr__(self):
        return f'<Playlist {self.id}: {self.name}>'

#################################################################################
#################################################################################


# Modelo para canais
class Channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(ChannelType), nullable=False)
    source = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return 

# Função para criar canais padrões caso não existam
def create_default_channels():
    global processes, NUM_CHANNELS
    processes = {}
    # Verifica se o número de canais no banco é diferente do esperado
    if db.session.query(Channels).count() != NUM_CHANNELS:
        db.session.query(Channels).delete()
        db.session.commit()
        # Cria os canais padrão com tipo LOCAL e fonte "default"
        for i in range(1, NUM_CHANNELS+1):
            new_channel = Channels(type=ChannelType.LOCAL, source="default")
            db.session.add(new_channel)
            db.session.commit()
            processes[i] = start_ffmpeg_process(i, "default", ChannelType.LOCAL)
            print(f"Channel {i} started")
    else:
        for channel in db.session.query(Channels).all():
            index = channel.id
            processes[index] = start_ffmpeg_process(index, channel.source, channel.type)
            print(f"Channel {channel.id} started")
            
            
    send_info(Nodes.query.all())  # Envia informações iniciais para os nós
            
    return processes

# Rota principal (index) que renderiza a página inicial com os nós, áreas e canais
@app.route('/', methods=['GET'])
def index():
    nodes = Nodes.query.order_by(Nodes.id).all()
    areas = Areas.query.order_by(Areas.id).all()
    channels = Channels.query.order_by(Channels.id).all()
    ####
    playlist = db.session.query(Playlist).first()  # Substitua por lógica específica, se necessário

    ###
    return render_template("index.html", nodes=nodes, areas=areas, channels=channels, playlist=playlist)
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
def send_info(nodes, removed=False, suspended=False):
    if not removed and not suspended:
        dic = {}
        for node in nodes:
            mac = node.mac
            area_id = node.area_id
            area = db.session.get(Areas, area_id) if area_id is not None else None
            volume = (area.volume/50) if area else 1
            channel = area.channel_id if area else None
            header = None
            
            # Se existir canal, lê o arquivo SDP gerado
            #if processes[channel] != None:
            if channel is not None and processes.get(channel) is not None:
                try:
                    file = open(f"session_{channel}.sdp", "r")
                    header = file.read()
                    file.close()
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
                        node = Nodes(name=node_name, mac=node_mac, ip=node_ip)
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
                        node_name = node.name
                        msg_buffer.put(f"Node {node_name} reconnected")
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
        send_info(Nodes.query.filter_by(area_id=area.id).all())
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
    
# Rota para atualizar o tipo de canal
@app.route('/update_channel/<int:channel_id>', methods=['POST'])
def update_channel(channel_id):
    # Recupera o novo tipo de canal enviado pelo formulário
    new_type = request.form.get('channel_type')
    if new_type not in [channel.value for channel in ChannelType]:
        return redirect('/')
    channel = db.session.get(Channels, channel_id)
    if not channel:
        return redirect('/')
    try:
        # Atualiza o tipo do canal e reinicia o processo correspondente
        channel.type = ChannelType[new_type]
        print(f"Channel {channel_id} updated to {new_type}")
        db.session.commit()
        change_channel_process_thread = threading.Thread(target=change_channel_process, args=(channel.id, channel.source, channel.type), daemon=True)
        change_channel_process_thread.start()
        socketio.emit('reload_page', namespace='/')
        return redirect('/')
    except Exception as e:
        socketio.emit('reload_page', namespace='/')
        return redirect('/')

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




@app.route('/edit_playlist')
def edit_playlist():
    return render_template('edit_playlist.html')


@app.route('/edit_stream/<int:playlist_id>')
def edit_stream(playlist_id):
    # Substitua pelo código correto para buscar a playlist no banco de dados
    playlist = db.session.query(Playlist).filter_by(id=playlist_id).first()
    
    if not playlist:
        # Retorne um erro ou redirecione se a playlist não for encontrada
        return "Playlist não encontrada", 404

    return render_template('edit_stream.html', playlist=playlist)




# Função para tratar o desligamento do sistema (Ctrl+C)
def shutdown_handler(signum, frame):
    """Trata o SIGINT (Ctrl+C) e garante o desligamento limpo."""
    print("\nShutting down gracefully...")
    with app.app_context():
        nodes = Nodes.query.all()
    send_info(nodes, suspended=True)  # Envia mensagem de suspensão para os nós
    stop_event.set()  # Sinaliza para parar as threads
    thread.join()     # Aguarda a thread de detecção de nós terminar
    # Aqui poderia-se terminar outros subprocessos, se necessário
    print("Processes terminated")
    sys.exit(0)  # Encerra o programa de forma limpa


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
        
        
    # Associa o sinal SIGINT ao shutdown_handler para tratamento de Ctrl+C
    signal.signal(signal.SIGINT, shutdown_handler)

    # Inicia a thread para detectar novos nós
    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()
    
    # Inicia o servidor Flask com SocketIO
    socketio.run(app, host=get_host_ip() ,debug=False, port=5000)
    #socketio.run(app, debug=False)

    
