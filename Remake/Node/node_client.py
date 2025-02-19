class node_client:
    def __init__(self):
        self.id = None
        self.area = None
        self.channel = None
        self.name = None


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

    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name