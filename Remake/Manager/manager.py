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
        msg = f"Canal {c.get_id()} iniciado com sucesso no modo {c.get_transmissao()}"
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
            return f"Erro ao adicionar nó: {e}"
        except socket.error:
            if ip in no.no._ips:
                no.no._ips.remove(ip)
            return "Erro ao conectar com o nó."

        self.nos[ip] = n
        return f"Nó {ip} adicionado com sucesso."

    def remove_no(self, ip):
        if ip not in self.nos:
            return "Nó não encontrado."

        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Nó Removido"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return "Erro ao conectar com o nó para remoção."
        
        if self.nos[ip].get_zona() is not None:
            self.nos[ip].get_zona().remove_no(self.nos[ip])

        if ip in no.no._ips:
            no.no._ips.remove(ip)
        if ip in self.nos:
            del self.nos[ip]
        return "Nó removido com sucesso."

    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
        except ValueError as e:
            return f"Erro ao adicionar zona: {e}"
        except socket.error:
            return "Erro na comunicação para adicionar zona."

        self.zonas[nome] = z
        return f"Zona {nome} adicionada com sucesso."

    def remove_zona(self, nome):
        if nome not in self.zonas:
            return "Zona não encontrada."
        
        
        for ip in self.nos:
            self.remove_no_from_zona(ip)
        
        if self.zonas[nome].get_canal() is not None:
            self.zonas[nome].get_canal().remove_zona(self.zonas[nome])

        zona.zona._nomes.remove(nome)
        del self.zonas[nome]
        return "Zona removida com sucesso."

    def add_no_to_zona(self, ip, zona_nome):
        if ip not in self.nos:
            return "Nó não encontrado."
        if zona_nome not in self.zonas:
            return "Zona não encontrada."
        if self.nos[ip].get_zona() is not None:
            return f"Nó já está na zona: {self.nos[ip].get_zona().get_nome()}"
        
        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "zona=" + zona_nome
                if self.zonas[zona_nome].get_canal() is not None:
                    mensagem += ",canal=" + str(self.zonas[zona_nome].get_canal().get_id())
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return "Erro ao conectar com o nó para adicionar à zona."

        self.nos[ip].set_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].add_no(self.nos[ip])
        return f"Nó {ip} adicionado à zona {zona_nome} com sucesso."

    def add_nos_to_zona(self, zona_nome, nos):
        nos = nos.split()
        for n in nos:
            r = self.add_no_to_zona(n, zona_nome)
            if "sucesso" not in r:
                return f"Falha ao adicionar alguns nós: {r}"
        return f"Todos os nós adicionados à zona {zona_nome} com sucesso."

    def remove_no_from_zona(self, ip):
        if ip not in self.nos:
            return "Nó não encontrado."
        if self.nos[ip].get_zona() is None:
            return "Nó não está em nenhuma zona."
        
        try:
            port = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, port))
                mensagem = "Removido da zona"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Erro ao conectar com o nó: {ip}"

        self.nos[ip].get_zona().remove_no(self.nos[ip])
        self.nos[ip].set_zona(None)
        return f"Nó {ip} removido da zona com sucesso."
        

    def remove_nos_from_zona(self, zona_nome, nos):
        nos_list = nos.split()
        for n in nos_list:
            r = self.remove_no_from_zona(n)
            if "sucesso" not in r:
                return f"Falha ao remover alguns nós: {r}"
        return f"Todos os nós removidos da zona {zona_nome} com sucesso."

    def assign_canal_to_zona(self, zona_nome, canal_id):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Canal não encontrado."
        if zona_nome not in self.zonas:
            return "Zona não encontrada."
        self.zonas[zona_nome].set_canal(self.canais[canal_id])
        self.canais[canal_id].add_zona(self.zonas[zona_nome])
        try:
            for n in self.zonas[zona_nome].get_nos():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "canal=" + str(canal_id)
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Erro ao conectar com o nó: {n.get_ip()}"
        return "Canal atribuído à zona com sucesso."
    
    def assign_zonas_to_canal(self, canal_id, zonas):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Canal não encontrado."
        zonas_list = zonas.split()
        for z in zonas_list:
            r = self.assign_canal_to_zona(z, canal_id)
            if "sucesso" not in r:
                return f"Falha ao atribuir canal a algumas zonas: {r}"
        return f"Canal atribuído a todas as zonas com sucesso."
    

    def remove_canal_from_zona(self, zona_nome):
        if zona_nome not in self.zonas:
            return "Zona não encontrada."
        if self.zonas[zona_nome].get_canal() is None:
            return "Zona não possui canal."
        
        canal_id = self.zonas[zona_nome].get_canal().get_id()
        self.zonas[zona_nome].get_canal().remove_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].set_canal(None)
        try:
            for n in self.zonas[zona_nome].get_nos():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "Canal removido"
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Erro ao conectar com o nó: {n.get_ip()}"
        return f"Canal {canal_id} removido da zona com sucesso."
    

    def remove_zonas_from_canal(self, canal_id, zonas):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Canal não encontrado."
        zonas_list = zonas.split()
        for z in zonas_list:
            r = self.remove_canal_from_zona(z)
            if "sucesso" not in r:
                return f"Falha ao remover canal de algumas zonas: {r}"
        return f"Canal removido de todas as zonas com sucesso."

    def assign_transmissao_to_canal(self, canal_id, tipo):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Canal não encontrado."
        if tipo not in ["LOCAL", "TRANSMISSAO", "VOZ"]:
            return "Tipo inválido."
        self.canais[canal_id].set_transmissao(tipo)
        return "Transmissão atribuída ao canal com sucesso."

    def info_canal(self, canal_id):
        canal_id = int(canal_id)
        if canal_id not in self.canais:
            return "Canal não encontrado."
        info = f"Canal {canal_id}:\n\tTransmissão: {self.canais[canal_id].get_transmissao()}\n\tZonas: "
        zonas_list = []
        for z in self.canais[canal_id].get_zonas():
            zonas_list.append(z.get_nome())
        info += ", ".join(zonas_list)
        return info

    def info_zona(self, nome):
        if nome not in self.zonas:
            return "Zona não encontrada."
        zona_info = f"Zona {nome}:\n\tCanal: {self.zonas[nome].get_canal()}\n\tNós: "
        zona_info += ", ".join(n.get_ip() for n in self.zonas[nome].get_nos())
        return zona_info

    def info_no(self, ip):
        if ip not in self.nos:
            return "Nó não encontrado."
        return f"Nó {ip}:\n\tZona: {self.nos[ip].get_zona()}"

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
                em_zonas += f"\tNó {n}: {self.nos[n].get_zona()}\n"
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



