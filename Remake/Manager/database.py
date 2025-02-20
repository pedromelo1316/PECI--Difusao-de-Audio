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
                nodes TEXT DEFAULT NULL,
                channel TEXT DEFAULT NULL     
            )
        """)

        self.conn.commit()


# TABELA DE AREA

    def add_area(self, area):
        self.cursor.execute("INSERT INTO areas (area) VALUES (?)", (area,))
        self.conn.commit()
        return f"Area {area} added successfully."

    def remove_area(self, area):
        self.cursor.execute("DELETE FROM areas WHERE area = ?", (area,))
        self.conn.commit()
        return f"Area {area} removed."

    def get_areas(self):
        self.cursor.execute("SELECT area FROM areas")
        result = self.cursor.fetchall()
        return [area[0] for area in result]
     
    
    def add_channel(self, area, channel):
        try:
            self.cursor.execute("UPDATE areas SET channel = ? WHERE area = ?", (channel, area))
            self.conn.commit()
            return f"Area {area} channel set to {channel}."
        except sqlite3.IntegrityError:
            return "Area already exists."


# TABELA DE NODE 
    def add_node_ip(self, ip):
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
    
    def add_node_area(self, ip, area, name):
        self.cursor.execute("UPDATE nodes SET area = ? WHERE ip = ?", (area, ip))
        self.conn.commit()

        self.cursor.execute("SELECT nodes FROM areas WHERE area = ?", (area,))
        result = self.cursor.fetchone()

        if result:
            existing_nodes = result[0]
            if existing_nodes:
                new_nodes = f"{existing_nodes},{name}"
            else:
                new_nodes = name

            # Atualiza a coluna nodes na tabela areas
            self.cursor.execute("UPDATE areas SET nodes = ? WHERE area = ?", (new_nodes, area))
            self.conn.commit()
    

        return f"Node {ip} set to area {area}."

    def remove_node(self, name):
        self.cursor.execute("DELETE FROM nodes WHERE name = ?", (name,))
        self.conn.commit()
        return f"Node {name} removed."
    
    def rename_node(self, ip, new_name):
        self.cursor.execute("UPDATE nodes SET name = ? WHERE ip = ?", (new_name, ip))  # Buscar pelo IP
        self.conn.commit()
        
        if self.cursor.rowcount == 0:
            return f"Error: Node with IP '{ip}' not found or already named '{new_name}'."
        
        return f"Node with IP {ip} renamed to {new_name}."
    
    def remove_node_area(self, ip):
        self.cursor.execute("UPDATE nodes SET area = NULL WHERE ip = ?", (ip,))
        self.conn.commit()

        return f"Node {ip} removed from area."
    
    
    def info_node(self, ip):
        self.cursor.execute("SELECT * FROM nodes WHERE ip = ?", (ip,))
        result = self.cursor.fetchone()
        if not result:
            return None
        return {
            "ip": result[1],
            "name": result[2],
            "area": result[3]
        }
    

    def get_nodes(self):
        self.cursor.execute("SELECT name FROM nodes")
        result = self.cursor.fetchall()
        return [row[0] for row in result]  # Retorna apenas os nomes como lista de strings

    

    def get_ip_by_name(self, name):
        self.cursor.execute("SELECT ip FROM nodes WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]  # Retorna apenas o IP como string
        return None  # Retorna None se o nó não for encontrado
    
    def get_name_by_ip(self, ip):
        self.cursor.execute("SELECT name FROM nodes WHERE ip = ?", (ip,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        return None
    
    def get_nodes_in_area(self):
        self.cursor.execute("SELECT nodes FROM areas")
        result = self.cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        return ""
    
    def get_free_nodes(self):
        self.cursor.execute("SELECT name FROM nodes WHERE area IS NULL")
        result = self.cursor.fetchall()
        return [node[0] for node in result]


    def close(self):
        self.conn.close()
        