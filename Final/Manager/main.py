import curses
import threading
import time
import queue
import manager



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
        menu_win.addstr(2, 2, "2 - Manage areas")
        menu_win.addstr(3, 2, "3 - Manage channels")
        menu_win.addstr(4, 2, "0 - Exit")
        menu_win.refresh()

        op = get_input(menu_win, "Choose an option: ",6,2)





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
        args=(lambda stdscr: main(stdscr, stop_event),),
        daemon=True
    )
    t_menu.start()

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