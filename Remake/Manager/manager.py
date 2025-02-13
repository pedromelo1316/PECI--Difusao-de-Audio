import socket
import zona
import no

class manager:
    def __init__(self):
        self.alocados = []
        self.livres = []
        self.zonas = []

    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
        except ValueError:
            return False
        
        if z not in self.zonas:
            self.zonas.append(z)
            return True
        return False

    def add_no(self, ip):
        try:
            n = no.no(ip)

            # Enviar via socket para o nó
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Conexão estabelecida com o manager: " + str(n.getId())
                s.sendall(mensagem.encode('utf-8'))
            
        except ValueError:
            return False
        except socket.error:
            return False
    
        if n not in self.livres:
            self.livres.append(n)
            return True
        return False

    def add_no_zona(self, ip, nome):
        for z in self.zonas:
            if z.getNome() == nome:
                for n in self.livres:
                    if n.getIp() == ip:
                        if z.add_no(n):
                            self.livres.remove(n)
                            self.alocados.append(n)

                            # Enviar via socket para o nó
                            PORT = 8080
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                s.connect((ip, PORT))
                                mensagem = "Zona: " + z.getNome()
                                s.sendall(mensagem.encode('utf-8'))

                            return True
        return False
    
    def remove_no_zona(self, ip, nome):
        for z in self.zonas:
            if z.getNome() == nome:
                for n in self.alocados:
                    if n.getIp() == ip:
                        if z.remove_no(n):
                            self.alocados.remove(n)
                            self.livres.append(n)

                            PORT = 8080
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                s.connect((ip, PORT))
                                mensagem = "Removido da zona: " + z.getNome()
                                s.sendall(mensagem.encode('utf-8'))
                                
                            return True
        return False
    
    def get_zonas(self):
        return self.zonas
    
    def get_nos_livres(self):
        return self.livres
    
    def get_nos_alocados(self):
        return self.alocados