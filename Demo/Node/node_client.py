class node_client:
    def __init__(self, name, mac):
        self.area = None
        self.channel = None
        self.name = name
        self.volume = None
        self.mac = mac
        self.hostIp = None



    def getMac(self):
        return self.mac

    def getId(self):
        return self.id
    
    def getArea(self):
        return self.area
    
    def getChannel(self):
        return self.channel
    
    def setId(self, id):
        self.id = id

    def setArea(self, area):
        self.area = area

    def setChannel(self, channel):
        self.channel = channel
    
    def getName(self):
        return self.name
    
    def setVolume(self, volume):
        if volume == None:
            self.volume = None
        elif volume >= 0 and volume <= 2.0:
            self.volume = volume

    def getVolume(self):
        return self.volume
    
    def setHostIp(self, ip):
        self.hostIp = ip

    def getHostIp(self):
        return self.hostIp
    
    

    def __str__(self):
        return f"Node {self.name} - {self.mac}"