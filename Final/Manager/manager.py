from database import manage_db
import socket
import json

class manager:


    def __init__(self):
        manage_db.init_db()





    def send_info(self, list, status="ON"):

        dic = {}

        for name in list:
            node = manage_db.get_node_by_name(name)

            volume, channel = None, None

            if node[3] != None:
                volume = manage_db.get_area_volume(node[3])

                channel = manage_db.get_area_channel(node[3])

            dic[node[2]] = {"status": status, "channel": channel, "volume": volume}



        dic = json.dumps(dic)



        #mandar broadcast do dic
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.sendto(dic.encode('utf-8'), ('<broadcast>', 8081))

        print("work")
        exit()
        return True


    # NODE


    def add_node(self, name, mac):

        macs = manage_db.get_node_macs()

        macs = [i[0] for i in macs]


        names = manage_db.get_node_names()

        names = [i[0] for i in names]

  
        if mac in macs:
            self.send_info([name])
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

        self.send_info([name])

        return True
    

    def remove_node(self, name):
        manage_db.remove_node(name)



        return True
            
        


    
    












    # CHANNEL    
    
    def add_channel(self):
        manage_db.add_channel("LOCAL")