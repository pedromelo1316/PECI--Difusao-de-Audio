class canal:
    _next_id = 1  # Variável de classe para manter o próximo id disponível
    def __init__(self):
        self.id = canal._next_id
        self.tipo = None
        self.zonas = []

        canal._next_id += 1


    def getTipo(self):
        return self.tipo

    def getZonas(self):
        return self.zonas
    
    def getId(self):
        return self.id
    
    def setTipo(self, tipo):
        self.tipo = tipo

    def setZonas(self, zonas):
        self.zonas = zonas

    def addZona(self, zona):
        self.zonas.append(zona)

    def __str__(self):
        return f"Canal: {self.id} - Tipo: {self.tipo} - Zonas: {self.zonas}"