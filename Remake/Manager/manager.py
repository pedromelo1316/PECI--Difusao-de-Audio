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
        print(f"Canal {c.get_id()} iniciado com sucesso no modo {c.get_transmissao()}")
        return c
        

    def add_no(self, ip):
        try:
            n = no.no(ip)

            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Conexão estabelecida com o manager: " + str(n.get_id())
                s.sendall(mensagem.encode('utf-8'))

        except ValueError as e:
            print(e)
            return None
        
        except socket.error:
            print("Erro ao conectar com o nó")
            return False

        self.nos[ip] = n

        print("Nó adicionado com sucesso")

        return n
    
    def remove_no(self, ip):
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        
        if self.nos[ip].get_zona() is not None:
            self.nos[ip].get_zona().remove_no(self.nos[ip])

        no.no._ips.remove(ip)

        del self.nos[ip]
        print("Nó removido com sucesso")

        #fazer depois...
        
    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
            print("Zona adicionada com sucesso")
        except ValueError as e:
            print(e)
            return None
        except socket.error:
            return False


        self.zonas[nome] = z
        return z
    
    def remove_zona(self, nome):
        if nome not in self.zonas:
            print("Zona não encontrada")
            return False
        

        #talvez trocar para broadcast
        port = 8080
        for n in self.nos:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n, port))
                    mensagem = "Removido da zona: " + nome
                    s.sendall(mensagem.encode('utf-8'))
            except socket.error:
                print("Erro ao conectar com o nó: ", n.get_ip())
                return False
        
        
        
        if self.zonas[nome].get_canal() is not None:
            self.zonas[nome].get_canal().remove_zona(self.zonas[nome])

        for no in self.zonas[nome].get_nos():
            no.set_zona(None)

        zona.zona._nomes.remove(nome)

        del self.zonas[nome]
        print("Zona removida com sucesso")
        return True



    

    def add_no_to_zona(self, ip, zona_nome):
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        if zona_nome not in self.zonas:
            print("Zona não encontrada")
            return False
        
        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Zona: " + zona_nome
                if self.zonas[zona_nome].get_canal() is not None:
                    mensagem += "; Canal: " + str(self.zonas[zona_nome].get_canal().get_id())
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return False

        self.nos[ip].set_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].add_no(self.nos[ip])
        print("Nó adicionado à zona com sucesso")
        return True
    

    def assign_canal_to_zona(self, canal_id, zona_nome):
        if canal_id not in self.canais:
            print("Canal não encontrado")
            return False
        if zona_nome not in self.zonas:
            print("Zona não encontrada")
            return False
        self.zonas[zona_nome].set_canal(self.canais[canal_id])
        self.canais[canal_id].add_zona(self.zonas[zona_nome])
        print("Canal atribuído à zona com sucesso")


        #trocar para broadcast talvez
        try:  
            for n in self.zonas[zona_nome].get_nos():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "Canal: " + str(canal_id)
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return False

        return True
    

    def assign_transmissao_to_canal(self, canal_id, tipo):
        if canal_id not in self.canais:
            print("Canal não encontrado")
            return False
        if tipo not in ["LOCAL", "TRANSMISSAO", "VOZ"]:
            print("Tipo inválido")
            return False
        self.canais[canal_id].set_transmissao(tipo)
        print("Transmissão atribuída ao canal com sucesso")
        return True
    
    def info_canal(self, canal_id):
        if canal_id not in self.canais:
            print("Canal não encontrado")
            return False
        print(f"Canal {canal_id}: \n\tTransmissão: {self.canais[canal_id].get_transmissao()} \n\tZonas: ", end="")

        for z in self.canais[canal_id].get_zonas():

            print(z.get_nome(), end=", ")

        print()

    def info_zona(self, nome):
        if nome not in self.zonas:
            print("Zona não encontrada")
            return False
        print(f"Zona {nome}: \n\tCanal: {self.zonas[nome].get_canal()} \n\tNós: ", end="")

        for n in self.zonas[nome].get_nos():
            print(n.get_ip(), end=", ")

        print()

    def info_no(self, ip):
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        print(f"Nó {ip}: \n\tZona: {self.nos[ip].get_zona()}")




    
    
