import manager


def main():

    num_canais = 3

    m = manager.manager()

    for i in range(num_canais):
        m.add_canal()    

    while True:
        print("1 - Adicionar nó")
        print("2 - Adicionar zona")
        print("3 - Remover nó")
        print("4 - Remover zona")
        print("5 - Adicionar nó à zona")
        print("6 - Atribuir canal à zona")
        print("0 - Sair")
        op = input("Escolha uma opção: ")

        if op == "1":
            m.add_no(input("IP do nó: "))

        elif op == "2":
            m.add_zona(input("Nome da zona: "))

        elif op == "3":
            m.remove_no(input("IP do nó: "))

        elif op == "4":
            m.remove_zona(input("Nome da zona: "))

        elif op == "5":
            m.add_no_to_zona(input("IP do nó: "), input("Nome da zona: "))

        elif op == "6":
            pass

        
        elif op == "0":
            break






if __name__ == '__main__':
    main()