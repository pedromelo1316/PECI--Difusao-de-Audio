import manager


def main():

    num_canais = 3

    m = manager.manager()

    for i in range(num_canais):
        m.add_canal()    

    while True:
        print("1 - Adicionar nó")
        print("2 - Adicionar zona")
        print("3 - Adicionar nó a zona")
        print("4 - Remover nó de zona")
        print("20 - Listar nós")
        print("21 - Listar zonas")
        print("22 - Listar canais")
        print("0 - Sair")
        op = input("Escolha uma opção: ")

        if op == "2":
            nome = input("Digite o nome da zona: ")
            if not m.add_zona(nome):
                print("Zona já existe")
            else:
                print("Zona adicionada com sucesso")

        elif op == "1":
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


        elif op == "20":
            for z in m.get_zonas():
                print(z)

        elif op == "21":
            for n in m.get_nos():
                print(n)

        elif op == "22":
            for c in m.get_canais():
                print(c)


        

        elif op == "0":
            break






if __name__ == '__main__':
    main()