from enum import Enum
from flask import Flask, render_template, request, redirect, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import subprocess
import threading
import queue
import time
import socket




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
    
def create_default_channels():
    ##add channels if less than 3
    if db.session.query(Channels).count() < 3:
        for channel in ChannelType:
            new_channel = Channels(type=channel)
            db.session.add(new_channel)
            db.session.commit()



@app.route('/', methods=['GET'])
def index():
    nodes = Nodes.query.order_by(Nodes.id).all()
    areas = Areas.query.order_by(Areas.id).all()
    channels = Channels.query.order_by(Channels.id).all()
    return render_template("index.html", nodes=nodes,areas=areas,channels=channels)

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Nodes.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        socketio.emit('update', {'action': 'delete', 'id': id})
        return redirect('/')
    except:
        return 'Houve um problema ao deletar a tarefa'
    
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

                        new_node = Nodes(name=node_name, mac=node_mac, ip=node_ip)
                        db.session.add(new_node)
                        db.session.commit()
                        

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
        flash(f"Area {area_name} removed", "success")
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')

    

@app.route('/update_volume', methods=['POST'])
def update_volume():
    area_name = request.form.get('name')
    new_volume = request.form.get('volume')

    area = Areas.query.filter_by(name=area_name).first()
    if not area:
        flash("Area not found", "error")
        return redirect('/')
    
    try:
        area.volume = new_volume
        print(f"Volume updated to {new_volume} for area {area_name}")
        db.session.commit()
        return redirect('/')
    except Exception as e:
        
        return redirect('/')


@app.route('/get_nodes')
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
    print(f"Coluna {column_name} associada à zona {zone_name}")

    db.session.commit()

    return jsonify({"success": "Coluna associada com sucesso!"}), 200



# remove column FROM zone
@app.route("/remove_column_from_zone", methods=["POST"])
def remove_column_from_zone():
    data = request.get_json()

    if not data or "zone_name" not in data or "column_name" not in data:
        return jsonify({"error": "Zone and column are required"}), 400

    zone_name = data["zone_name"]
    column_name = data["column_name"]

    # Buscar a coluna na BD
    area = Areas.query.filter_by(name=zone_name).first()
    if not area:
        return jsonify({"error": "Zone not found"}), 404
    column = Nodes.query.filter_by(name=column_name, area_id=area.id).first()

    if not column:
        return jsonify({"error": "Column not found"}), 404
    
    try:       
        column.area_id = None  
        db.session.commit()
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
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')


'''
corrigir isto dps

@app.route("/get_columns", methods=["GET"])
def get_columns():
    columns = Nodes.query.all()
    return jsonify([
        {"id": column.id, "name": column.name, "zone_id": column.zone_id}
        for column in columns
    ])

@app.route("/get_column", methods=["GET"])
def get_column():
    column_name = request.args.get("name")
    column = Nodes.query.filter_by(name=column_name).first()
    
    if not column:
        return jsonify({"error": "Coluna não encontrada"}), 404
    
    return jsonify({"id": column.id, "name": column.name, "zone_id": column.zone_id})

@app.route("/get_zones", methods=["GET"])
def get_zones():
    zones = Areas.query.all()
    return jsonify([
        {"id": zone.id, "name": zone.name, "columns": [
            {"id": col.id, "name": col.name} for col in Nodes.query.filter_by(zone_id=zone.id)
        ]}
        for zone in zones
    ])

'''     

if __name__ == '__main__':
    stop_event = threading.Event()
    msg_buffer = queue.Queue()

    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()

    with app.app_context():
        db.create_all()
        create_default_channels()
    socketio.run(app, debug=False)

    thread.join()




