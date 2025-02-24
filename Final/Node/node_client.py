class node_client:
    def __init__(self, name, mac):
        self.area = None
        self.channel = None
        self.name = name
        self.volume = None
        self.mac = mac



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
        if volume >= 0.1 and volume <= 2.0:
            self.volume = volume

    def getVolume(self):
        return self.volume
    

    def __str__(self):
        return f"Node {self.name} - {self.mac}"