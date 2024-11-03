import os
from pydub import AudioSegment
from io import BytesIO

# Função para verificar e processar dados binários de um arquivo
def check_binary_data(file_path):
    try:
        with open(file_path, 'rb') as f:
            audio_data = f.read()

        # Exibe os primeiros 16 bytes para depuração
        print('------------------')
        print("Primeiros bytes do arquivo:")
        print(audio_data[:16])
        print('------------------')


        # Tenta processar os dados binários como um arquivo WebM
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

# Caminho para o arquivo de dados binários
binary_data_file = 'audio_data.txt'

# Verifica e processa o arquivo de dados binários
check_binary_data(binary_data_file)
