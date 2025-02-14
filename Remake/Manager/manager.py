import socket
import zona
import no
import canal

class manager:
    def __init__(self):
        self.nos = dict()
        self.zonas = dict()
        self.canais = dict()
        

    def add_no(self, ip):
        try:
            n = no.no(ip)
            print("Nó adicionado com sucesso")
        except ValueError as e:
            print(e)
            return None
        self.nos[ip] = n
        return n
    
    def remove_no(self, ip):
        pass
        
    def add_zona(self, nome):
        try:
            z = zona.zona(nome)
            print("Zona adicionada com sucesso")
        except ValueError as e:
            print(e)
            return None
        self.zonas[nome] = z
        return z
    
    def remove_zona(self, nome):
        pass
    
    def add_canal(self):
        c = canal.canal()
        self.canais[c.get_id()] = c
        print(f"Canal {c.get_id()} inciado com sucesso")
        return c
    

    def add_no_to_zona(self, ip, zona_nome):
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        if zona_nome not in self.zonas:
            print("Zona não encontrada")
            return False
        self.nos[ip].set_zona(self.zonas[zona_nome])
        self.zonas[zona_nome].add_no(self.nos[ip])
        print("Nó adicionado à zona com sucesso")
        return True
    

    def remove_no_from_zona(self, ip, zona_nome):
        pass

    def assign_canal_to_zona(self, canal_id, zona_nome):
        pass

    
    
