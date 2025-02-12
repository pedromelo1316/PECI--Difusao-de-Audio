class no:
    _next_id = 1  # Variável de classe para manter o próximo id disponível
    _ips = set()  # Conjunto para manter os IPs únicos

    def __init__(self, ip):
        if ip in no._ips:
            raise ValueError("IP já existe")
        self.ip = ip
        self.zona = None
        self.id = no._next_id
        no._next_id += 1
        self.alocado = False
        no._ips.add(ip)

    def alocar(self, zona):
        if self.alocado:
            return False
        self.alocado = True
        self.zona = zona
        return True

    def desalocar(self):
        if not self.alocado:
            return False
        self.alocado = False
        self.zona = None
        return True

    def getIp(self):
        return self.ip

    def getId(self):
        return self.id

    def getZona(self):
        return self.zona

    def getAlocado(self):
        return self.alocado

    def __str__(self):
        return f"{self.ip} - {self.id} - {self.zona.getNome() if self.zona else 'Livre'}"