import curses
import time
import manager
import socket
import threading
import queue
import os






def get_input(win, prompt, pos_y, pos_x):
    """
    Exibe o prompt na janela 'win' na posição definida e permite que o usuário
    digite, mostrando os caracteres ao lado do prompt. Retorna o valor
    quando Enter é pressionado.
    """
    win.addstr(pos_y, pos_x, prompt)
    win.refresh()
    curses.echo()
    inp = win.getstr(pos_y, pos_x + len(prompt) + 1).decode('utf-8')
    curses.noecho()
    return inp

# New helper to print multiline messages with border offset
def add_msg(win, msg, start_y=1, start_x=2):
    lines = msg.split("\n")
    for i, line in enumerate(lines, start=start_y):
        win.addstr(i, start_x, line)


def main(stdscr, stop_event):
    curses.curs_set(1)
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Define área de mensagens (3 linhas) e área para menu (restante)
    msg_height = height // 4
    menu_height = height - msg_height

    # Cria janelas: menu_win para menus e msg_win para exibição de mensagens
    menu_win = curses.newwin(menu_height, width, 0, 0)
    msg_win  = curses.newwin(msg_height, width, menu_height, 0)
    

    while not stop_event.is_set():
        # Menu principal
        menu_win.clear()
        menu_win.border()
        menu_win.addstr(1, 2, "1 - Manage nodes")
        menu_win.addstr(2, 2, "2 - Manage zones")
        menu_win.addstr(3, 2, "3 - Manage channels")
        menu_win.addstr(4, 2, "0 - Exit")
        menu_win.refresh()

        op = get_input(menu_win, "Choose an option: ",6,2)


        if op == "1":
            # Submenu de nós
            while True:
                menu_win.clear()
                menu_win.border()

                menu_win.addstr(1, 2, "1 - Detect Nodes")
                menu_win.addstr(2, 2, "2 - Add Node")
                menu_win.addstr(3, 2, "3 - Remove Node")
                menu_win.addstr(4, 2, "4 - Rename Node")
                menu_win.addstr(5, 2, "5 - Node Information")
                menu_win.addstr(6, 2, "6 - Add Node to Area")
                menu_win.addstr(7, 2, "7 - Remove Node from Area")
                menu_win.addstr(8, 2, "0 - Back")

                menu_win.refresh()

                op2 = get_input(menu_win, "Choose an option:", 9, 2)


                if op2 == "1":
                    msg = "Nodes detected: "
                    msg_win.clear()
                    msg_win.border()
                    detected = set()
                    detection_port = 9090

                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(3)  # Timeout para não esperar indefinidamente
                    message = b"Detect"
                    sock.sendto(message, ("<broadcast>", detection_port))

                    # Loop de deteção com interface reduzida
                    while True:
                        menu_win.clear()
                        menu_win.border()
                        menu_win.addstr(1, 2, "Detecting new nodes...")  # "Detecting new nodes..."
                        menu_win.refresh()
                        time.sleep(0.5)

                        try:

                            data, addr = sock.recvfrom(1024)  # Espera pela resposta
                            
                            if data.decode('utf-8').strip() == "hello":
                                if m.add_no(addr[0]) == f"Node {addr[0]} added successfully.":

                                    detected.add(addr[0])
                                    msg += f"{addr[0]} "
                                    add_msg(msg_win, msg)
                                    msg_win.refresh()

                        except socket.timeout:
                            break

                    
                    sock.close()
                    msg = "Detection ended. Nodes: " + ", ".join(detected) if detected else "Detection ended. No new nodes detected."
                    msg_win.clear()
                    msg_win.border()
                    add_msg(msg_win, msg)
                    msg_win.refresh()

                elif op2 == "2":
                    ip = get_input(menu_win, "Node IP:", 10, 2)
                    msg = m.add_no(ip)
                    

                elif op2 == "3":
                    nodes = [node.getName() for node in m.get_nos().values()]
                    if not nodes:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Nodes")  

                        msg_win.refresh()
                        continue
                    
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Nodes: " + ", ".join(nodes))
                    msg_win.refresh()
            
                    node_name = get_input(menu_win, "Node Name:", 10, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.remove_node(node_ip)


                elif op2 == "4":
                    nodes = [node.getName() for node in m.get_nos().values()]
                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Nodes: " + ", ".join(nodes))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 10, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                        
                    new_name = get_input(menu_win, "New Name:", 11, 2)
                    msg = m.rename_node(node_ip, new_name)

                elif op2 == "5":
                    nos = [node.getName() for node in m.get_nos().values()]
                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Nodes: " + ", ".join(nos))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 10, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.info_no(node_ip)

                elif op2 == "6":
                    free_nodes = m.get_free_nodes()
                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Free Nodes: " + " ".join(free_nodes))
                    msg_win.addstr(2, 2, "Areas: " + ", ".join(list(m.get_zonas().keys())))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 10, 2)
                    area_name = get_input(menu_win, "Area Name:", 11, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.add_node_to_area(node_ip, area_name)

                elif op2 == "7":
                    nodes_in_area = m.get_nodes_in_Area()
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Area Nodes: \n" + nodes_in_area)
                    msg_win.refresh()
                    node_name = get_input(menu_win, "Node Name:", 10, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.remove_node_from_area(node_ip)


                elif op2 == "0":
                    break
                else:
                    msg = "Invalid option."  # "Invalid option."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()
        

        elif op == "2":
            # Submenu de zonas
            while True:
                menu_win.clear()
                menu_win.border()
                menu_win.addstr(1, 2, "1 - Add Area")
                menu_win.addstr(2, 2, "2 - Remove Area")
                menu_win.addstr(3, 2, "3 - Area information")
                menu_win.addstr(4, 2, "4 - Add nodes to Area")
                menu_win.addstr(5, 2, "5 - Remove nodes from Area")
                menu_win.addstr(6, 2, "6 - Assign channel to Area")
                menu_win.addstr(7, 2, "7 - Remove channel from Area")
                menu_win.addstr(8, 2, "0 - Back")
                menu_win.refresh()

                op2 = get_input(menu_win, "Choose an option:", 10, 2)  # Prompt: "Choose an option:"
                if op2 == "1":
                    zona_nome = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    msg = m.add_zona(zona_nome)

                elif op2 == "2":
                    areas = list(m.get_zonas().keys())

                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue

                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))
                    msg_win.refresh()
            
                    area_name = get_input(menu_win, "Area Name:", 12, 2)
                    msg = m.remove_area(area_name)

                elif op2 == "3":
                    areas = list(m.get_zonas().keys())
                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))
                    msg_win.refresh()
                    area_nome = get_input(menu_win, "Area Name:", 12, 2)
                    msg = m.info_area(area_nome)


                elif op2 == "4":
                    areas = list(m.get_zonas().keys())
                    free_nodes = m.get_free_nodes()

                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    if not free_nodes:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No free nodes.")  # "No free nodes."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()

                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))
                    msg_win.addstr(2, 2, "Free Nodes: " + " ".join(free_nodes))
                    msg_win.refresh()
                    area_nome = get_input(menu_win, "Area Name:", 12, 2)
                    name_list = get_input(menu_win, "Nodes Names (seperated by spaces):", 13, 2)
                    msg = m.add_nos_to_zona(area_nome, name_list)


                elif op2 == "5":
                    zonas = list(m.get_zonas().keys())
                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(zonas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Name Area:", 12, 2)  # Prompt: "Zone name:"
                    nos_em_zona = [n.get_ip() for n in m.get_zonas()[zona_nome].get_nos()]

                    if not nos_em_zona:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, f"No nodes in area {zona_nome}.")  # "No nodes in zone [zone name]."
                        msg_win.refresh()
                        continue

                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Nodes in {zona_nome}: " + ", ".join(nos_em_zona))  # "Nodes in [zone name]: [list of nodes]"
                    msg_win.refresh()
                    ips = get_input(menu_win, "Node IPs (separated by space):", 13, 2)  # Prompt: "Node IPs (separated by space):"
                    msg = m.remove_nos_from_zona(zona_nome, ips)

                elif op2 == "6":
                    zonas = list(m.get_zonas().keys())
                    canais = [str(c+1) for c in range(num_canais)]

                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(zonas))  # "Zones: [list of zones]"
                    msg_win.addstr(2, 2, "Channels: " + ", ".join(canais))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    canal = get_input(menu_win, "Channel:", 13, 2)  # Prompt: "Channel:"
                    msg = m.assign_canal_to_zona(zona_nome, canal)

                elif op2 == "7":
                    zonas = list(m.get_zonas().keys())
                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(zonas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    msg = m.remove_canal_from_zona(zona_nome)

                elif op2 == "0":
                    break
                else:
                    msg = "Invalid option."  # "Invalid option."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()
        

        elif op == "3":
            # Submenu for channels
            while True:
                menu_win.clear()
                menu_win.border()
                menu_win.addstr(1, 2, "1 - Change channel transmission")
                menu_win.addstr(2, 2, "2 - Channel information")
                menu_win.addstr(3, 2, "3 - Assign zones to channel")
                menu_win.addstr(4, 2, "4 - Remove zones from channel")
                menu_win.addstr(5, 2, "0 - Back")
                menu_win.refresh()

                op2 = get_input(menu_win, "Choose an option:", 7, 2)  # Prompt: "Choose an option:"
                if op2 == "1":
                    canais = [str(c+1) for c in range(num_canais)]
                    tipos = ["LOCAL", "TRANSMISSION", "VOICE"]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(canais))  # "Channels: [list of channels]"
                    msg_win.addstr(2, 2, "Types: " + ", ".join(tipos))  # "Types: [list of types]"
                    msg_win.refresh()
                    canal = get_input(menu_win, "Channel:", 9, 2)  # Prompt: "Channel:"
                    tipo = get_input(menu_win, "Transmission type:", 10, 2)  # Prompt: "Transmission type:"
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue
                    msg = m.assign_transmissao_to_canal(canal, tipo)

                elif op2 == "2":
                    canais = [str(c+1) for c in range(num_canais)]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(canais))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    canal = get_input(menu_win, "Channel:", 7, 2)  # Prompt: "Channel:"
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue
                    msg = m.info_canal(canal)

                elif op2 == "3":
                    canais = [str(c+1) for c in range(num_canais)]
                    zonas = list(m.get_zonas_livres())
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(canais))  # "Channels: [list of channels]"
                    msg_win.addstr(2, 2, "Zones: " + ", ".join(zonas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    canal = get_input(menu_win, "Channel:", 7, 2)  # Prompt: "Channel:"
                    zona = get_input(menu_win, "Zone:", 8, 2)  # Prompt: "Zone:"
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue
                    msg = m.assign_zonas_to_canal(canal, zona)

                elif op2 == "4":
                    canais = [str(c+1) for c in range(num_canais)]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(canais))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    canal = get_input(menu_win, "Channel:", 7, 2)  # Prompt: "Channel:"
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue

                    zonas_em_canal = [zona.get_nome() for zona in list(m.get_canais()[canal].get_zonas())]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Zones in {canal}: " + ", ".join(zonas_em_canal))  # "Zones in [channel]: [list of zones]"
                    msg_win.refresh()
                    zonas = get_input(menu_win, "Zones (separated by space):", 8, 2)  # Prompt: "Zones (separated by space):"
                    msg = m.remove_zonas_from_canal(canal, zonas)

                elif op2 == "0":
                    break
                else:
                    msg = "Invalid option."  # "Invalid option."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()

        elif op == "0":
            stop_event.set()  # Signal threads to stop
            break
        else:
            msg = "Invalid option."  # "Invalid option."
            msg_win.clear()
            msg_win.border()
            add_msg(msg_win, msg)
            msg_win.refresh()


def get_local(q, stop_event=None):
    while not stop_event.is_set():
        # Gera 1024 bytes aleatórios
        q.put(os.urandom(1024))
        time.sleep(0.5)
    print("get_local encerrado.")

def get_transmissao(q, stop_event=None):
    while not stop_event.is_set():
        q.put(os.urandom(1024))
        time.sleep(0.5)
    print("get_transmissao encerrado.")

def get_voz(q, stop_event=None):
    while not stop_event.is_set():
        q.put(os.urandom(1024))
        time.sleep(0.5)
    print("get_voz encerrado.")



def play_audio(port=8081, stop_event=None, q_local=None, q_transmissao=None, q_voz=None):
    # Aguarda até que cada fila tenha 10 pacotes (10*1024 bytes)

    while q_local.qsize() < 10 or q_transmissao.qsize() < 10 or q_voz.qsize() < 10:
        if stop_event.is_set():
            return
        time.sleep(0.1)

    while not stop_event.is_set():
        # Lê um pacote de cada fila a cada 0.5s
        packet_local = q_local.get()
        packet_trans = q_transmissao.get()
        packet_voz   = q_voz.get()
        # Monta a mensagem combinando os dados de cada fila
        message = packet_local + packet_trans + packet_voz
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message, ("<broadcast>", port))
        sock.close()
        time.sleep(0.5)
    print("play_audio encerrado.")








if __name__ == "__main__":
    num_canais = 3
    m = manager.manager()
    for i in range(num_canais):
        m.add_canal()

    stop_event = threading.Event()

    # Cria as queues para cada função de "get"
    q_local = queue.Queue()
    q_transmissao = queue.Queue()
    q_voz = queue.Queue()

    # Thread do menu (curses)
    t_menu = threading.Thread(
        target=curses.wrapper, 
        args=(lambda stdscr: main(stdscr, stop_event),),
        daemon=True
    )
    t_menu.start()

    # Threads para encher as queues a cada 0.5s
    t_local = threading.Thread(target=get_local, args=(q_local, stop_event), daemon=True)
    t_trans = threading.Thread(target=get_transmissao, args=(q_transmissao, stop_event), daemon=True)
    t_voz   = threading.Thread(target=get_voz, args=(q_voz, stop_event), daemon=True)
    t_local.start()
    t_trans.start()
    t_voz.start()

    # Thread do play_audio que aguarda as queues e envia pacotes a cada 0.5s
    t_play = threading.Thread(target=play_audio, args=(8081, stop_event, q_local, q_transmissao, q_voz), daemon=True)
    t_play.start()

    t_menu.join()
    t_local.join()
    t_trans.join()
    t_voz.join()
    t_play.join()