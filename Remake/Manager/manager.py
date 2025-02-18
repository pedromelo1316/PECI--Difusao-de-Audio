import socket
import zona
import no
import canal



class manager:
    def __init__(self):
        self.nos = dict()
        self.zonas = dict()
        self.canais = dict()

    def add_canal(self):
        c = canal.canal()
        self.canais[c.get_id()] = c
        msg = f"Channel {c.get_id()} started successfully in {c.get_transmissao()} mode"        
        return msg

    def add_no(self, ip):
        try:
            if ip in no.no._ips:
                return "IP already exists."
            n = no.no(ip)

            
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Add Node " + str(n.get_id())
                s.sendall(mensagem.encode('utf-8'))

                data = s.recv(1024)
                received_name = data.decode('utf-8').split('=')[1]
                n.setName(received_name)
                
        except ValueError as e:
            if ip in no.no._ips:
                no.no._ips.remove(ip)
            return f"Error adding node: {e}"
        except socket.error:
            if ip in no.no._ips:
                no.no._ips.remove(ip)

            return "Error connecting to node."

        self.nos[ip] = n
        return f"Node {ip} added successfully."

    def remove_node(self, ip):
        if ip not in self.nos:
            return "Node not found."


        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))

                mensagem = "Node removed"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return "Error connecting to the node for removal."
        

        if self.nos[ip].get_zona() is not None:
            self.nos[ip].get_zona().remove_no(self.nos[ip])

        if ip in no.no._ips:
            no.no._ips.remove(ip)
        if ip in self.nos:
            del self.nos[ip]
        return "Node removed successfully."
    


    def rename_node(self, ip, name):
        if ip not in self.nos:
            return "Node not found."
        
        old_name = self.nos[ip].getName()
        self.nos[ip].setName(name)
        return f"Node name {old_name} changed to {name}."


    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
        except ValueError as e:
            return f"Error adding zone: {e}"
        except socket.error:
            return "Communication error while adding zone."
        
        self.zonas[nome] = z
        return f"Area {nome} added successfully."
    

    def remove_area(self, nome):
        if nome not in self.zonas:
            return "Area not found."        
        
        for ip in self.nos:
            self.remove_node_from_area(ip)
        
        if self.zonas[nome].get_canal() is not None:
            self.zonas[nome].get_canal().remove_zona(self.zonas[nome])

        zona.zona._nomes.remove(nome)
        del self.zonas[nome]
        return "Area removed successfully."
    

    def add_node_to_area(self, ip, zona_nome):
        if ip not in self.nos:
            return "Node not found."
        if zona_nome not in self.zonas:

            return "Area not found."
        if self.nos[ip].get_zona() is not None:
            return f"Node is in Area: {self.nos[ip].get_zona().get_nome()}"

        
        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "zone=" + zona_nome
                if self.zonas[zona_nome].get_canal() is not None:
                    mensagem += ",channel=" + str(self.zonas[zona_nome].get_canal().get_id())
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:

            return "Error connecting to the node to add to the area."


        self.nos[ip].set_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].add_no(self.nos[ip])
        return f"Node {ip} added to area {zona_nome} successfully."
    

    def add_nos_to_zona(self, zona_nome, nos):
        nos = nos.split()
        for n in nos:
            r = self.add_no_to_zona(n, zona_nome)
            if "successfully" not in r:
                return f"Failed to add some nodes: {r}"
            return f"All nodes added to area {zona_nome} successfully."
        

    def remove_node_from_area(self, ip):
        if ip not in self.nos:
            return "Node not found."
        if self.nos[ip].get_zona() is None:

            return "Node is not in any Area."
        
        node = self.nos[ip]

        try:
            port = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, port))

                mensagem = "Area removed"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to Node: {node.getName()}"

        
        node.get_zona().remove_no(self.nos[ip])
        node.set_zona(None)
        return f"Node {node.getName()} removed from Area successfully."

        

    def remove_nos_from_zona(self, zona_nome, nos):
        nos_list = nos.split()
        for n in nos_list:
            r = self.remove_no_from_zona(n)
            if "successfully" not in r:
                return f"Failed to remove some nodes: {r}"
        return f"All nodes removed from zone {zona_nome} successfully."
    

    def assign_canal_to_zona(self, zona_nome, canal_id):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Channel not found."
        if zona_nome not in self.zonas:
            return "Area not found."
        self.zonas[zona_nome].set_canal(self.canais[canal_id])
        self.canais[canal_id].add_zona(self.zonas[zona_nome])
        try:
            for n in self.zonas[zona_nome].get_nos():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "channel=" + str(canal_id)
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to node: {n.get_ip()}"
        return "Channel assigned to zone successfully."


    def assign_zonas_to_canal(self, canal_id, zonas):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Channel not found."
        zonas_list = zonas.split()
        for z in zonas_list:
            r = self.assign_canal_to_zona(z, canal_id)
            if "successfully" not in r:
                return f"Failed to assign channel to some zones: {r}"
        return f"Channel assigned to all zones successfully."    

    def remove_canal_from_zona(self, zona_nome):
        if zona_nome not in self.zonas:
            return "Area not found."
        if self.zonas[zona_nome].get_canal() is None:
            return "Area has no channel."
                
        canal_id = self.zonas[zona_nome].get_canal().get_id()
        self.zonas[zona_nome].get_canal().remove_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].set_canal(None)
        try:
            for n in self.zonas[zona_nome].get_nos():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "Channel removed"
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to node: {n.get_ip()}"
        return f"Channel {canal_id} removed from zone successfully."    

    def remove_zonas_from_canal(self, canal_id, zonas):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Channel not found."
        zonas_list = zonas.split()
        for z in zonas_list:
            r = self.remove_canal_from_zona(z)
            if "successfully" not in r:
                return f"Failed to remove channel from some zones: {r}"
        return f"Channel removed from all zones successfully."
    
    def assign_transmissao_to_canal(self, canal_id, tipo):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Channel not found."
        if tipo not in ["LOCAL", "TRANSMISSAO", "VOZ"]:
            return "Invalid type."
        self.canais[canal_id].set_transmissao(tipo)
        return "Transmission assigned to channel successfully."
    
    def info_canal(self, canal_id):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Channel not found."
        info = f"Channel {canal_id}:\n\tTransmission: {self.canais[canal_id].get_transmissao()}\n\tZones: "
        zonas_list = []
        for z in self.canais[canal_id].get_zonas():
            zonas_list.append(z.get_nome())
        info += ", ".join(zonas_list)
        return info

    def info_area(self, nome):
        if nome not in self.zonas:

            return "Area not found."
        area_info = f"Area {nome}:\n\Channel: {self.zonas[nome].get_canal()}\n\tNodes: "
        area_info += ", ".join(n.getName() for n in self.zonas[nome].get_nos())
        return area_info


    def info_no(self, ip):
        if ip not in self.nos:
            return "Node not found."

        return self.nos[ip].__str__()


    def get_free_nodes(self):
        livres = []
        for n in self.nos:
            if self.nos[n].get_zona() is None:
                livres.append(self.nos[n].getName())
        return livres

    def get_nodes_in_Area(self):
        in_area = ""
        for n in self.nos:

            node = self.nos[n]
            if node.get_zona() is not None:
                in_area += f"\tNode {node.getName()}: {node.get_zona()}\n"
        return in_area

    

    def get_canais(self): 
        return self.canais
    

    def get_zonas(self):
        return self.zonas

    def get_nos(self):
        return self.nos
    
    
    
    def get_zonas_livres(self):
        livres = []
        for z in self.zonas:
            if self.zonas[z].get_canal() is None:
                livres.append(z)
        return livres


    def get_nodeIP_byName(self, name):
        for n in self.nos:
            if self.nos[n].getName() == name:
                return n
        return None
       
