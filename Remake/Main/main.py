import manager


def main():

    m = manager.manager()

    while True:
        print("1 - Adicionar zona")
        print("2 - Adicionar nó")
        print("3 - Adicionar nó a zona")
        print("4 - Remover nó de zona")
        print("5 - Listar zonas")
        print("6 - Listar nós livres")
        print("7 - Listar nós alocados")
        print("0 - Sair")
        op = input("Escolha uma opção: ")

        if op == "1":
            nome = input("Digite o nome da zona: ")
            if not m.add_zona(nome):
                print("Zona já existe")
            else:
                print("Zona adicionada com sucesso")

        elif op == "2":
            ip = input("Digite o ip do nó: ")
            if not m.add_no(ip):
                print("Nó já existe")
            else:
                print("Nó adicionado com sucesso")

        elif op == "3":
            ip = input("Digite o ip do nó: ")
            nome = input("Digite o nome da zona: ")
            if not m.add_no_zona(ip, nome):
                print("Erro ao adicionar nó a zona")
            else:
                print("Nó adicionado a zona com sucesso")

        elif op == "4":
            ip = input("Digite o ip do nó: ")
            nome = input("Digite o nome da zona: ")
            if not m.remove_no_zona(ip, nome):
                print("Erro ao remover nó de zona")
            else:
                print("Nó removido de zona com sucesso")


        elif op == "5":
            for z in m.get_zonas():
                print(z)

        elif op == "6":
            for n in m.get_nos_livres():
                print(n)

        elif op == "7":
            for n in m.get_nos_alocados():
                print(n)

        elif op == "0":
            break






if __name__ == '__main__':
    main()