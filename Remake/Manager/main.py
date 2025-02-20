import curses
import time
import manager
import socket
import threading
import queue
import os
import subprocess
import pyaudio




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

def check_valid_input(msg):
    if msg == "":
        return False
    return True

    

def main(stdscr, stop_event, inicio):

    while not inicio.is_set():
        time.sleep(0.1)

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
        menu_win.addstr(2, 2, "2 - Manage areas")
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

                op2 = get_input(menu_win, "Choose an option:", 10, 2)


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
                                if m.add_node(addr[0]) == f"Node {addr[0]} added successfully.":

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
                    ip = get_input(menu_win, "Node IP:", 12, 2)
                    msg = m.add_node(ip)
                    

                elif op2 == "3":
                    nodes = [node.getName() for node in m.get_nodes().values()]
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
            
                    node_name = get_input(menu_win, "Node Name:", 12, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.remove_node(node_ip)


                elif op2 == "4":
                    nodes = [node.getName() for node in m.get_nodes().values()]
                    msg_win.clear()
                    msg_win.border()

                    if not nodes:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Nodes")  

                        msg_win.refresh()
                        continue

                    msg_win.addstr(1, 2, "Nodes: " + ", ".join(nodes))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 12, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                        
                    new_name = get_input(menu_win, "New Name:", 13, 2)
                    msg = m.rename_node(node_ip, new_name)

                elif op2 == "5":
                    nos = [node.getName() for node in m.get_nodes().values()]
                    msg_win.clear()
                    msg_win.border()

                    if not nos:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Nodes")  

                        msg_win.refresh()
                        continue

                    msg_win.addstr(1, 2, "Nodes: " + ", ".join(nos))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 12, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.info_node(node_ip)

                elif op2 == "6":
                    free_nodes = m.get_free_nodes()
                    msg_win.clear()
                    msg_win.border()

                    if not free_nodes:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Nodes")  

                        msg_win.refresh()
                        continue
                        
                    if not list(m.get_areas().keys()):
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas")  

                        msg_win.refresh()
                        continue

                    msg_win.addstr(1, 2, "Free Nodes: " + " ".join(free_nodes))
                    msg_win.addstr(2, 2, "Areas: " + ", ".join(list(m.get_areas().keys())))
                    msg_win.refresh()

                    node_name = get_input(menu_win, "Node Name:", 12, 2)
                    area_name = get_input(menu_win, "Area Name:", 13, 2)
                    node_ip = m.get_nodeIP_byName(node_name)
                    msg = m.add_node_to_area(node_ip, area_name)

                elif op2 == "7":
                    nodes_in_area = m.get_nodes_in_Area()
                    msg_win.clear()
                    msg_win.border()

                    #if not nodes_in_area:


             

                    

                    add_msg(msg_win, "Nodes in areas: "+ nodes_in_area)

                    msg_win.refresh()
                    node_name = get_input(menu_win, "Node Name:", 12, 2)
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
            # Submenu de areas
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
                    area_name = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    if check_valid_input(area_name):
                        msg = m.add_area(area_name)
                    else:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Area name not valid") 
                        msg_win.refresh()
                        continue


                elif op2 == "2":
                    areas = list(m.get_areas().keys())

                        

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
                    if check_valid_input(area_name):
                        msg = m.remove_area(area_name)
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Area name not valid") 
                    msg_win.refresh()
                    continue


                elif op2 == "3":
                    areas = list(m.get_areas().keys())
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
                    msg = m.info_area(area_name)


                elif op2 == "4":
                    areas = list(m.get_areas().keys())
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
                    area_name = get_input(menu_win, "Area Name:", 12, 2)
                    if check_valid_input(area_name):
                        name_list = get_input(menu_win, "Nodes Names (seperated by spaces):", 13, 2)
                        msg = m.add_nodes_to_area(area_name, name_list)
                    else:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Area name invalid.")  # "No zones exist."
                        msg_win.refresh()
                        continue


                elif op2 == "5":
                    areas = list(m.get_areas().keys())
                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No Areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    area_name = get_input(menu_win, "Name Area:", 12, 2)  # Prompt: "Zone name:"
                    if check_valid_input(area_name):
                        nos_em_area = [n.getName() for n in m.get_areas()[area_name].get_nodes()]
                    else:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Area name invalid.")  # "No zones exist."
                        msg_win.refresh()
                        continue

                    if not nos_em_area:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, f"No nodes in area {area_name}.")  # "No nodes in zone [zone name]."
                        msg_win.refresh()
                        continue

                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Nodes in {area_name}: " + ", ".join(nos_em_area))  # "Nodes in [zone name]: [list of nodes]"
                    msg_win.refresh()
                    names = get_input(menu_win, "Node Names (separated by space):", 13, 2)  # Prompt: "Node IPs (separated by space):"
                    msg = m.remove_nodes_from_area(area_name, names)

                elif op2 == "6":
                    areas = list(m.get_areas().keys())
                    channels = [str(c+1) for c in range(num_channels)]

                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))  # "Zones: [list of zones]"
                    msg_win.addstr(2, 2, "Channels: " + ", ".join(channels))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    area_name = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    channel = get_input(menu_win, "Channel:", 13, 2)  # Prompt: "Channel:"
                    if check_valid_input(area_name) and check_valid_input(channel):
                        msg = m.assign_channel_to_area(area_name, channel)
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Invalid area name or channel")
                    msg_win.refresh()
                    continue

                elif op2 == "7":
                    areas = list(m.get_areas().keys())
                    if not areas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "No areas exist.")  # "No zones exist."
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Areas: " + ", ".join(areas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    area_name = get_input(menu_win, "Area name:", 12, 2)  # Prompt: "Zone name:"
                    msg = m.remove_channel_from_area(area_name)

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
                menu_win.addstr(3, 2, "3 - Assign areas to channel")
                menu_win.addstr(4, 2, "4 - Remove areas from channel")
                menu_win.addstr(5, 2, "0 - Back")
                menu_win.refresh()

                op2 = get_input(menu_win, "Choose an option:", 7, 2)  # Prompt: "Choose an option:"
                if op2 == "1":
                    channels = [str(c+1) for c in range(num_channels)]
                    tipos = ["LOCAL", "TRANSMISSION", "VOICE"]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(channels))  # "Channels: [list of channels]"
                    msg_win.addstr(2, 2, "Types: " + ", ".join(tipos))  # "Types: [list of types]"
                    msg_win.refresh()
                    channel = get_input(menu_win, "Channel:", 9, 2)  # Prompt: "Channel:"
                    tipo = get_input(menu_win, "Transmission type:", 10, 2)  # Prompt: "Transmission type:"
                    try:
                        channel = int(channel)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue

                    msg = m.assign_transmission_to_channel(channel, tipo)

                elif op2 == "2":
                    channels = [str(c+1) for c in range(num_channels)]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(channels))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    channel = get_input(menu_win, "Channel:", 9, 2)  # Prompt: "Channel:"
                    try:
                        channel = int(channel)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue
                    msg = m.info_channel(channel)

                elif op2 == "3":
                    channels = [str(c+1) for c in range(num_channels)]
                    areas = list(m.get_free_areas())
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(channels))  # "Channels: [list of channels]"
                    msg_win.addstr(2, 2, "Areas (separated by space):" + ", ".join(areas))  # "Zones: [list of zones]"
                    msg_win.refresh()
                    channel = get_input(menu_win, "Channel:", 9, 2)  # Prompt: "Channel:"
                    area = get_input(menu_win, "Area:", 10, 2)  # Prompt: "Zone:"
                    try:
                        channel = int(channel)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue
                    msg = m.assign_areas_to_channel(channel, area)

                elif op2 == "4":
                    channels = [str(c+1) for c in range(num_channels)]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Channels: " + ", ".join(channels))  # "Channels: [list of channels]"
                    msg_win.refresh()
                    channel = get_input(menu_win, "Channel:", 9, 2)  # Prompt: "Channel:"
                    try:
                        channel = int(channel)
                    except ValueError:
                        msg = "Invalid channel."  # "Invalid channel."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue

                    areas_em_channel = [area.get_name() for area in list(m.get_channels()[channel].get_areas())]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Areas in {channel}: " + ", ".join(areas_em_channel))  # "Zones in [channel]: [list of zones]"
                    msg_win.refresh()
                    areas = get_input(menu_win, "Areas (separated by space):", 10, 2)  # Prompt: "Zones (separated by space):"
                    msg = m.remove_areas_from_channel(channel, areas)

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
    playlist_dir = "Playlist"  # Pasta com arquivos .mp3
    files = [os.path.join(playlist_dir, f) for f in os.listdir(playlist_dir) if f.lower().endswith(".mp3")]

    if not files:
        if stop_event:
            stop_event.set()
        return

    file_index = 0
    while not stop_event.is_set():
        current_file = files[file_index]
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", current_file,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "1",
            "pipe:1"
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while not stop_event.is_set():
                try:
                    data = process.stdout.read(1024)
                except OSError:
                    break
                if not data:
                    break
                
                while q.qsize() > 300:
                    time.sleep((512/44100) * 290)

                    
                q.put(data)
        except Exception:
            pass
        finally:
            if process.stdout:
                process.stdout.close()
            process.terminate()
            process.wait()
        file_index = (file_index + 1) % len(files)



def get_transmission(q, stop_event=None):
    while not stop_event.is_set():
        time.sleep(2)
    print("get_transmission encerrado.")

def get_voz(q, stop_event=None, inicio=None):
    p = pyaudio.PyAudio()
    print(chr(27) + "[2J")
    inicio.set()
    CHUNK = 512
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    try:
        while not stop_event.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)
            q.put(data)
    except Exception as e:
        print(f"Erro na captura de áudio: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("get_voz encerrado.")



def send_audio(port=8081, stop_event=None, q_local=None, q_transmission=None, q_voz=None):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    count = 0
    while not stop_event.is_set():
        try:


            packet_local = q_local.get()
            packet_trans = b'\x00' * 1024 
            packet_voz   = q_voz.get()


            #print(f"Local: {q_local.qsize()}")


            mensagem = b""

            for canal in m.get_channels().values():

                if canal.get_transmission() == "LOCAL":
                    mensagem += packet_local
                elif canal.get_transmission() == "TRANSMISSION":
                    mensagem += packet_trans
                elif canal.get_transmission() == "VOICE":
                    mensagem += packet_voz
                else:
                    mensagem += b'\x00' * 1024


            sock.sendto(mensagem, ("<broadcast>", port))

            #print("\rPacote enviado: ", count, end="")
            count += 1

        except queue.Empty:
            continue
            
    sock.close()
    print("play_audio encerrado.")








if __name__ == "__main__":
    num_channels = 3
    m = manager.manager()
    for i in range(num_channels):
        m.add_channel()

    stop_event = threading.Event()
    inicio = threading.Event()

    # Cria as queues para cada função de "get"
    q_local = queue.Queue()
    q_transmission = queue.Queue()
    q_voz = queue.Queue()

    # Thread do menu (curses)
    t_menu = threading.Thread(
        target=curses.wrapper, 
        args=(lambda stdscr: main(stdscr, stop_event, inicio),),
        daemon=True
    )
    t_menu.start()

    # Threads para encher as queues a cada 0.5s
    t_local = threading.Thread(target=get_local, args=(q_local, stop_event), daemon=True)
    t_trans = threading.Thread(target=get_transmission, args=(q_transmission, stop_event), daemon=True)
    t_voz   = threading.Thread(target=get_voz, args=(q_voz, stop_event, inicio), daemon=True)
    t_local.start()
    t_trans.start()
    t_voz.start()

    # Thread do play_audio que aguarda as queues e envia pacotes a cada 0.5s
    t_play = threading.Thread(target=send_audio, args=(8081, stop_event, q_local, q_transmission, q_voz), daemon=True)
    t_play.start()

    t_menu.join()
    t_local.join()
    t_trans.join()
    t_voz.join()
    t_play.join()