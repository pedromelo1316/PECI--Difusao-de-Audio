import curses
import threading
import time
import queue
import manager
import socket
from database import manage_db





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



def add_msg(msg_win, menu_win,  msg):
    """
    Adds a message to the window 'win' with scrolling.
    The window is assumed to have a border. If the number of messages 
    exceeds the available area, older messages are removed.
    """
    if not hasattr(add_msg, "lines"):
        add_msg.lines = []
        
    height, width = msg_win.getmaxyx()
    max_lines = height - 2  # leaving room for the border

    add_msg.lines.append(msg)
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

                menu_win.clear()
                menu_win.border()

                menu_win.addstr(1, 2, "1 - Remove Node")
                menu_win.addstr(2, 2, "2 - Rename Node")
                menu_win.addstr(3, 2, "3 - Node Information")
                menu_win.addstr(4, 2, "4 - Add Node to Area")
                menu_win.addstr(5, 2, "5 - Remove Node from Area")
                menu_win.addstr(6, 2, "0 - Back")

                menu_win.refresh()

                op2 = get_input(menu_win, "Choose an option:", 10, 2)

                if op2 == "0":
                    break
                



def get_local(q, stop_event=None):
    while not stop_event.is_set():
        time.sleep(1)


def get_transmission(q, stop_event=None):
    while not stop_event.is_set():
        time.sleep(1)

def get_voz(q, stop_event=None):
    while not stop_event.is_set():
        time.sleep(1)



def send_audio(port=8081, stop_event=None, q_local=None, q_transmission=None, q_voz=None):
    while not stop_event.is_set():
        time.sleep(1)



if __name__ == "__main__":


    msg_buffer = queue.Queue()

    num_channels = 3
    m = manager.manager()
    for i in range(num_channels):
        m.add_channel()

    stop_event = threading.Event()

    # Cria as queues para cada função de "get"
    q_local = queue.Queue()
    q_transmission = queue.Queue()
    q_voz = queue.Queue()

    # Thread do menu (curses)
    t_menu = threading.Thread(
        target=curses.wrapper, 
        args=(lambda stdscr: main(stdscr, stop_event, msg_buffer),),
        daemon=True
    )



    t_menu.start()


    detect = threading.Thread(target=detect_new_nodes, args=(stop_event,msg_buffer), daemon=True)
    detect.start()

    # Threads para encher as queues a cada 0.5s
    t_local = threading.Thread(target=get_local, args=(q_local, stop_event), daemon=True)
    t_trans = threading.Thread(target=get_transmission, args=(q_transmission, stop_event), daemon=True)
    t_voz   = threading.Thread(target=get_voz, args=(q_voz, stop_event), daemon=True)
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