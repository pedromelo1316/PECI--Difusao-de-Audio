class canal:
    _next_id = 1  # Variável de classe para manter o próximo id disponível
    def __init__(self):
        self.id = canal._next_id
        self.transmissao = "LOCAL"
        self.zonas = set()

        canal._next_id += 1


    def set_transmissao(self, transmissao):
        self.transmissao = transmissao

    def get_transmissao(self):
        return self.transmissao
    
    def get_id(self):
        return self.id
    
    def add_zona(self, zona):
        self.zonas.add(zona)

    def remove_zona(self, zona):
        self.zonas.remove(zona)

    def get_zonas(self):
        return self.zonas
    
    def __str__(self):
        return f"Canal {self.id}"