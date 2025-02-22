from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from Manager.manager import *
from Manager.area import *
from Manager.node_server import *
from Manager.channel import *
from flask_wtf.csrf import CSRFProtect
from forms import AddNodeForm, RemoveNodeForm, AddAreaForm, RemoveAreaForm



# para dar run tenho de dar python3 app.py mas tbm tenho de ter um para o node_server_main.py 


# dps se calhar tentar fazer com que seja so preciso dar run ao app.py 



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
csrf = CSRFProtect(app)
m = manager()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = m.get_nodes()
    return jsonify(nodes)

@app.route('/add_node', methods=['GET', 'POST'])
def add_node():
    form = AddNodeForm()
    if form.validate_on_submit():
        ip = form.ip.data
        result = m.add_node(ip)
        flash(result)
        return redirect(url_for('add_node'))
    return render_template('add_node.html', form=form)

@app.route('/remove_node', methods=['GET', 'POST'])
def remove_node():
    form = RemoveNodeForm()
    if form.validate_on_submit():
        ip = form.ip.data
        result = m.remove_node(ip)
        flash(result)
        return redirect(url_for('remove_node'))
    return render_template('remove_node.html', form=form)


@app.route('/areas', methods=['GET'])
def get_areas():
    areas = m.get_areas()
    return render_template('areas.html', areas=areas)

@app.route('/add_area', methods=['GET', 'POST'])
def add_area():
    form = AddAreaForm()
    if form.validate_on_submit():
        name = form.name.data
        result = m.add_area(name)
        flash(result)
        return redirect(url_for('add_area'))
    return render_template('add_area.html', form=form)

@app.route('/remove_area', methods=['GET', 'POST'])
def remove_area():
    form = RemoveAreaForm()
    if form.validate_on_submit():
        name = form.name.data
        result = m.remove_area(name)
        flash(result)
        return redirect(url_for('remove_area'))
    return render_template('remove_area.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)