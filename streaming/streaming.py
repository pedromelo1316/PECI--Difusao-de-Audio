    import subprocess
import os

# URL da música no YouTube
url = 'https://www.youtube.com/watch?v=mix9YfaaNa0&ab_channel=twentyonepilots'  # Substitua pela URL desejada

# Cria um arquivo temporário para armazenar o áudio
temp_audio_file = 'temp_audio.mp3'
binary_data_file = 'audio_data.txt'  # Nome do arquivo para armazenar dados binários

# Comando para baixar o áudio usando yt-dlp
command = [
    'yt-dlp',
    '-f', 'bestaudio',  # Melhor qualidade de áudio
    '-o', temp_audio_file,  # Saída para o arquivo temporário
    url
]

# Executa o comando de download
with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
    # Lê os dados de erro
    _, error_data = proc.communicate()  

# Verifica se ocorreu algum erro durante o download
if proc.returncode != 0:
    print("Erro ao baixar o áudio:", error_data.decode())
else:
    # O áudio foi salvo no arquivo temporário
    print("Download concluído, arquivo salvo em:", temp_audio_file)

    # Lê os dados binários do arquivo de áudio
    with open(temp_audio_file, 'rb') as f:
        audio_data = f.read()

    # Exibe os primeiros 100 bytes do áudio como exemplo
    print('-----------------------------------------------------')
    print("Dados binários da música (primeiros 100 bytes):", audio_data[:100])
    print('-----------------------------------------------------')


    print("Dados binários da música toda: \n ",audio_data)
    print('-----------------------------------------------------')


    # Salva os dados binários em um arquivo .txt
    with open(binary_data_file, 'wb') as binary_file:
        binary_file.write(audio_data)

    print(f"Dados binários salvos em: {binary_data_file}")

    # Comando para reproduzir o áudio usando ffplay
    ffplay_command = ['ffplay', '-nodisp', '-autoexit', temp_audio_file]  # Reproduz o arquivo temporário

    # Reproduz o áudio
    subprocess.run(ffplay_command)

    # Remove o arquivo temporário após a reprodução
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)
