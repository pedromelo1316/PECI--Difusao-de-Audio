import manager


def main():

    num_canais = 3

    m = manager.manager()

    for i in range(num_canais):
        m.add_canal()    

    while True:
        print("1 - Adicionar nó")
        print("2 - Adicionar zona")
        print("3 - Adicionar transmissão a canal")
        print("4 - Adicionar nó à zona")
        print("5 - Atribuir canal à zona")
        print("6 - Informações")
        print("7 - Remover nó")
        print("8 - Remover zona")
        print("0 - Sair")
        op = input("Escolha uma opção: ")

        if op == "1":
            m.add_no(input("IP do nó: "))

        elif op == "2":
            m.add_zona(input("Nome da zona: "))

        elif op == "3":
            tipos = ["LOCAL", "TRANSMISSAO", "VOZ"]
            m.assign_transmissao_to_canal(int(input("ID do canal: ")), input(f"{tipos}\nTransmissão: "))
            

        elif op == "4":
            m.add_no_to_zona(input("IP do nó: "), input("Nome da zona: "))

        elif op == "5":
            m.assign_canal_to_zona(int(input("ID do canal: ")), input("Nome da zona: "))

        elif op == "6":
            print("1 - Informações de canal")
            print("2 - Informações de zona")
            print("3 - Informações de nó")
            op2 = input("Escolha uma opção: ")

            if op2 == "1":
                m.info_canal(int(input("ID do canal: ")))

            elif op2 == "2":
                m.info_zona(input("Nome da zona: "))

            elif op2 == "3":
                m.info_no(input("IP do nó: "))


        elif op == "7":
            m.remove_no(input("IP do nó: "))

        elif op == "8":
            m.remove_zona(input("Nome da zona: "))


        
        elif op == "0":
            break






if __name__ == '__main__':
    main()