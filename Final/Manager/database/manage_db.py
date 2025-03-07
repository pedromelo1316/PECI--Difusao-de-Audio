import sqlite3




def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS nodes (id INTEGER PRIMARY KEY, name TEXT, mac TEXT, area_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS areas (id INTEGER PRIMARY KEY, name TEXT, channel_id INTEGER, nodes TEXT, volume FLOAT)")
    c.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, type TEXT)")
    conn.commit()

    
#NODE


def add_node(name, mac, area_id=None):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO nodes (name, mac) VALUES (?, ?)", (name, mac))
    conn.commit()


def get_nodes():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes")
    return c.fetchall()


def get_node_by_name(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes WHERE name=?", (name,))
    return c.fetchone()


def get_node_by_id(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes WHERE id=?", (id,))
    return c.fetchone()


def get_node_by_mac(mac):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes WHERE mac=?", (mac,))
    return c.fetchone()


def remove_node(name):

    area_name = get_node_area(name)[1]
    if area_name is not None:
        remove_node_from_area(area_name, name)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM nodes WHERE name=?", (name,))
    conn.commit()


    


def remove_area_from_node(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE nodes SET area_id=NULL WHERE name=?", (name,))
    conn.commit()


def add_area_to_node(name, area_name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (area_name,))
    area = c.fetchone()
    c.execute("UPDATE nodes SET area_id=? WHERE name=?", (area[0], name))
    conn.commit()



def change_node_name(name, new_name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE nodes SET name=? WHERE name=?", (new_name, name))
    conn.commit()


def get_node_area(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes WHERE name=?", (name,))
    node = c.fetchone()
    if node[3] is None:
        return None
    c.execute("SELECT * FROM areas WHERE id=?", (node[3],))
    return c.fetchone()




def get_node_names():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name FROM nodes")
    return c.fetchall()


def get_node_macs():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT mac FROM nodes")
    return c.fetchall()



def check_name(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM nodes WHERE name=?", (name,))
    
    if c.fetchone():
        return True
    return False











#AREA


def add_area(name, channel_id=None, nodes="", volume=1.0):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO areas (name, channel_id, nodes, volume) VALUES (?, ?, ?, ?)", (name, channel_id, nodes, volume))
    conn.commit()

def get_areas():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas")
    return c.fetchall()

def get_area_by_name(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    return c.fetchone()

def get_area_by_id(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE id=?", (id,))
    return c.fetchone()

def remove_area(name):

    nodes = get_nodes_by_area(name)
    for node in nodes:
        remove_area_from_node(node)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM areas WHERE name=?", (name,))
    conn.commit()


def change_area_name(name, new_name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE areas SET name=? WHERE name=?", (new_name, name))
    conn.commit()

def change_area_volume(name, volume):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE areas SET volume=? WHERE name=?", (volume, name))
    conn.commit()

def get_area_volume(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    return c.fetchone()[4]

def remove_node_from_area(name, node_name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    area = c.fetchone()
    nodes = area[3].split(",")
    nodes.remove(node_name)
    c.execute("UPDATE areas SET nodes=? WHERE name=?", (",".join(nodes), name))
    conn.commit()
    c.execute("SELECT * FROM nodes WHERE name=?", (node_name,))
    node = c.fetchone()
    c.execute("UPDATE nodes SET area_id=NULL WHERE name=?", (node_name,))
    conn.commit()


def add_node_to_area(name, node_name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    area = c.fetchone()
    nodes = area[3].split(",")
    nodes[-1] = f"{node_name},"
    c.execute("UPDATE areas SET nodes=? WHERE name=?", (",".join(nodes), name))
    conn.commit()
    c.execute("SELECT * FROM nodes WHERE name=?", (node_name,))
    node = c.fetchone()
    c.execute("UPDATE nodes SET area_id=? WHERE name=?", (area[0], node[1]))
    conn.commit()



def get_nodes_by_area(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    area = c.fetchone()
    nodes = area[3].split(",")
    return nodes[:-1]


def remove_area_channel(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE areas SET channel_id=NULL WHERE name=?", (name,))
    conn.commit()



def add_channel_to_area(name, channel_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE areas SET channel_id=? WHERE name=?", (channel_id, name))
    conn.commit()



def get_area_names():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name FROM areas")
    return c.fetchall()


def get_area_channel(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    area = c.fetchone()
    if not area:
        return None
    if area[2] is None:
        return None
    c.execute("SELECT * FROM channels WHERE id=?", (area[2],))
    return c.fetchone()


def check_area(name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE name=?", (name,))
    
    if c.fetchone():
        return True
    return False



def get_nodes_not_in_areas():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name FROM nodes WHERE area_id IS NULL")
    return c.fetchall()

#CHANNEL


def init_channels(num):
    #se o numero de canais for diferente de num apagar todos e criar num novos
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels")
    channels = c.fetchall()
    if len(channels) != num:
        c.execute("DELETE FROM channels")
        for i in range(num):
            c.execute("INSERT INTO channels (type) VALUES (?)", ("LOCAL",))
        conn.commit()


    


def get_channels():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels")
    return c.fetchall()


def get_channel_by_id(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE id=?", (id,))
    return c.fetchone()

def change_channel_type(id, type):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE channels SET type=? WHERE id=?", (type, id))
    conn.commit()


def remove_channel(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE id=?", (id,))
    conn.commit()


def get_channel_names():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM channels")
    return c.fetchall()



def check_channel(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE id=?", (id,))
    
    if c.fetchone():
        return True
    return False


def get_channel_type(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE id=?", (id,))
    return c.fetchone()[1]



def get_nodes_by_channel_type(type):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE type=?", (type,))
    channels = c.fetchall()
    nodes = []
    for channel in channels:
        c.execute("SELECT * FROM areas WHERE channel_id=?", (channel[0],))
        areas = c.fetchall()
        for area in areas:
            nodes += get_nodes_by_area(area[1])
    return nodes



def get_nodes_by_channel(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas WHERE channel_id=?", (id,))
    areas = c.fetchall()
    nodes = []
    for area in areas:
        nodes += get_nodes_by_area(area[1])
    return nodes
