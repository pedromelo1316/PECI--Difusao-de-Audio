import sqlite3

class NodeDatabase:
    def __init__(self, db_name="nodes.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)   
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT NULL,
                area TEXT DEFAULT NULL        
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area TEXT UNIQUE NOT NULL,
                channel TEXT DEFAULT NULL     
            )
        """)

        self.conn.commit()


# TABELA DE AREA

    def add_area(self, area):
        try:
            self.cursor.execute("INSERT INTO areas (area) VALUES (?)", (area,))
            self.conn.commit()
            return f"Area {area} added successfully."
        except sqlite3.IntegrityError:
            return "Area already exists."  
    
    def add_channel(self, area, channel):
        try:
            self.cursor.execute("UPDATE areas SET channel = ? WHERE area = ?", (channel, area))
            self.conn.commit()
            return f"Area {area} channel set to {channel}."
        except sqlite3.IntegrityError:
            return "Area already exists."


# TABELA DE NODE 
    def add_node(self, ip):
        try:
            self.cursor.execute("INSERT INTO nodes (ip) VALUES (?)", (ip,))
            self.conn.commit()
            return f"Node {ip} added successfully."
        except sqlite3.IntegrityError:
            return "Node already exists."
    
    def add_node_name(self, ip, name):
        self.cursor.execute("UPDATE nodes SET name = ? WHERE ip = ?", (name, ip))
        self.conn.commit()
        return f"Node {ip} renamed to {name}."
    
    def add_node_area(self, ip, area):
        self.cursor.execute("UPDATE nodes SET area = ? WHERE ip = ?", (area, ip))
        self.conn.commit()
        return f"Node {ip} area set to {area}."

    def remove_node(self, ip):
        self.cursor.execute("DELETE FROM nodes WHERE ip = ?", (ip,))
        self.conn.commit()
        return f"Node {ip} removed."

    def get_nodes(self):
        self.cursor.execute("SELECT * FROM nodes")
        return self.cursor.fetchall()

    def get_node_by_ip(self, ip):
        self.cursor.execute("SELECT * FROM nodes WHERE ip = ?", (ip,))
        return self.cursor.fetchone()

    def rename_node(self, ip, new_name):
        self.cursor.execute("UPDATE nodes SET name = ? WHERE ip = ?", (new_name, ip))
        self.conn.commit()
        return f"Node {ip} renamed to {new_name}."

    def close(self):
        self.conn.close()
        