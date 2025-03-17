from enum import Enum
from flask import Flask, render_template, request, redirect, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import subprocess
import threading
import queue
import time
import socket
import json




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # acho que tenho de meter esta linha para poder usar o flash
db = SQLAlchemy(app)
socketio = SocketIO(app)



class Areas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nodes = db.relationship('Nodes', backref='area', lazy=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=True)
    volume = db.Column(db.Integer, nullable=False, default=50)

    def __repr__(self):
        return f'<Area {self.id}: {self.name}>'

class Nodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    mac = db.Column(db.String(200), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)

    def __repr__(self):
        return f'<Node {self.id}: {self.name}>'


class ChannelType(str, Enum):  # Enum to restrict allowed values
    LOCAL = "LOCAL"
    STREAMING = "STREAMING"
    VOICE = "VOICE"

class Channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(ChannelType), nullable=False)  # Enforce restriction

    def __repr__(self):
        return 

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    songs = db.relationship('Song', secondary='playlist_song', backref=db.backref('playlists', lazy='dynamic'))

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

class Microphone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('song_order', db.Integer, nullable=False, default=999999)  # new column
)

def create_default_channels():
    ##add channels if less than 3
    if db.session.query(Channels).count() < 3:
        for channel in ChannelType:
            new_channel = Channels(type=channel)
            db.session.add(new_channel)
            db.session.commit()

# ...existing code...
def ensure_column_song_order():
    from sqlalchemy import inspect
    engine = db.engine
    with engine.connect() as conn:
        inspector = inspect(conn)
        if inspector.has_table('playlist_song'):
            columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info('playlist_song')")]
            if 'song_order' not in columns:
                print("Adding 'song_order' column...")
                conn.exec_driver_sql("ALTER TABLE playlist_song ADD COLUMN song_order INTEGER NOT NULL DEFAULT 999999")
# ...existing code...

@app.route('/', methods=['GET'])
def index():
    nodes = Nodes.query.order_by(Nodes.id).all()
    areas = Areas.query.order_by(Areas.id).all()
    channels = Channels.query.order_by(Channels.id).all()
    playlists = Playlist.query.order_by(Playlist.id).all()
    songs = Song.query.order_by(Song.id).all()
    microphones = Microphone.query.order_by(Microphone.id).all()
    return render_template("index.html", nodes=nodes, areas=areas, channels=channels, playlists=playlists, songs=songs, microphones=microphones)

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
    
@app.route('/refresh_nodes', methods=['POST'])
def refresh_nodes():
    return redirect('/')

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
    

def send_info(nodes, removed=False):
    if not removed:
        dic = {}
        for node in nodes:
            mac = node.mac
            area_id = node.area_id
            area = db.session.get(Areas, area_id) if area_id is not None else None
            
            volume = area.volume if area else None
            channel = area.channel_id if area else None

            dic[mac] = {"volume": volume, "channel": channel}
    else:
        dic = {}
        for node in nodes:
            mac = node.mac
            dic[mac] = {"removed": True}

    msg = json.dumps(dic)

    #print(msg)
    #mandar broadcast do dic
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', 8081))

def detect_new_nodes(stop_event, msg_buffer):
    time.sleep(0.1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', 8080))
        msg_buffer.put("Detection started")
        while not stop_event.is_set():
            data, addr = server_socket.recvfrom(1024)
            data = data.decode('utf-8')
            if data:
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
                        }
                    )
                    socketio.emit('reload')

                    msg_buffer.put(f"Node {node_name} connected")
                    server_socket.sendto(b"OK", addr)
                except Exception as e:
                    if str(e) == "Limit of nodes with the same name reached":
                        msg_buffer.put("Limit of nodes with the same name reached")
                        server_socket.sendto(b"Limit of nodes with the same name reached", addr)
                    elif str(e) == "MAC already in use":
                        with app.app_context():
                            node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                        
                        node_name = node.name
                        msg_buffer.put(f"Node {node_name} reconnected")
                        server_socket.sendto(b"OK", addr)
                    else:
                        msg_buffer.put(f"Error: {e}")
                        server_socket.sendto(b"Error " + str(e).encode('utf-8'), addr)

                with app.app_context():
                    node = db.session.query(Nodes).filter(Nodes.mac == node_mac).first()
                    send_info([node])
                    socketio.emit('reload_page', namespace='/')  # Emite para todos os clientes




@app.route('/rename_node/<int:id>', methods=['POST'])
def rename_node(id):
    new_name = request.form['name']
    try:
        node = Nodes.query.get_or_404(id)
        node.name = new_name
        db.session.commit()
        return redirect('/')
    
    except Exception as e:
        return str(e), 500


@app.route('/add_area', methods=['POST'])
def add_area():
    data = request.json  
    area_name = data.get('name')

    if not area_name:
        return jsonify({"error": "Nome da área é obrigatório"}), 400

    if Areas.query.filter_by(name=area_name).first():
        return jsonify({"error": "Área já existe"}), 400

    try:
        new_area = Areas(name=area_name, volume=50)  # Volume = 50%, Canal 1 como padrão
        db.session.add(new_area)
        db.session.commit()

        return jsonify({"success": True, "id": new_area.id, "name": new_area.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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

        nodes_in_area = Nodes.query.filter_by(area_id=area.id).all()
        for node in nodes_in_area:
            node.area_id = None  
            db.session.add(node)

        db.session.delete(area)
        db.session.commit()

        send_info(nodes_in_area)
        flash(f"Area {area_name} removed", "success")
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')

    

@app.route('/update_volume', methods=['POST'])
def update_volume():
    area_name = request.form.get('name')
    new_volume = float(request.form.get('volume', 0)) / 50.0

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


@app.route('/get_free_nodes')
def get_nodes():
    nodes = Nodes.query.filter_by(area_id=None).all()  # Apenas os não associados
    return jsonify([{"id": node.id, "name": node.name} for node in nodes])


@app.route('/associate_node', methods=['POST'])
def associate_node():
    data = request.get_json()
    zone_name = data.get("zone_name")
    node_id = data.get("node_id")

    # Buscar a zona e o nó no banco de dados
    area = Areas.query.filter_by(name=zone_name).first()
    node = Nodes.query.get(node_id)

    if not area or not node:
        return jsonify({"success": False, "error": "Zona ou nó inválido"}), 400

    if node.area_id:
        return jsonify({"success": False, "error": "Este nó já está associado a uma zona!"}), 400

    # Associar o nó à zona
    node.area_id = area.id
    db.session.commit()

    return jsonify({"success": True})


@app.route("/add_column_to_zone", methods=["POST"])
def add_column_to_zone():
    data = request.get_json()
    zone_name = data.get("zone_name")
    column_name = data.get("column_name")

    
    if not zone_name or not column_name:
        return jsonify({"error": "Zona e coluna são obrigatórias"}), 400

    # Buscar zona e coluna no banco de dados
    area = Areas.query.filter_by(name=zone_name).first()
    column = Nodes.query.filter_by(name=column_name).first()

    if not area:
        return jsonify({"error": "Zona não encontrada"}), 404
    if not column:
        return jsonify({"error": "Coluna não encontrada"}), 404

    # Verificar se a coluna já está associada a alguma zona
    if column.area_id:
        return jsonify({"error": "Essa coluna já está associada a outra zona"}), 400

    # Associar a coluna à zona
    column.area_id = area.id
    print(f"Column {column_name} associated with zone {zone_name}")

    db.session.commit()
    send_info([column])

    return jsonify({"success": "Coluna associada com sucesso!"}), 200



# remove column FROM zone
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
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
      
 



@app.route('/update_channel/<int:channel_id>', methods=['POST'])
def update_channel(channel_id):
    # Get the selected type from the form submission
    new_type = request.form.get('channel_type')
    # Ensure the type is valid (check against the enum)
    if new_type not in [channel.value for channel in ChannelType]:
        return redirect('/')

    # Find the channel by ID and update its type
    channel = db.session.get(Channels, channel_id)

    if not channel:
        return redirect('/')
    
    try:
        channel.type = ChannelType[new_type]  # Update the channel's type
        print(f"Channel {channel_id} updated to {new_type}")
        db.session.commit()  # Save the changes to the database
        return redirect('/')
    except Exception as e:
        return redirect('/')



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
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')

@app.route('/update_column_name', methods=['POST'])
def update_column_name():
    data = request.get_json()
    old_name = data.get('old_name')
    new_name = data.get('new_name')

    if not old_name or not new_name:
        return jsonify({"error": "Nome antigo e novo nome são obrigatórios"}), 400

    try:
        column = Nodes.query.filter_by(name=old_name).first()
        if not column:
            return jsonify({"error": "Coluna não encontrada"}), 404

        column.name = new_name
        db.session.commit()
        return jsonify({"success": "Nome da coluna atualizado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit_playlist/<playlist_name>', methods=['GET', 'POST'])
def edit_playlist(playlist_name):
    if request.method == 'POST':
        data = request.get_json()
        new_name = data.get('new_name')
        song_name = data.get('song_name')
        action = data.get('action')
        playlist = Playlist.query.filter_by(name=playlist_name).first()
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        if new_name:
            playlist.name = new_name
            db.session.commit()
            return jsonify({"success": True}), 200
        elif song_name and action:
            song = Song.query.filter_by(name=song_name).first()
            if not song:
                return jsonify({"error": "Song not found"}), 404
            if action == 'add':
                if song not in playlist.songs:
                    playlist.songs.append(song)
                    db.session.commit()
                    return jsonify({"success": True}), 200
                else:
                    return jsonify({"error": "Song already in playlist"}), 400
            elif action == 'remove':
                if song in playlist.songs:
                    playlist.songs.remove(song)
                    db.session.commit()
                    return jsonify({"success": True}), 200
                else:
                    return jsonify({"error": "Song not in playlist"}), 400
            else:
                return jsonify({"error": "Invalid action"}), 400
        return jsonify({"error": "Invalid request"}), 400
    else:
        # Fetch playlist songs and all available songs
        playlist = Playlist.query.filter_by(name=playlist_name).first()
        if not playlist:
            # Create a new empty playlist if not found
            playlist = Playlist(name=playlist_name)
            db.session.add(playlist)
            db.session.commit()
            print("DEBUG - Created new playlist:", playlist_name)
        playlist_songs = [song.name for song in playlist.songs]
        all_songs = [song.name for song in Song.query.all()]
        return render_template('edit_playlist.html', playlist_name=playlist_name, playlist_songs=playlist_songs, all_songs=all_songs)
# ...existing code...

@app.route('/add_song', methods=['POST'])
def add_song():
    song_name = request.form['songName']
    song_file = request.files['songFile']
    # Save the song file to the server (implement as needed)
    new_song = Song(name=song_name)
    db.session.add(new_song)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/delete_song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    song = Song.query.get_or_404(song_id)
    db.session.delete(song)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/save_playlist/<playlist_name>', methods=['POST'])
def save_playlist(playlist_name):
    data = request.get_json()
    song_order = data.get('song_order')
    if not song_order:
        return jsonify({"error": "Ordem das músicas é obrigatória"}), 400

    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404

    try:
        # Clear existing songs and add them in the new order
        db.session.execute(playlist_song.delete().where(playlist_song.c.playlist_id == playlist.id))  # clear old data
        for index, song_name in enumerate(song_order, start=1):
            song = Song.query.filter_by(name=song_name).first()
            if song:
                insert_stmt = playlist_song.insert().values(
                    playlist_id=playlist.id,
                    song_id=song.id,
                    song_order=index
                )
                db.session.execute(insert_stmt)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_playlist/<playlist_name>', methods=['DELETE'])
def delete_playlist(playlist_name):
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    try:
        db.session.delete(playlist)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_song/<int:song_id>', methods=['POST'])
def update_song(song_id):
    data = request.get_json()
    new_name = data.get('new_name')
    if not new_name:
        return jsonify({"error": "Novo nome é obrigatório"}), 400
    song = Song.query.get(song_id)
    if not song:
        return jsonify({"error": "Música não encontrada"}), 404
    try:
        song.name = new_name
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/get_songs', methods=['GET'])
def get_songs():
    songs = Song.query.all()
    return jsonify({"songs": [song.name for song in songs]})

@app.route('/playlist_order/<playlist_name>', methods=['GET'])
def playlist_order(playlist_name):
    playlist = Playlist.query.filter_by(name=playlist_name).first()
    if not playlist:
        return jsonify({"error": "Playlist não encontrada"}), 404
    query = db.session.query(
        playlist_song.c.song_order, Song.name
    ).join(Song, playlist_song.c.song_id == Song.id
    ).filter(playlist_song.c.playlist_id == playlist.id
    ).order_by(playlist_song.c.song_order)
    song_order_names = [row[1] for row in query.all()]
    return jsonify({"songs": song_order_names})

@app.route('/add_microphone', methods=['POST'])
def add_microphone():
    data = request.get_json()
    mic_name = data.get('name')
    if not mic_name:
        return jsonify({"error": "Nome do microfone é obrigatório"}), 400
    new_mic = Microphone(name=mic_name)
    db.session.add(new_mic)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/delete_microphone/<int:mic_id>', methods=['DELETE'])
def delete_microphone(mic_id):
    mic = Microphone.query.get_or_404(mic_id)
    db.session.delete(mic)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/sync_microphone/<int:mic_id>', methods=['POST'])
def sync_microphone(mic_id):
    microphone = Microphone.query.get_or_404(mic_id)
    try:
        # Logic to sync the microphone
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    stop_event = threading.Event()
    msg_buffer = queue.Queue()

    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()

    with app.app_context():
        db.create_all()
        ensure_column_song_order()
        create_default_channels()
        
    # socketio.run(app, debug=True)
    app.run(debug=True, port=5001)
    #thread.join()




