import os
import soundfile as sf

audio_filename = 'gravacao.wav'

os.system(f'ffmpeg -f alsa -i default -t 5 -y {audio_filename}')

data, samplerate = sf.read(audio_filename)
print(f"Áudio gravado com taxa de amostragem: {samplerate} Hz")
print(f"Número de amostras: {data.shape[0]}")