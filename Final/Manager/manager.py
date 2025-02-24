from database import manage_db
import socket
import json

class manager:


    def __init__(self):
        manage_db.init_db()





    def send_info(self, list):

        dic = {}

        for name in list:
            node = manage_db.get_node_by_name(name)

            volume, channel = None, None

            if node[3] != None:
                volume = manage_db.get_area_volume(node[3])

                channel = manage_db.get_area_channel(node[3])

            dic[node[2]] = {"channel": channel, "volume": volume}



        dic = json.dumps(dic)



        #mandar broadcast do dic
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.sendto(dic.encode('utf-8'), ('<broadcast>', 8081))

        return True


    # NODE


    def add_node(self, name, mac):

        macs = manage_db.get_node_macs()

        macs = [i[0] for i in macs]


        names = manage_db.get_node_names()

        names = [i[0] for i in names]

  
        if mac in macs:
            raise Exception("MAC already in use")
        
        
        if name in names:
            new_name = name
            
            for i in range(1, 1000):
                new_name = name + str(i)
                if new_name not in names:
                    name = new_name
                    break

                if i == 999:
                    raise Exception("Limit of nodes with the same name reached")

        manage_db.add_node(name, mac)


        return True
    

    def remove_node(self, name):
        
        
        if not manage_db.check_name(name):
            raise Exception(f"Node {name} not found")
        manage_db.remove_node(name)

        return True
    

    def rename_node(self, old_name, new_name):
        
        if not manage_db.check_name(old_name):
            raise Exception(f"Node {old_name} not found")
        manage_db.change_node_name(old_name, new_name)
        

        return True
    


    def get_node_info(self, name):
        
        if not manage_db.check_name(name):
            raise Exception(f"Node {name} not found")
        node = manage_db.get_node_by_name(name)


        mac = node[2]
        aread_id = node[3]
        area = manage_db.get_area_by_id(aread_id) if aread_id != None else None

        return f"\n\tMac: {mac}\n\tArea: {area}"
    
















    #AREA

    def add_area(self, name):
        
        if manage_db.check_area(name):
            raise Exception(f"Area {name} already exists")
        manage_db.add_area(name)

        return True


    def remove_area(self, name):
        
        if not manage_db.check_area(name):
            raise Exception(f"Area {name} not found")
        manage_db.remove_area(name)

        return True
    

    def get_area_info(self, name):

        if not manage_db.check_area(name):
            raise Exception(f"Area {name} not found")

        nodes = manage_db.get_nodes_by_area(name)


        volume = manage_db.get_area_volume(name)

        channel = manage_db.get_area_channel(name)

        return f"\n\tNodes: " + ", ".join(nodes) + f"\n\tVolume: {volume}\n\tChannel: {channel}"
    


    def add_node_to_area(self, node_name, area_name):
        
        if not manage_db.check_name(node_name):
            raise Exception(f"Node {node_name} not found")
        if not manage_db.check_area(area_name):
            raise Exception(f"Area {area_name} not found")
        manage_db.add_node_to_area(area_name,node_name)

        return True
    

    def remove_node_from_area(self, node_name, area_name):
        
        if not manage_db.check_name(node_name):
            raise Exception(f"Node {node_name} not found")
        if not manage_db.check_area(area_name):
            raise Exception(f"Area {area_name} not found")
        manage_db.remove_node_from_area(area_name,node_name)

        return True
    
            
        
    def add_channel_to_area(self, area_name, channel_name):
        
        if not manage_db.check_area(area_name):
            raise Exception(f"Area {area_name} not found")
        if not manage_db.check_channel(channel_name):
            raise Exception(f"Channel {channel_name} not found")
        manage_db.add_channel_to_area(area_name,channel_name)

        return True



    def remove_area_channel(self, area_name):

        if not manage_db.check_area(area_name):
            raise Exception(f"Area {area_name} not found")

        manage_db.remove_area_channel(area_name)

        return True
    

    def set_area_volume(self, area_name, volume):
        
        if not manage_db.check_area(area_name):
            raise Exception(f"Area {area_name} not found")
        
        volume = float(volume)

        if volume < 0.0 or volume > 2.0:
            raise Exception("Volume must be between 0 and 2.0")

        manage_db.change_area_volume(area_name,volume)

        return True
    
    












    # CHANNEL 

    def change_channel_transmission(self, channel_id, transmission):
        
        if not manage_db.check_channel(channel_id):
            raise Exception(f"Channel {channel_id} not found")
        manage_db.change_channel_type(channel_id,transmission)



    def get_channel_info(self, channel_id):
        
        if not manage_db.check_channel(channel_id):
            raise Exception(f"Channel {channel_id} not found")
        channel = manage_db.get_channel_by_id(channel_id)

        return f"\n\tTransmission: {channel[1]}"