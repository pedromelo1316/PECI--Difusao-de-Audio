
from flask import Flask, render_template, url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
import threading
import queue
import time
import socket


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

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

@app.route('/', methods=['GET']) # metodos para enviar e receber dados
def index():
    
    nodes = Nodes.query.order_by(Nodes.id).all() # podemos metrer tbm .first()
    return render_template("index.html",nodes=nodes)



@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Nodes.query.get_or_404(id) 
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Houve um problema ao deletar a tarefa'

@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    node = Nodes.query.get_or_404(id)
    if request.method == 'POST':
        node.name = request.form['name']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Houve um problema ao atualizar a tarefa'
    else:
        return render_template('update.html',node=node)    



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
                        name = name.upper()
                        new_node = Nodes(name=name, mac=mac)
                        db.session.add(new_node)
                        db.session.commit()      

                    msg_buffer.put(f"Node {name} connected")
                    server_socket.sendto(b"OK", addr)

                except Exception as e:
                    if str(e) == "Limit of nodes with the same name reached":
                        msg_buffer.put("Limit of nodes with the same name reached")
                        server_socket.sendto(b"Limit of nodes with the same name reached", addr)
                    elif str(e) == "MAC already in use":
                        node = db.session.query(Nodes).filter(Nodes.mac == mac).first()
                        name = node.name
                        msg_buffer.put(f"Node {name} reconected")
                        server_socket.sendto(b"OK", addr)
                    else:
                        msg_buffer.put(f"Error: {e}")
                        server_socket.sendto(b"Error " + str(e).encode('utf-8'), addr)

                #send_info([name])





if __name__ == '__main__':
    
    
    stop_event = threading.Event()
    msg_buffer = queue.Queue()

    thread = threading.Thread(target=detect_new_nodes, args=(stop_event, msg_buffer), daemon=True)
    thread.start()

    
    with app.app_context():
        db.create_all()
    app.run(debug=False)


    thread.join()

    


