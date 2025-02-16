import curses
import time
import manager
import socket

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


def main(stdscr):
    # Inicializa o manager e canais
    num_canais = 3
    m = manager.manager()
    for i in range(num_canais):
        # agora add_canal retorna uma mensagem
        msg = m.add_canal()
        # opicional: pode logar msg se necessário

    curses.curs_set(1)
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Define área de mensagens (3 linhas) e área para menu (restante)
    msg_height = height // 4
    menu_height = height - msg_height

    # Cria janelas: menu_win para menus e msg_win para exibição de mensagens
    menu_win = curses.newwin(menu_height, width, 0, 0)
    msg_win  = curses.newwin(msg_height, width, menu_height, 0)

    while True:
        # Menu principal
        menu_win.clear()
        menu_win.border()
        menu_win.addstr(1, 2, "1 - Gerir nós")
        menu_win.addstr(2, 2, "2 - Gerir zonas")
        menu_win.addstr(3, 2, "3 - Gerir canais")
        menu_win.addstr(4, 2, "0 - Sair")
        menu_win.refresh()

        op = get_input(menu_win, "Escolha uma opção:", 6, 2)

        if op == "1":
            # Submenu de nós
            while True:
                menu_win.clear()
                menu_win.border()
                menu_win.addstr(1, 2, "1 - Detetar nós")
                menu_win.addstr(2, 2, "2 - Adicionar nó")
                menu_win.addstr(3, 2, "3 - Remover nó")
                menu_win.addstr(4, 2, "4 - Informações do nó")
                menu_win.addstr(5, 2, "5 - Adicionar nó a zona")
                menu_win.addstr(6, 2, "6 - Remover nó de zona")
                menu_win.addstr(7, 2, "0 - Voltar")
                menu_win.refresh()

                op2 = get_input(menu_win, "Escolha uma opção:", 9, 2)


                if op2 == "1":
                    msg_win.clear()
                    msg_win.border()
                    detected = set()
                    detection_port = 9090

                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(3)  # Timeout para não esperar indefinidamente
                    message = b"Detetar"
                    sock.sendto(message, ("<broadcast>", detection_port))

                    # Loop de deteção com interface reduzida
                    while True:
                        menu_win.clear()
                        menu_win.border()
                        menu_win.addstr(1, 2, "Detetando nós... (Pressione 0 para parar)")
                        menu_win.refresh()

                        try:
                            data, addr = sock.recvfrom(1024)  # Espera pela resposta
                            if data.decode('utf-8').strip() == "hello":
                                detected.add(addr[0])
                                msg = f"Nó {addr[0]} detetado."
                                add_msg(msg_win, msg)
                                msg_win.refresh()

                                m.add_no(addr[0])

                        except socket.timeout:
                            pass


                        # Verifica se o usuário pressionou "0" para parar
                        ch = menu_win.getch()
                        if ch == ord('0'):
                            break

                    sock.close()
                    msg = "Deteção encerrada. Nós: " + ", ".join(detected)
                    msg_win.clear()
                    msg_win.border()
                    add_msg(msg_win, msg)
                    msg_win.refresh()

                if op2 == "2":
                    ip = get_input(menu_win, "IP do nó:", 10, 2)
                    msg = m.add_no(ip)
                    
                elif op2 == "3":
                    nos = list(m.get_nos().keys())
                    if not nos:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem nós.")  
                        msg_win.refresh()
                        continue
                    
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Nós: " + ", ".join(nos))
                    msg_win.refresh()
            
                    ip = get_input(menu_win, "IP do nó:", 10, 2)
                    msg = m.remove_no(ip)

                elif op2 == "4":
                    nos = list(m.get_nos().keys())
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Nós: " + ", ".join(nos))
                    msg_win.refresh()
                    ip = get_input(menu_win, "IP do nó:", 10, 2)
                    msg = m.info_no(ip)

                elif op2 == "5":
                    nos_livres = m.get_nos_livres()
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Nós livres: " + " ".join(nos_livres))
                    msg_win.addstr(2, 2, "Zonas: " + ", ".join(list(m.get_zonas().keys())))
                    msg_win.refresh()
                    ip = get_input(menu_win, "IP do nó:", 10, 2)
                    zona_nome = get_input(menu_win, "Nome da zona:", 11, 2)
                    msg = m.add_no_to_zona(ip, zona_nome)

                elif op2 == "6":
                    nos_em_zona = m.get_nos_em_zonas()
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Nós em zonas: \n" + nos_em_zona)
                    msg_win.refresh()
                    ip = get_input(menu_win, "IP do nó:", 10, 2)
                    msg = m.remove_no_from_zona(ip)

                elif op2 == "0":
                    break
                else:
                    msg = "Opção inválida."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()
        

        elif op == "2":
            # Submenu de zonas
            while True:
                menu_win.clear()
                menu_win.border()
                menu_win.addstr(1, 2, "1 - Adicionar zona")
                menu_win.addstr(2, 2, "2 - Remover zona")
                menu_win.addstr(3, 2, "3 - Informações de zona")
                menu_win.addstr(4, 2, "4 - Adicionar nós a zona")
                menu_win.addstr(5, 2, "5 - Remover nós de zona")
                menu_win.addstr(6, 2, "6 - Atribuir canal a zona")
                menu_win.addstr(7, 2, "7 - Remover canal de zona")
                menu_win.addstr(8, 2, "0 - Voltar")
                menu_win.refresh()

                op2 = get_input(menu_win, "Escolha uma opção:", 10, 2)
                if op2 == "1":
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    msg = m.add_zona(zona_nome)

                elif op2 == "2":
                    zonas = list(m.get_zonas().keys())

                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue

                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.refresh()
            
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    msg = m.remove_zona(zona_nome)
                elif op2 == "3":
                    zonas = list(m.get_zonas().keys())
                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    msg = m.info_zona(zona_nome)

                elif op2 == "4":
                    zonas = list(m.get_zonas().keys())
                    nos_livres = m.get_nos_livres()

                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue
                    if not nos_livres:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem nós livres.")  
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.addstr(2, 2, "Nós livres: " + " ".join(nos_livres))
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    ip_list = get_input(menu_win, "IP dos nós (separados por espaço):", 11, 2)
                    msg = m.add_nos_to_zona(zona_nome, ip_list)

                elif op2 == "5":
                    zonas = list(m.get_zonas().keys())
                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    nos_em_zona = [n.get_ip() for n in m.get_zonas()[zona_nome].get_nos()]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Nós em {zona_nome}: " + ", ".join(nos_em_zona))
                    msg_win.refresh()
                    ips = get_input(menu_win, "IP dos nós (separados por espaço):", 11, 2)
                    msg = m.remove_nos_from_zona(zona_nome, ips)


                elif op2 == "6":
                    zonas = list(m.get_zonas().keys())
                    canais = [str(c+1) for c in range(num_canais)]

                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.addstr(2, 2, "Canais: " + ", ".join(canais))
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    canal = get_input(menu_win, "Canal:", 11, 2)
                    msg = m.assign_canal_to_zona(zona_nome, canal)

                elif op2 == "7":
                    zonas = list(m.get_zonas().keys())
                    if not zonas:
                        msg_win.clear()
                        msg_win.border()
                        msg_win.addstr(1, 2, "Não existem zonas.")  
                        msg_win.refresh()
                        continue
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.refresh()
                    zona_nome = get_input(menu_win, "Nome da zona:", 10, 2)
                    msg = m.remove_canal_from_zona(zona_nome)

                elif op2 == "0":
                    break
                else:
                    msg = "Opção inválida."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()
        

        elif op == "3":
            # Submenu de canais
            while True:
                menu_win.clear()
                menu_win.border()
                menu_win.addstr(1, 2, "1 - Alterar transmissão do canal")
                menu_win.addstr(2, 2, "2 - Informações do canal")
                menu_win.addstr(3, 2, "3 - Atribuir zonas ao canal")
                menu_win.addstr(4, 2, "4 - Remover zonas do canal")
                menu_win.addstr(5, 2, "0 - Voltar")
                menu_win.refresh()

                op2 = get_input(menu_win, "Escolha uma opção:", 7 , 2)
                if op2 == "1":
                    canais = [str(c+1) for c in range(num_canais)]
                    tipos = ["LOCAL", "TRNASMISSAO", "VOZ"]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, "Canais: " + ", ".join(canais))
                    msg_win.addstr(2, 2, "Tipos: " + ", ".join(tipos))
                    msg_win.refresh()
                    canal = get_input(menu_win, "Canal:", 9, 2)
                    tipo = get_input(menu_win, "Tipo de transmissão:", 10, 2)
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Canal inválido."
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
                    msg_win.addstr(1, 2, "Canais: " + ", ".join(canais))
                    msg_win.refresh()
                    canal = get_input(menu_win, "Canal:", 7, 2)
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Canal inválido."
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
                    msg_win.addstr(1, 2, "Canais: " + ", ".join(canais))
                    msg_win.addstr(2, 2, "Zonas: " + ", ".join(zonas))
                    msg_win.refresh()
                    canal = get_input(menu_win, "Canal:", 7, 2)
                    zona = get_input(menu_win, "Zona:", 8, 2)
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Canal inválido."
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
                    msg_win.addstr(1, 2, "Canais: " + ", ".join(canais))
                    msg_win.refresh()
                    canal = get_input(menu_win, "Canal:", 7, 2)
                    try:
                        canal = int(canal)
                    except ValueError:
                        msg = "Canal inválido."
                        msg_win.clear()
                        msg_win.border()
                        add_msg(msg_win, msg)
                        msg_win.refresh()
                        continue

                    zonas_em_canal = [zona.get_nome() for zona in list(m.get_canais()[canal].get_zonas())]
                    msg_win.clear()
                    msg_win.border()
                    msg_win.addstr(1, 2, f"Zonas em {canal}: " + ", ".join(zonas_em_canal))
                    msg_win.refresh()
                    zonas = get_input(menu_win, "Zonas (separadas por espaço):", 8, 2)
                    msg = m.remove_zonas_from_canal(canal, zonas)

                elif op2 == "0":
                    break
                else:
                    msg = "Opção inválida."

                msg_win.clear()
                msg_win.border()
                add_msg(msg_win, msg)
                msg_win.refresh()
        
        elif op == "0":
            break
        else:
            msg = "Opção inválida."
            msg_win.clear()
            msg_win.border()
            add_msg(msg_win, msg)
            msg_win.refresh()
    

if __name__ == "__main__":
    curses.wrapper(main)