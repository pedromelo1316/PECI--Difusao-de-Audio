from database import manage_db



class manager:


    def __init__(self):
        manage_db.init_db()



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
            
        
    












    # CHANNEL    
    
    def add_channel(self):
        manage_db.add_channel("LOCAL")