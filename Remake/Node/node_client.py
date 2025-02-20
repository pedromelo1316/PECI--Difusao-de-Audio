class node_client:
    def __init__(self):
        self.id = None
        self.area = None
        self.channel = None
        self.name = None
        self.volume = 1.0


    def getId(self):
        return self.id
    
    def getArea(self):
        return self.area
    
    def getChannel(self):
        return self.channel
    
    def setVolume(self, volume):
        self.volume = max(0.1, min(2.0, volume))  # Mantém volume entre 0.1 e 2.0

    def getVolume(self):
        return self.volume

    
    def setId(self, id):
        self.id = id

    def setArea(self, area):
        self.area = area

    def setChannel(self, channel):
        self.channel = channel

    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name