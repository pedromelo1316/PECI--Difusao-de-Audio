import socket
import area
import node_server

import channel



class manager:
    def __init__(self):
        self.nodes = dict()
        self.areas = dict()
        self.channels = dict()

    def add_channel(self):
        c = channel.channel()
        self.channels[c.get_id()] = c
        msg = f"Channel {c.get_id()} started successfully in {c.get_transmission()} mode"        
        return msg

    def add_node(self, ip):
        try:
            if ip in node_server.node_server._ips:
                return "IP already exists."
            n = node_server.node_server(ip)

            
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "Add Node " + str(n.get_id())
                s.sendall(mensagem.encode('utf-8'))

                data = s.recv(1024)
                received_name = data.decode('utf-8').split('=')[1]
                n.setName(received_name)
                
        except ValueError as e:
            if ip in node_server.node_server._ips:
                node_server.node_server._ips.remove(ip)
            return f"Error adding node: {e}"
        except socket.error:
            if ip in node_server.node_server._ips:
                node_server.node_server._ips.remove(ip)

            return "Error connecting to node."

        self.nodes[ip] = n
        return f"Node {ip} added successfully."

    def remove_node(self, ip):
        if ip not in self.nodes:
            return "Node not found."


        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))

                mensagem = "Node Removed"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return "Error connecting to the node for removal."
        

        if self.nodes[ip].get_area() is not None:
            self.nodes[ip].get_area().remove_node(self.nodes[ip])

        if ip in node_server.node_server._ips:
            node_server.node_server._ips.remove(ip)
        if ip in self.nodes:
            del self.nodes[ip]
        return "Node removed successfully."
    


    def rename_node(self, ip, name):
        if ip not in self.nodes:
            return "Node not found."
        
        old_name = self.nodes[ip].getName()
        self.nodes[ip].setName(name)
        return f"Node name {old_name} changed to {name}."


    def add_area(self, name):
        try:
            z = area.area(name)
        except ValueError as e:
            return f"Error adding area: {e}"
        except socket.error:
            return "Communication error while adding area."
        
        self.areas[name] = z
        return f"Area {name} added successfully."
    

    def remove_area(self, name):
        if name not in self.areas:
            return "Area not found."        
        
        for ip in self.nodes:
            self.remove_node_from_area(ip)
        
        if self.areas[name].get_channel() is not None:
            self.areas[name].get_channel().remove_area(self.areas[name])

        area.area._names.remove(name)
        del self.areas[name]
        return "Area removed successfully."
    

    def add_node_to_area(self, ip, area_name):
        if ip not in self.nodes:
            return "Node not found."
        if area_name not in self.areas:

            return "Area not found."
        if self.nodes[ip].get_area() is not None:
            return f"Node is in Area: {self.nodes[ip].get_area().get_name()}"

        
        try:
            PORT = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, PORT))
                mensagem = "area=" + area_name
                if self.areas[area_name].get_channel() is not None:
                    mensagem += ",channel=" + str(self.areas[area_name].get_channel().get_id())
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:

            return "Error connecting to the node to add to the area."


        self.nodes[ip].set_area(self.areas[area_name])
        self.areas[area_name].add_node(self.nodes[ip])
        return f"Node {ip} added to area {area_name} successfully."
    

    def add_nodes_to_area(self, area_name, nodes):
        nodes = nodes.split()
        for n in nodes:
            ip = self.get_nodeIP_byName(n)
            if ip is None:
                return f"Failed to add some nodes: Node {n} not found."
            r = self.add_node_to_area(ip, area_name)
            if "successfully" not in r:
                return f"Failed to add some nodes: {r}"
        return f"All nodes added to area {area_name} successfully."
        

    def remove_node_from_area(self, ip):
        if ip not in self.nodes:
            return "Node not found."
        if self.nodes[ip].get_area() is None:

            return "Node is not in any Area."
        
        node = self.nodes[ip]

        try:
            port = 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((ip, port))

                mensagem = "Area Removed"
                s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to Node: {node.getName()}"

        
        node.get_area().remove_node(self.nodes[ip])
        node.set_area(None)
        return f"Node {node.getName()} removed from Area successfully."

        

    def remove_nodes_from_area(self, area_name, nodes):
        nodes_list = nodes.split()
        for n in nodes_list:
            ip = self.get_nodeIP_byName(n)
            if ip is None:
                return f"Failed to remove some nodes: Node {n} not found."
            r = self.remove_node_from_area(ip)
            if "successfully" not in r:
                return f"Failed to remove some nodes: {r}"
        return f"All nodes removed from zone {area_name} successfully."
    

    def assign_channel_to_area(self, area_name, channel_id):
        channel_id = int(channel_id)
        if channel_id not in self.channels:
            return "Channel not found."
        if area_name not in self.areas:
            return "Area not found."
        self.areas[area_name].set_channel(self.channels[channel_id])
        self.channels[channel_id].add_area(self.areas[area_name])
        try:
            for n in self.areas[area_name].get_nodes():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "channel=" + str(channel_id)
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to node: {n.get_ip()}"
        return "Channel assigned to area successfully."


    def assign_areas_to_channel(self, channel_id, areas):
        channel_id = int(channel_id)
        if channel_id not in self.channels:
            return "Channel not found."
        areas_list = areas.split()
        for z in areas_list:
            r = self.assign_channel_to_area(z, channel_id)
            if "successfully" not in r:
                return f"Failed to assign channel to some areas: {r}"
        return f"Channel assigned to all areas successfully."    

    def remove_channel_from_area(self, area_name):
        if area_name not in self.areas:
            return "Area not found."
        if self.areas[area_name].get_channel() is None:
            return "Area has no channel."
                
        channel_id = self.areas[area_name].get_channel().get_id()
        self.areas[area_name].get_channel().remove_area(self.areas[area_name])
        self.areas[area_name].set_channel(None)
        try:
            for n in self.areas[area_name].get_nodes():
                PORT = 8080
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((n.get_ip(), PORT))
                    mensagem = "Channel Removed"
                    s.sendall(mensagem.encode('utf-8'))
        except socket.error:
            return f"Error connecting to node: {n.get_ip()}"
        return f"Channel {channel_id} removed from area successfully."    

    def remove_areas_from_channel(self, channel_id, areas):
        channel_id = int(channel_id)
        if channel_id not in self.channels:
            return "Channel not found."
        areas_list = areas.split()
        for z in areas_list:
            r = self.remove_channel_from_area(z)
            if "successfully" not in r:
                return f"Failed to remove channel from some areas: {r}"
        return f"Channel removed from all areas successfully."
    
    def assign_transmission_to_channel(self, channel_id, tipo):
        channel_id = int(channel_id)
        if channel_id not in self.channels:
            return "Channel not found."
        if tipo not in ["LOCAL", "TRANSMISSION", "VOZ"]:
            return "Invalid type."
        self.channels[channel_id].set_transmission(tipo)
        return "Transmission assigned to channel successfully."
    
    def info_channel(self, channel_id):
        channel_id = int(channel_id)
        if channel_id not in self.channels:
            return "Channel not found."
        info = f"Channel {channel_id}:\n\tTransmission: {self.channels[channel_id].get_transmission()}\n\tAreas: "
        areas_list = []
        for z in self.channels[channel_id].get_areas():
            areas_list.append(z.get_name())
        info += ", ".join(areas_list)
        return info

    def info_area(self, name):
        if name not in self.areas:

            return "Area not found."
        area_info = f"Area {name}:\n\tChannel: {self.areas[name].get_channel()}\n\tNodes: "
        area_info += ", ".join(n.getName() for n in self.areas[name].get_nodes())
        return area_info


    def info_node(self, ip):
        if ip not in self.nodes:
            return "Node not found."

        return self.nodes[ip].__str__()


    def get_free_nodes(self):
        livres = []
        for n in self.nodes:
            if self.nodes[n].get_area() is None:
                livres.append(self.nodes[n].getName())
        return livres

    def get_nodes_in_Area(self):
        in_area = ""
        for n in self.nodes:

            node = self.nodes[n]
            if node.get_area() is not None:
                in_area += f"\n\tNode {node.getName()}: {node.get_area()}\n"
        return in_area

    

    def get_channels(self): 
        return self.channels
    

    def get_areas(self):
        return self.areas

    def get_nodes(self):
        return self.nodes
    
    
    
    def get_free_areas(self):
        free = []
        for z in self.areas:
            if self.areas[z].get_channel() is None:
                free.append(z)
        return free


    def get_nodeIP_byName(self, name):
        for n in self.nodes:
            if self.nodes[n].getName() == name:
                return n
        return None
    

    def get_nodeName_byIP(self,ip):
        for n in self.nodes:
            if n == ip:
                return self.nodes[n].getName()
        return None
       
