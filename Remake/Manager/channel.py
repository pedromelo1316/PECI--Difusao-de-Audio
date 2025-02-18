class channel:
    _next_id = 1  # Variável de classe para manter o próximo id disponível
    def __init__(self):
        self.id = channel._next_id
        self.transmission = "LOCAL"
        self.areas = set()

        channel._next_id += 1


    def set_transmission(self, transmission):
        self.transmission = transmission

    def get_transmission(self):
        return self.transmission
    
    def get_id(self):
        return self.id
    
    def add_area(self, area):
        self.areas.add(area)

    def remove_area(self, area):
        self.areas.remove(area)

    def get_areas(self):
        return self.areas
    
    def __str__(self):
        return f"Channel {self.id}"