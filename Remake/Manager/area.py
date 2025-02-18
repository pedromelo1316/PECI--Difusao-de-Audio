class area:
    _names = set()  # Conjunto para manter os names únicos

    def __init__(self, name):
        if name in area._names:
            raise ValueError(f"Area {name} already exists")
        self.name = name
        self._names.add(name)
        self.nodes = []
        self.channel = None

    def add_node(self, node):
        self.nodes.append(node)

    def remove_nde(self, node):
        self.nodes.remove(node)

    def set_channel(self, channel):
        self.channel = channel

    def get_name(self):
        return self.name
    
    def get_nodes(self):
        return self.nodes
    
    def get_channel(self):
        return self.channel
    

    def __str__(self):
        return f"{self.name}"
    