import pyaudio
import numpy as np
import tkinter as tk
from tkinter import StringVar

# Ustawienia audio
CHUNK = 4096
RATE = 44100

class FrequencyDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detektor Częstotliwości")

        # Zmienna do wyświetlania częstotliwości
        self.freq_var = StringVar()
        self.freq_var.set("Częstotliwość: --- Hz")

        # Tworzenie interfejsu
        self.label = tk.Label(root, textvariable=self.freq_var, font=("Helvetica", 24))
        self.label.pack(pady=20)

        self.start_button = tk.Button(root, text="Start", command=self.start_detection, font=("Helvetica", 14))
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_detection, font=("Helvetica", 14))
        self.stop_button.pack(pady=10)

        # Flagi i strumień
        self.running = False
        self.stream = None

    def get_precise_frequency(self, data, rate):
        n = len(data) * 4
        fft_data = np.fft.rfft(data, n=n)
        freqs = np.fft.rfftfreq(n, d=1/rate)
        magnitude = np.abs(fft_data)
        peak_index = np.argmax(magnitude)

        if 1 <= peak_index < len(magnitude) - 1:
            alpha = magnitude[peak_index - 1]
            beta = magnitude[peak_index]
            gamma = magnitude[peak_index + 1]
            p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
            peak_index += p

        return freqs[int(round(peak_index))]

    def detect_frequency(self):
        if not self.running:
            return

        # Odczyt danych z mikrofonu
        data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        window = np.hanning(len(data))
        data_windowed = data * window
        freq = self.get_precise_frequency(data_windowed, RATE)

        # Aktualizacja etykiety
        self.freq_var.set(f"Częstotliwość: {freq:.1f} Hz")

        # Wywołanie ponowne po 100 ms
        self.root.after(100, self.detect_frequency)

    def start_detection(self):
        if not self.running:
            self.running = True
            p = pyaudio.PyAudio()
            self.stream = p.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=RATE,
                                 input=True,
                                 frames_per_buffer=CHUNK)
            self.detect_frequency()

    def stop_detection(self):
        if self.running:
            self.running = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.freq_var.set("Częstotliwość: --- Hz")

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencyDetectorApp(root)
    root.mainloop()
