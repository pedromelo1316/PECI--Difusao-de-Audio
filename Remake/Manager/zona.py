class zona:
    _nomes = set()  # Conjunto para manter os nomes únicos

    def __init__(self, nome):
        if nome in zona._nomes:
            raise ValueError(f"Zone {nome} already exists")
        self.nome = nome
        self._nomes.add(nome)
        self.nos = []
        self.canal = None

    def add_no(self, no):
        self.nos.append(no)

    def remove_no(self, no):
        self.nos.remove(no)

    def set_canal(self, canal):
        self.canal = canal

    def get_nome(self):
        return self.nome
    
    def get_nos(self):
        return self.nos
    
    def get_canal(self):
        return self.canal
    

    def __str__(self):
        return f"{self.nome}"
    