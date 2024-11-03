import socket
import subprocess
import os
import time

def udp_server(host="192.168.109.109", port=8080, url='https://www.youtube.com/watch?v=Wjg6IUL2Pq4'):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f'Servidor UDP ativo em {host}:{port}')

    clients = set()

    def download_and_convert_audio():
        """
        Função para baixar e converter o áudio em binário.
        """
        temp_audio_file = 'temp_audio.mp3'
        binary_data_file = 'audio_data.txt'

        # Comando para baixar o áudio
        command = [
            'yt-dlp',
            '-f', 'bestaudio',
            '-o', temp_audio_file,
            url
        ]

        # Baixar o áudio
        print("Baixando o áudio...")
        subprocess.run(command, check=True)

        # Ler os dados binários do arquivo de áudio
        with open(temp_audio_file, 'rb') as f:
            audio_data = f.read()

        # Remover o ficheiro temporário
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)

        return audio_data

    while True:
        # Receber dados de qualquer cliente
        data, addr = server_socket.recvfrom(1024)
        
        if addr not in clients:
            clients.add(addr)
            print(f'Novo cliente conectado: {addr}')
            #server_socket.sendto(b'A tocar RFM...\n', addr)

            # Fazer download e converter o áudio
            audio_data = download_and_convert_audio()

            # Enviar o áudio em pacotes para o cliente
            packet_size = 1024
            total_packets = len(audio_data) // packet_size + (1 if len(audio_data) % packet_size else 0)
            print(f'Enviando {total_packets} pacotes de áudio para {addr}.')

            for i in range(total_packets):
                start = i * packet_size
                end = start + packet_size
                packet = audio_data[start:end]
                server_socket.sendto(packet, addr)
                time.sleep(0.005)  # Pequeno intervalo entre pacotes

            print(f'Envio de áudio concluído para {addr}')

if __name__ == '__main__':
    udp_server()