import socket
import os
from pydub import AudioSegment
from io import BytesIO

def convert_and_play_audio(audio_data):
    try:
        # Tenta processar os dados binários como um arquivo MP3
        audio_segment = AudioSegment.from_file(BytesIO(audio_data), format='webm')

        # Define o nome do arquivo de saída
        output_file = 'output_audio.wav'

        # Salva o áudio como WAV
        audio_segment.export(output_file, format='wav')
        print(f"Áudio produzido e salvo como: {output_file}")

        # Reproduz o áudio
        os.system(f"ffplay -nodisp -autoexit {output_file}")

    except Exception as e:
        print(f"Erro ao processar os dados binários: {e}")

def save_audio_data_to_file(audio_data, file_path):
    """Salva os dados de áudio binário em um arquivo de texto."""
    try:
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        print(f"Dados de áudio salvos em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar dados de áudio: {e}")

def udp_client(server_host="192.168.109.81", server_port=8080):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Aumentar o tamanho do buffer de recepção
    buffer_size = 65536  # Ajuste conforme necessário
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)

    # Enviar mensagem inicial ao servidor
    message = b'Hello, servidor!'
    client_socket.sendto(message, (server_host, server_port))
    print(f'Cliente conectado ao servidor em {server_host}:{server_port}')

    # Receber o áudio do servidor em pacotes
    audio_data = bytearray()  # Usar bytearray para acumular os dados
    packet_count = 0  # Contador de pacotes

    while True:
        data, addr = client_socket.recvfrom(1024)  # Receber pacotes de 4096 bytes
        if not data:
            break

        audio_data.extend(data)  # Acumular dados recebidos
        packet_count += 1

        # Print informações do pacote recebido
        print(f'Pacote {packet_count} recebido: {len(data)} bytes, primeiros bytes: {data[:10]}')

        # (Opcional) Sinal para finalizar a recepção, se necessário
        if len(data) < 1024:  # Assumir que o último pacote pode ser menor
            break

    print(f'Áudio completo recebido com {packet_count} pacotes.')

    # Salvar dados de áudio em um arquivo de texto
    save_audio_data_to_file(audio_data, 'binario.txt')

    # Converter os dados binários acumulados em áudio e reproduzir
    if audio_data:  # Verifique se há dados antes de tentar reproduzir
        convert_and_play_audio(audio_data)
    else:
        print("Nenhum dado de áudio recebido.")

if __name__ == '__main__':
    udp_client()
