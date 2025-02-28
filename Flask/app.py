from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import subprocess
import threading
import queue
import time
import socket




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)



class Nodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    mac = db.Column(db.String(200), nullable=True)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    def __repr__(self):
        return '<Task %r>' % self.id

class Areas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nodes = db.relationship('Nodes', backref='area', lazy=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return '<Task %r>' % self.id

class Channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return '<Task %r>' % self.id

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
                name, mac = data.split(',')

                try:
                    with app.app_context():
                        if db.session.query(Nodes).filter(Nodes.mac == mac).first():
                            raise Exception("MAC already in use")
                    
                        name = name.upper()
                        new_node = Nodes(name=name, mac=mac)
                        db.session.add(new_node)
                        db.session.commit()
                        socketio.emit('update', {'action': 'add', 'id': new_node.id, 'name': new_node.name})

                    msg_buffer.put(f"Node {name} connected")
                    server_socket.sendto(b"OK", addr)
                except Exception as e:
                    if str(e) == "Limit of nodes with the same name reached":
                        msg_buffer.put("Limit of nodes with the same name reached")
                        server_socket.sendto(b"Limit of nodes with the same name reached", addr)
                    elif str(e) == "MAC already in use":
                        with app.app_context():
                            node = db.session.query(Nodes).filter(Nodes.mac == mac).first()
                        
                        name = node.name
                        msg_buffer.put(f"Node {name} reconnected")
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
        socketio.emit('update', {'action': 'update', 'id': node.id, 'name': node.name})
        return redirect('/')
    except Exception as e:
        return str(e), 500


@app.route('/add_channel', methods=['POST'])
def add_channel():
    channel_type = request.form['type']
    try:
        new_channel = Channels(type=channel_type)
        db.session.add(new_channel)
        db.session.commit()
        socketio.emit('update', {'action': 'add', 'id': new_channel.id, 'type': new_channel.type})
        return redirect('/')
    except Exception as e:
        return str(e), 500

@app.route('/add_area', methods=['POST'])
def add_area():
    area_name = request.form.get('name')
    channel_id = request.form.get('channel_id')
    volume = request.form.get('volume')
    
    if not area_name:
        flash("Area name is required", "error")
        return redirect('/')
    
    try:
        print(f"Adding area: {area_name}")
        new_area = Areas(name=area_name, channel_id=channel_id, volume=volume)
        db.session.add(new_area)
        db.session.commit()
        print(f"Area {area_name} added with ID: {new_area.id}")
        socketio.emit('update', {'action': 'add', 'id': new_area.id, 'name': new_area.name})
        return redirect('/')
    except Exception as e:
        print(f"Error adding area: {e}")
        flash(str(e), "error")
        return redirect('/')



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
        socketio.emit('update', {'action': 'delete', 'id': area.id})
        return redirect('/')
    except Exception as e:
        flash(str(e), "error")
        return redirect('/')
    

    




        

if __name__ == '__main__':
    stop_event = threading.Event()
    msg_buffer = queue.Queue()

    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()

    with app.app_context():
        db.create_all()
    socketio.run(app, debug=False)

    thread.join()




