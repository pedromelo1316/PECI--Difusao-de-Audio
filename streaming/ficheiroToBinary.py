from pydub import AudioSegment

# Abrir o ficheiro MP3
audio = AudioSegment.from_mp3("Twenty One Pilots - Paladin Strait (Official Video) [mix9YfaaNa0].mp3")

# Exportar o áudio para bytes
raw_data = audio.raw_data

# Converter cada byte em binário
binario = ''.join(format(byte, '08b') for byte in raw_data)
hexadecimal = ''.join(format(byte, '02x') for byte in raw_data)

# Exibir parte do resultado

print(binario[:200])  # Mostra os primeiros 200 bits para visualização
print('----')
print(hexadecimal[:9999])  # Mostra os primeiros 200 caracteres em hexadecimal para visualização
