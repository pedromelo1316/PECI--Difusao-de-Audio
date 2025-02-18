import socket
import ipaddress

class node_server:
    _next_id = 1  # Variável de classe para manter o próximo id disponível
    _ips = set()  # Conjunto para manter os IPs únicos
    _names = set()  # Conjunto para manter os nomes únicos

    def __init__(self, ip):
        if ip in node_server._ips:

            raise ValueError("IP already in use")       
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError("Invalid IP address")  

        self.id = node_server._next_id
        self.ip = ip
        self._ips.add(ip)
        self.area = None
        self.name = ip

        node_server._next_id += 1

    def get_id(self):
        return self.id
    
    def get_ip(self):
        return self.ip
    
    def set_area(self, area):
        self.area = area

    def get_area(self):
        return self.area
    
    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name

    
    def __str__(self):
        return f"Node Name: {self.getName()}\nNode ID: {self.get_id()}\nNode IP: {self.get_ip()}\nNode Area: {self.get_area()}"