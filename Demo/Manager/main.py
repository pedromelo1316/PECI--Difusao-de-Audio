import curses
import os
import threading
import time
import queue
import manager
import socket
from database import manage_db
import json
import sounddevice as sd
import numpy as np
import struct
import subprocess


import base64
def send_info(nodes, removed=False):

    if not removed:
        dic = {}
        for node in nodes:
            node = manage_db.get_node_by_name(node)
            mac = node[2]
            area_id = node[3]
            volume = None
            channel = None
            area = manage_db.get_area_by_id(area_id) if area_id else None
            header = None
            
            volume = area[4] if area is not None else None
            channel = area[2] if area is not None else None
            header = channels_dict[channel]["header"] if channel in channels_dict else None
            header = base64.b64encode(header).decode('utf-8') if header is not None else None
            dic[mac] = {"volume": volume, "channel": channel, "header": header}
    else:
        dic = {}
        for node in nodes:
            node = manage_db.get_node_by_name(node)
            mac = node[2]
            dic[mac] = {"removed": True}

    msg = json.dumps(dic)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto(msg.encode('utf-8'), ('<broadcast>', 8081))



def detect_new_nodes(stop_event, msg_buffer):

    time.sleep(0.1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', 8080))
        msg_buffer.put("Detection started")
        while not stop_event.is_set():
            data, addr = server_socket.recvfrom(1024)
            data = data.decode('utf-8')
            if data:
                name, mac = data.split(',')
                try:
                    name = name.upper()
                    m.add_node(name, mac)
                    msg_buffer.put(f"Node {name} connected")
                    server_socket.sendto(b"OK", addr)

                except Exception as e:
                    if str(e) == "Limit of nodes with the same name reached":
                        msg_buffer.put("Limit of nodes with the same name reached")
                        server_socket.sendto(b"Limit of nodes with the same name reached", addr)
                    elif str(e) == "MAC already in use":
                        node = manage_db.get_node_by_mac(mac)
                        name = node[1]
                        msg_buffer.put(f"Node {name} reconected")
                        server_socket.sendto(b"OK", addr)
                    else:
                        msg_buffer.put(f"Error: {e}")
                        server_socket.sendto(b"Error", addr)

                send_info([name])


        


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
    return inp.upper()



def add_msg(msg_win, menu_win, msg):
    """
    Adds a message to the window 'win' with scrolling.
    The window is assumed to have a border. If the number of messages 
    exceeds the available area, older messages are removed.
    """
    if not hasattr(add_msg, "lines"):
        add_msg.lines = []
        
    height, width = msg_win.getmaxyx()
    max_lines = height - 2  # leaving room for the border

    # Split the message into multiple lines if necessary
    msg_lines = msg.split('\n')
    for line in msg_lines:
        add_msg.lines.append(line)
        if len(add_msg.lines) > max_lines:
            add_msg.lines = add_msg.lines[-max_lines:]
        
    msg_win.clear()
    msg_win.border()
    for idx, line in enumerate(add_msg.lines):
        truncated_line = line[:width - 2]
        msg_win.addstr(idx + 1, 1, truncated_line)
    msg_win.refresh()

    menu_win.refresh()


def message_listener(stop_event, msg_buffer, msg_win, menu_win):
    """
    Continuously listens for messages in msg_buffer and adds them to the window.
    """
    while not stop_event.is_set():
        try:
            # Adjust timeout as needed
            msg = msg_buffer.get(timeout=0.5)
            add_msg(msg_win, menu_win, msg)
        except queue.Empty:
            continue




def main(stdscr, stop_event, msg_buffer):

    try:
        curses.curs_set(1)
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Define área de mensagens (3 linhas) e área para menu (restante)
        msg_height = height // 4
        menu_height = height - msg_height

        # Cria janelas: menu_win para menus e msg_win para exibição de mensagens
        menu_win = curses.newwin(menu_height, width, 0, 0)
        msg_win  = curses.newwin(msg_height, width, menu_height, 0)


        # Start thread to listen to message buffer and update msg_win
        msg_thread = threading.Thread(target=message_listener, args=(stop_event, msg_buffer, msg_win, menu_win), daemon=True)
        msg_thread.start()

        

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

            if op == "0":
                stop_event.set()
                break

            elif op == "1":

                while not stop_event.is_set():

                    nodes = manage_db.get_node_names()
                    nodes = [i[0] for i in nodes] if nodes else []

                    areas = manage_db.get_areas()
                    areas = [i[1] for i in areas] if areas else []


                    if not nodes:
                        msg = "No nodes to manage"
                        add_msg(msg_win, menu_win, msg)
                        break

                    menu_win.clear()
                    menu_win.border()

                    menu_win.addstr(1, 2, "1 - Remove Node")
                    menu_win.addstr(2, 2, "2 - Rename Node")
                    menu_win.addstr(3, 2, "3 - Node Information")
                    menu_win.addstr(4, 2, "0 - Back")

                    menu_win.refresh()

                    op2 = get_input(menu_win, "Choose an option:", 6, 2)

                    if op2 == "0":
                        break

                    elif op2 == "1":

                        msg = "Nodes: " + ", ".join(nodes)
                        add_msg(msg_win, menu_win, msg)

                        node = get_input(menu_win, "Node: ", 8, 2)
                        try:
                            m.remove_node(node)
                            msg = f"Node {node} removed"
                            add_msg(msg_win, menu_win, msg)
                            send_info([node], removed=True)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)

                    elif op2 == "2":

                        msg = "Nodes: " + ", ".join(nodes)
                        add_msg(msg_win, menu_win, msg)

                        node = get_input(menu_win, "Node: ", 8, 2)
                        new_name = get_input(menu_win, "New name: ", 9, 2)

                        try:
                            m.rename_node(node, new_name)
                            msg = f"Node {node} renamed to {new_name}"
                            add_msg(msg_win, menu_win, msg)

                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "3":

                        msg = "Nodes: " + ", ".join(nodes)
                        add_msg(msg_win, menu_win, msg)

                        node = get_input(menu_win, "Node: ", 8, 2)

                        try:
                            info = m.get_node_info(node)
                            msg = f"Node {node} information: {info}"
                            add_msg(msg_win, menu_win, msg)

                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    


            elif op == "2":
                while True:

                    areas = manage_db.get_areas()
                    areas = [i[1] for i in areas] if areas else []

                    nodes = manage_db.get_node_names()
                    nodes = [i[0] for i in nodes] if nodes else []

                    channels = manage_db.get_channel_names()
                    channels = [i[0] for i in channels] if channels else []

                    menu_win.clear()
                    menu_win.border()
                    menu_win.addstr(1, 2, "1 - Add Area")
                    menu_win.addstr(2, 2, "2 - Remove Area")
                    menu_win.addstr(3, 2, "3 - Area information")
                    menu_win.addstr(4, 2, "4 - Add nodes to Area")
                    menu_win.addstr(5, 2, "5 - Remove nodes from Area")
                    menu_win.addstr(6, 2, "6 - Assign channel to Area")
                    menu_win.addstr(7, 2, "7 - Remove channel from Area")
                    menu_win.addstr(8, 2, "8 - Set volume")
                    menu_win.addstr(9, 2, "0 - Back")
                    menu_win.refresh()

                    op2 = get_input(menu_win, "Choose an option:", 11, 2)  # Prompt: "Choose an option:"


                    if op2 == "0":
                        break

                    elif op2 == "1":
                        area = get_input(menu_win, "Area name: ", 13, 2)
                        try:
                            m.add_area(area)
                            msg = f"Area {area} added"
                            add_msg(msg_win, menu_win, msg)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "2":

                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)
                        try:
                            nodes_in_area = manage_db.get_nodes_by_area(area)
                            m.remove_area(area)
                            msg = f"Area {area} removed"
                            add_msg(msg_win, menu_win, msg)
                            send_info(nodes_in_area)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "3":

                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)
                        try:
                            info = m.get_area_info(area)
                            msg = f"Area {area} information: {info}"
                            add_msg(msg_win, menu_win, msg)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "4":

                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        out_nodes = manage_db.get_nodes_not_in_areas()
                        out_nodes = [i[0] for i in out_nodes] if out_nodes else []

                        if not out_nodes:
                            msg = "All nodes are already in areas"
                            add_msg(msg_win, menu_win, msg)
                            continue

                        area = get_input(menu_win, "Area: ", 13, 2)


                        msg = "Nodes: " + ", ".join(out_nodes)
                        add_msg(msg_win, menu_win, msg)

                        nodes = get_input(menu_win, "Node(separado por espaço): ", 14, 2)

                        try:
                            nodes = nodes.split()
                            for n in nodes:
                                if n not in out_nodes:
                                    raise Exception(f"Node {n} not available")
                            m.add_node_to_area(nodes, area)
                            msg = f"Nodes " + ",".join(nodes) +  f" added to area {area}"
                            add_msg(msg_win, menu_win, msg)
                            send_info(nodes)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "5":

                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)


                        inside_nodes = manage_db.get_nodes_by_area(area)

                        if not inside_nodes:
                            msg = "No nodes in area"
                            add_msg(msg_win, menu_win, msg)
                            continue

                        msg = "Nodes: " + ", ".join(inside_nodes)
                        add_msg(msg_win, menu_win, msg)

                        nodes = get_input(menu_win, "Node(separado por espaço): ", 14, 2)

                        try:
                            nodes = nodes.split()
                            for n in nodes:
                                if n not in inside_nodes:
                                    raise Exception(f"Node {n} not available")
                            m.remove_node_from_area(nodes, area)
                            msg = f"Node {nodes} removed from area {area}"
                            add_msg(msg_win, menu_win, msg)
                            send_info(nodes)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)

                    elif op2 == "6":
                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)

                        channel = manage_db.get_area_channel(area)[0] if manage_db.get_area_channel(area) else None

                        other_channels = [i for i in channels if i != channel]

                        msg = "Channels: " + ", ".join(map(str, other_channels))
                        add_msg(msg_win, menu_win, msg)

                        channel = get_input(menu_win, "Channel: ", 14, 2)

                        try:
                            if int(channel) not in other_channels:
                                raise Exception(f"Channel {channel} not available")

                            m.add_channel_to_area(area, channel)
                            msg = f"Channel {channel} added to area {area}"
                            add_msg(msg_win, menu_win, msg)
                            send_info(manage_db.get_nodes_by_area(area))
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "7":
                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)

                        try:
                            m.remove_area_channel(area)
                            msg = f"Channel removed from area {area}"
                            add_msg(msg_win, menu_win, msg)
                            send_info(manage_db.get_nodes_by_area(area))
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    elif op2 == "8":
                        msg = "Areas: " + ", ".join(areas)
                        add_msg(msg_win, menu_win, msg)

                        area = get_input(menu_win, "Area: ", 13, 2)

                        volume = get_input(menu_win, "Volume(0.1 a 2.0): ", 14, 2)

                        try:
                            m.set_area_volume(area, volume)
                            msg = f"Volume set to {volume} in area {area}"
                            add_msg(msg_win, menu_win, msg)
                            send_info(manage_db.get_nodes_by_area(area))
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)


                    


            elif op == "3":
                # Submenu for channels
                while True:

                    channels = manage_db.get_channel_names()
                    channels = [i[0] for i in channels] if channels else []

                    opc = ["LOCAL", "TRANSMISSION", "VOICE"]

                    menu_win.clear()
                    menu_win.border()
                    menu_win.addstr(1, 2, "1 - Change channel transmission")
                    menu_win.addstr(2, 2, "2 - Channel information")
                    menu_win.addstr(3, 2, "0 - Back")
                    menu_win.refresh()

                    op2 = get_input(menu_win, "Choose an option:", 5, 2)  # Prompt: "Choose an option:"


                    if op2 == "0":
                        break

                    elif op2 == "1":

                        msg = "Channels: " + ", ".join(map(str, channels))
                        add_msg(msg_win, menu_win, msg)

                        channel = get_input(menu_win, "Channel: ", 7, 2)

                        transmission = manage_db.get_channel_type(channel)

                        _options = [i for i in opc if i != transmission]

                        msg = "Options: " + ", ".join(_options)
                        add_msg(msg_win, menu_win, msg)

                        transmission = get_input(menu_win, "Transmission: ", 8, 2)

                        try:
                            if transmission not in opc:
                                raise Exception(f"Transmission {transmission} not available")
                            m.change_channel_transmission(channel, transmission)
                            msg = f"Transmission set to {transmission} in channel {channel}"
                            add_msg(msg_win, menu_win, msg)
                            change_channel_process_thread = threading.Thread(target=change_channel_process, args=(int(channel), manage_db.get_channel_source(channel), transmission), daemon=True)
                            change_channel_process_thread.start()


                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)



                    elif op2 == "2":

                        msg = "Channels: " + ", ".join(map(str, channels))
                        add_msg(msg_win, menu_win, msg)

                        channel = get_input(menu_win, "Channel: ", 7, 2)

                        try:
                            info = m.get_channel_info(channel)
                            msg = f"Channel {channel} information: {info}"
                            add_msg(msg_win, menu_win, msg)
                        except Exception as e:
                            msg = f"Error: {e}"
                            add_msg(msg_win, menu_win, msg)

                    



            elif op == "CLEAR":
                msg_win.clear()
                msg_win.border()
                msg_win.refresh()



    except Exception as e:
        curses.endwin()  # Restaura o terminal
        raise e
                        

# fiz alterações a partir de aqui

BITRATE = "256k"  # max 256k
SAMPLE_RATE = "48000"
CHUNCK_SIZE = 960
HEADER_SIZE = 300
AUDIO_CHANNELS = "1"         # Mono
MULTIPLICADOR = 65   # Ajuste conforme necessário max 65


LOCAL = 0
VOICE = 1
TRANSMISSION = 2
                

# Configura o stdout dos processos FFmpeg para ser não bufferizado
def start_ffmpeg_process(source, _type):
    if _type == "VOICE":
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-f", "alsa", "-i", source,
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            "-f", "opus",
            "pipe:1"
        ]
    elif _type == "LOCAL":
        playlist_path = f"Playlists/{source}.txt"
        if not os.path.exists(playlist_path):
            print(f"Playlist {playlist_path} not found")
            return None

        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
            "-f", "concat",          # Adicione esta linha
            "-safe", "0",            # Permite caminhos absolutos/relativos
            "-re",                   # Opcional (simula velocidade real)
            "-i", f"Playlists/{source}.txt",
            "-af", "apad",  # Preenche com silêncio entre as músicas
            "-vn",
            "-acodec", "libopus",
            "-b:a", BITRATE,
            "-ar", SAMPLE_RATE,
            "-ac", AUDIO_CHANNELS,
            "-packet_size", str(CHUNCK_SIZE), # Tamanho do pacote (ajuste conforme a rede)
            "-f", "opus",
            "pipe:1"
        ]
    elif _type == "TRANSMISSION":
        return None
    else:
        return None
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=int(CHUNCK_SIZE*2))
    return process



def send_audio(port=8082, stop_event=None):
    global start_time
    MCAST_GRP = "224.1.1.1"
    MCAST_PORT = port

    count = 0
    seq = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = 2
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        while not stop_event.is_set():
            for channel in list(channels_dict.keys()):
                if channels_dict[channel] is None:
                    continue
                process = channels_dict[channel]["process"]
                if process:
                    opus_data = process.stdout.read(CHUNCK_SIZE*MULTIPLICADOR)  # Ajuste o tamanho conforme necessário
                    if not opus_data:
                        break
                    
                    dados = struct.pack('!I', channel) + struct.pack('!B', seq) + opus_data
                    sock.sendto(dados, (MCAST_GRP, MCAST_PORT))

                    #print(f"\rEnviado: {seq}, velocidade: {(count*CHUNCK_SIZE*MULTIPLICADOR)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")
                    count += 1
                
            seq = (seq + 1) % 256
            print(f"\rEnviado: {seq}, velocidade: {(count*CHUNCK_SIZE*MULTIPLICADOR)*8/(time.time()-start_time)/1000000:.2f}Mbits/s", end="")

    except KeyboardInterrupt:
        print("Transmissão interrompida.")
    finally:
        sock.close()
        for channel in list(channels_dict.keys()):
            if channels_dict[channel]:
                process = channels_dict[channel]["process"]
                process.terminate()
                process.wait()
        print("Processes terminated")
        stop_event.set()


def change_channel_process(channel, source, transmission_type):
    global channels_dict
    if channel in channels_dict:
        process = channels_dict[channel]["process"]
        process.kill()
        channels_dict[channel] = {"process": None, "header": None}
        process = start_ffmpeg_process(source, transmission_type)
        if process:
            header = process.stdout.read(HEADER_SIZE)
            channels_dict[channel] = {"process": process, "header": header}
            send_info(manage_db.get_nodes_by_channel(channel))
        else:
            channels_dict[channel] = None
    else:
        process = start_ffmpeg_process(source, transmission_type)
        if process:
            header = process.stdout.read(HEADER_SIZE)
            channels_dict[channel] = {"process": process, "header": header}
            send_info(manage_db.get_nodes_by_channel(channel))
        else:
            channels_dict[channel] = None



def init_processes():
    global channels_dict, start_time

    for channel in channels_dict:
        transmission_type = manage_db.get_channel_type(channel)
        source = manage_db.get_channel_source(channel)
        process = start_ffmpeg_process(source, transmission_type)
        if process:
            channels_dict[channel] = {"process": process, "header": None}
            #print(f"Channel {channel} started")
        else:
            channels_dict[channel] = None



    start_time = time.time()
    for channel in channels_dict:
        if channels_dict[channel]:
            process = channels_dict[channel]["process"]
            header = process.stdout.read(HEADER_SIZE)
            channels_dict[channel]["header"] = header
            send_info(manage_db.get_nodes_by_channel(channel))
            #print(f"Channel {channel} header received")


    
    #print(channels_dict)


if __name__ == "__main__":
    global channels_dict

    channels_dict = {}

    msg_buffer = queue.Queue()

    num_channels = 3

    m = manager.manager()

    manage_db.init_channels(num_channels)

    channels = manage_db.get_channel_names()
    channels = [i[0] for i in channels] if channels else []

    for channel in channels:
        channels_dict[channel] = None

    init_processes_thread = threading.Thread(target=init_processes, daemon=True)
    init_processes_thread.start()


    stop_event = threading.Event()

    # Thread do menu (curses)
    '''t_menu = threading.Thread(
        target=curses.wrapper, 
        args=(lambda stdscr: main(stdscr, stop_event, msg_buffer),),
        daemon=True
    )



    t_menu.start()'''


    detect = threading.Thread(target=detect_new_nodes, args=(stop_event,msg_buffer), daemon=True)
    detect.start()
 

    init_processes_thread.join()

    # Thread do play_audio que aguarda as queues e envia pacotes a cada 0.5s
    t_play = threading.Thread(target=send_audio, args=(8082, stop_event), daemon=True)
    t_play.start()

    #t_menu.join()
    t_play.join()