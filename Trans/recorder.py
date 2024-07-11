import threading
from pyaudio import PyAudio, paInt16
import wave

# 录音参数
framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2bytes
FILEPATH = 'speech.wav'

def save_wave_file(filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.pa = PyAudio()
        self.stream = self.pa.open(format=paInt16, channels=channels,
                                   rate=framerate, input=True, frames_per_buffer=num_samples)
        self.my_buf = []

    def start_recording(self):
        self.is_recording = True
        self.my_buf = []
        threading.Thread(target=self.record).start()

    def stop_recording(self):
        self.is_recording = False

    def record(self):
        while self.is_recording:
            string_audio_data = self.stream.read(num_samples)
            self.my_buf.append(string_audio_data)
        save_wave_file(FILEPATH, self.my_buf)
        self.stream.close()