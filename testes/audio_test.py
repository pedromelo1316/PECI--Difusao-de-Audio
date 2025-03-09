# Teste simples de reprodução
import sounddevice as sd
import numpy as np

duration = 3  # seconds
frequency = 440  # Hz
SAMPLE_RATE = 44100

t = np.linspace(0, duration, int(duration * SAMPLE_RATE), False)
wave = 0.5 * np.sin(2 * np.pi * frequency * t)
sd.play(wave, samplerate=SAMPLE_RATE)
sd.wait()