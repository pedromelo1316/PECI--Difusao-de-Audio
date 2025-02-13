class zona:
    _nomes = set()  # Conjunto para manter os nomes únicos

    def __init__(self, nome):
        if nome in zona._nomes:
            raise ValueError("Nome da zona já existe")
        self.nome = nome
        self.nos = []
        self.canal = None
        zona._nomes.add(nome)

    def add_no(self, no):
        if no not in self.nos and no.alocar(self):
            self.nos.append(no)
            return True
        return False

    def remove_no(self, no):
        if no in self.nos and no.desalocar():
            self.nos.remove(no)
            return True
        return False

    def getNome(self):
        return self.nome

    def getNos(self):
        return self.nos
    
    def getCanal(self):
        return self.canal
    
    def setCanal(self, canal):
        self.canal = canal
    


    def __str__(self):
        return f"{self.nome} - {[n.getId() for n in self.nos]} - {self.canal}"