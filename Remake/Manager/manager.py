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
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        
        if self.nos[ip].get_zona() is not None:
            self.nos[ip].get_zona().remove_no(self.nos[ip])

        no.no._ips.remove(ip)

        del self.nos[ip]
        print("Nó removido com sucesso")
        
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
        if nome not in self.zonas:
            print("Zona não encontrada")
            return False
        
        if self.zonas[nome].get_canal() is not None:
            self.zonas[nome].get_canal().remove_zona(self.zonas[nome])

        for no in self.zonas[nome].get_nos():
            no.set_zona(None)

        zona.zona._nomes.remove(nome)

        del self.zonas[nome]
        print("Zona removida com sucesso")
    
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
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        if zona_nome not in self.zonas:
            print("Zona não encontrada")
            return False
        self.nos[ip].set_zona(None)
        self.zonas[zona_nome].remove_no(self.nos[ip])
        print("Nó removido da zona com sucesso")
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
        print(f"Canal {canal_id}: \n\t{self.canais[canal_id].get_transmissao()} \n\t{self.canais[canal_id].get_zonas()}")


    def info_zona(self, zona_nome):
        if zona_nome not in self.zonas:
            print("Zona não encontrada")
            return False
        print(f"Zona {zona_nome}: \n\t{self.zonas[zona_nome].get_nos()} \n\t{self.zonas[zona_nome].get_canal()}")


    def info_no(self, ip):
        if ip not in self.nos:
            print("Nó não encontrado")
            return False
        print(f"Nó {ip}: \n\t{self.nos[ip].get_zona()}")

    
    
