import socket
import zona
import no
import canal

class manager:
    def __init__(self):
        self.alocados = []
        self.livres = []
        self.zonas = []
        self.zonas_livres = []
        self.zonas_alocadas = []
        self.canais = []


    def add_canal(self):
        c = canal.canal()
        self.canais.append(c)
        return c

    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
        except ValueError:
            return False
        
        if z not in self.zonas:
            self.zonas_livres.append(z)
            self.zonas.append(z)
            return True
        return False
    

    def add_no(self, ip):
        try:
            n = no.no(ip)
        except ValueError:
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
                            return True
                        

    def add_zona_canal(self, nome, id):
        for z in self.zonas:
            if z.getNome() == nome:
                for c in self.canais:
                    if c.getId() == id:
                        z.setCanal(c)
                        c.addZona(z)
                        return True
        return False
    
    def get_zonas(self):
        return self.zonas
    
    def get_zonas_livres(self):
        return self.zonas_livres
    
    def get_nos_livres(self):
        return self.livres
    
    def get_nos_alocados(self):
        return self.alocados
    
    def get_nos(self):
        return self.livres + self.alocados
    

    def get_canais(self):
        return self.canais