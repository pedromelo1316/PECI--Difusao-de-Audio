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
            n = no.no(ip)
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "id=" + str(n.get_id())
                s.sendall(mensagem.encode('utf-8'))
        except ValueError as e:
            if ip in no.no._ips:
                no.no._ips.remove(ip)
            return f"Error adding node: {e}"
        except socket.error:
            if ip in no.no._ips:
                no.no._ips.remove(ip)
            return "Error connecting to the node."
        self.nos[ip] = n
        return f"Node {ip} added successfully."
    def remove_no(self, ip):
        if ip not in self.nos:
            return "Node not found."
        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Node Removed"
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
    
    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
        except ValueError as e:
            return f"Error adding zone: {e}"
        except socket.error:
            return "Communication error while adding zone."
        
        self.zonas[nome] = z
        return f"Zone {nome} added successfully."
    

    def remove_zona(self, nome):
        if nome not in self.zonas:
            return "Zone not found."        
        
        for ip in self.nos:
            self.remove_no_from_zona(ip)
        
        if self.zonas[nome].get_canal() is not None:
            self.zonas[nome].get_canal().remove_zona(self.zonas[nome])

        zona.zona._nomes.remove(nome)
        del self.zonas[nome]
        return "Zone removed successfully."
    

    def add_no_to_zona(self, ip, zona_nome):
        if ip not in self.nos:
            return "Node not found."
        if zona_nome not in self.zonas:
            return "Zone not found."
        if self.nos[ip].get_zona() is not None:
            return f"Node is already in zone: {self.nos[ip].get_zona().get_nome()}"
        
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
            return "Error connecting to the node to add to zone."
            
        self.nos[ip].set_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].add_no(self.nos[ip])
        return f"Node {ip} added to zone {zona_nome} successfully."
    

    def add_nos_to_zona(self, zona_nome, nos):
        nos = nos.split()
        for n in nos:
            r = self.add_no_to_zona(n, zona_nome)
            if "successfully" not in r:
                return f"Failed to add some nodes: {r}"
            return f"All nodes added to zone {zona_nome} successfully."
        

    def remove_no_from_zona(self, ip):
        if ip not in self.nos:
            return "Node not found."
        if self.nos[ip].get_zona() is None:
            return "Node is not in any zone."        
        try:
            port = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, port))
                mensagem = "Removed from zone"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to node: {ip}"
        

        self.nos[ip].get_zona().remove_no(self.nos[ip])
        self.nos[ip].set_zona(None)
        return f"Node {ip} removed from zone successfully."

        

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
            return "Zone not found."
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
            return "Zone not found."
        if self.zonas[zona_nome].get_canal() is None:
            return "Zone has no channel."
                
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

    def info_zona(self, nome):
        if nome not in self.zonas:
            return "Zone not found."
        zona_info = f"Zone {nome}:\n\tChannel: {self.zonas[nome].get_canal()}\n\tNodes: "
        zona_info += ", ".join(n.get_ip() for n in self.zonas[nome].get_nos())
        return zona_info

    def info_no(self, ip):
        if ip not in self.nos:
            return "Node not found."
        return f"Node {ip}:\n\tZone: {self.nos[ip].get_zona()}"

    def get_nos_livres(self):
        livres = []
        for n in self.nos:
            if self.nos[n].get_zona() is None:
                livres.append(n)
        return livres

    def get_nos_em_zonas(self):
        em_zonas = ""
        for n in self.nos:
            if self.nos[n].get_zona() is not None:
                em_zonas += f"\tNode {n}: {self.nos[n].get_zona()}\n"
        return em_zonas
    

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



