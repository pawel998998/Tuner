import pyaudio
import numpy as np
import tkinter as tk
from tkinter import StringVar
import math

# Ustawienia audio
CHUNK = 4096
RATE = 44100

class FrequencyDetectorApp:
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, root):
        self.root = root
        self.root.title("Detektor Częstotliwości")
        self.root.configure(bg="#1a1a1a")

      
        self.freq_var = StringVar()
        self.freq_var.set(" --- Hz\n---\n---")

    
        self.label = tk.Label(root, textvariable=self.freq_var, font=("Helvetica", 18), justify="left", fg="white", bg="#1a1a1a")
        self.label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=400, height=60, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.create_rectangle(20, 25, 380, 35, fill="#333333", outline="#555555")  # Pasek
        self.center_line = self.canvas.create_line(200, 20, 200, 40, fill="#00cc00", dash=(2, 2))  # Linia środka (zielona)
        self.ball = self.canvas.create_oval(195, 20, 205, 30, fill="#ff3333", outline="#cc0000")  # Kulka (czerwona)

        self.start_button = tk.Button(root, text="Start", command=self.start_detection, font=("Helvetica", 14), bg="#333333", fg="white", activebackground="#555555")
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_detection, font=("Helvetica", 14), bg="#333333", fg="white", activebackground="#555555")
        self.stop_button.pack(pady=5)

        self.running = False
        self.stream = None
        self.current_ball_pos = 200 
        self.target_ball_pos = 200  
        self.last_freq_update = 0  
    def midi_to_note(self, m):
        note_index = m % 12
        octave = (m // 12) - 1
        return self.NOTES[note_index], octave

    def frequency_to_note(self, f):
        if f <= 0:
            return None, None
        m = 69 + 12 * math.log(f / 440, 2)
        m_int = round(m)
        f_note = 440 * (2 ** ((m_int - 69) / 12))
        note_name, octave = self.midi_to_note(m_int)
        return f"{note_name}{octave}", f_note

    def get_precise_frequency(self, data, rate):
        n = len(data) * 16
        fft_data = np.fft.rfft(data, n=n)
        freqs = np.fft.rfftfreq(n, d=1/rate)
        magnitude = np.abs(fft_data)
        peak_index = np.argmax(magnitude)

        if 1 <= peak_index < len(magnitude) - 1:
            alpha = magnitude[peak_index - 1]
            beta = magnitude[peak_index]
            gamma = magnitude[peak_index + 1]
            if alpha != beta and beta != gamma:
                p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
                peak_index += p

        return freqs[int(round(peak_index))]

    def move_ball(self, cents):
        if cents is None:
            self.target_ball_pos = 200
            return

        
        self.target_ball_pos = 200 + cents * 15
        self.target_ball_pos = max(20, min(380, self.target_ball_pos))  

    def animate_ball(self):
        smoothing_factor = 0.1  
        self.current_ball_pos = self.current_ball_pos + smoothing_factor * (self.target_ball_pos - self.current_ball_pos)
        self.canvas.coords(self.ball, self.current_ball_pos - 5, 20, self.current_ball_pos + 5, 30)
        self.root.after(16, self.animate_ball)

    def detect_frequency(self):
        if not self.running:
            return

        # Odczyt danych z mikrofonu
        data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        window = np.hanning(len(data))
        data_windowed = data * window
        freq = self.get_precise_frequency(data_windowed, RATE)

 
        self.last_freq_update += 16 
        if self.last_freq_update >= 100: 
            if freq > 0:
                note, f_note = self.frequency_to_note(freq)
                if note:
                    cents = 1200 * math.log(freq / f_note, 2)
                    if abs(cents) < 1:
                        tuning = "W stroju"
                    elif cents > 0:
                        tuning = f"Za wysoko o {cents:.2f} centów"
                    else:
                        tuning = f"Za nisko o {-cents:.2f} centów"
                    self.freq_var.set(f" {freq:.2f} Hz\n{note}\n{tuning}")
                    self.move_ball(cents)
                else:
                    self.freq_var.set(f" {freq:.2f} Hz\n(Brak nuty)\n---")
                    self.move_ball(None)
            else:
                self.freq_var.set(" --- Hz\n---\n---")
                self.move_ball(None)
            self.last_freq_update = 0 

        if freq > 0:
            _, f_note = self.frequency_to_note(freq)
            if f_note:
                cents = 1200 * math.log(freq / f_note, 2)
                self.move_ball(cents)
            else:
                self.move_ball(None)
        else:
            self.move_ball(None)

        self.root.after(16, self.detect_frequency)

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
            self.animate_ball() 

    def stop_detection(self):
        if self.running:
            self.running = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.freq_var.set(" --- Hz\nNajbliższa nuta: ---\n---")
            self.move_ball(None)

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencyDetectorApp(root)
    root.mainloop()