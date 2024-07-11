import sys
import threading
import requests
import json
import base64
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from pyaudio import PyAudio, paInt16
import wave

# 以下参数根据实际情况进行设置
framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2bytes
FILEPATH = 'speech.wav'

# 百度语音识别API密钥和密钥
APIKey_ASR = "AtyMxF2zsxDyuMrfK8cKg8uk"
SecretKey_ASR = "lrtDArdly4i3CAfa0ykdbztYDGGhLrM2"
HOST_ASR = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={APIKey_ASR}&client_secret={SecretKey_ASR}"

# 百度机器翻译API密钥和密钥
APIKey_MT = "lH4qWAZewQQSb7QquKosyDOl"
SecretKey_MT = "pDjb3YOVu2drXKRCPIZk0chLdlPc0Zuc"
HOST_MT = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={APIKey_MT}&client_secret={SecretKey_MT}"

# 获取访问令牌的函数
def getToken(host):
    res = requests.post(host)
    return res.json()['access_token']

# 保存WAV文件的函数
def save_wave_file(filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()

# 获取音频数据的函数
def get_audio(file):
    with open(file, 'rb') as f:
        data = f.read()
    return data

# 语音识别函数
def speech2text(speech_data, token, dev_pid=1537):
    FORMAT = 'wav'
    RATE = '16000'
    CHANNEL = 1
    CUID = 'BA-31-B5-98-BB-36'
    SPEECH = base64.b64encode(speech_data).decode('utf-8')

    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid
    }
    url = 'https://vop.baidu.com/server_api'
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, json=data, headers=headers)
    Result = r.json()
    return Result.get('result', [None])[0]

# 机器翻译函数
def translate_text(query, token):
    url_mt = 'https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1'
    headers_mt = {'Content-Type': 'application/json'}
    payload_mt = {'q': query, 'from': 'auto', 'to': 'en'}
    try:
        response = requests.post(url_mt, json=payload_mt, headers=headers_mt, params={'access_token': token})
        response.raise_for_status()  # 如果请求返回了失败的状态码，将抛出异常
        result = response.json()

        if 'result' in result:
            translation_result = result['result']
            if 'trans_result' in translation_result:
                return translation_result['trans_result'][0]['dst']
            else:
                return "警告：在 'result' 字典中没有找到 'trans_result' 字段"
        else:
            if 'error_msg' in result:
                return f"错误信息：{result['error_msg']}"
            return "警告：API响应中没有找到 'result' 字典"
    except requests.exceptions.RequestException as e:
        return f"请求翻译API时发生错误：{e}"

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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.recorder = Recorder()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('语音识别与翻译')
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()

        self.recordButton = QPushButton('开始录音', self)
        self.recordButton.clicked.connect(self.startRecording)
        self.layout.addWidget(self.recordButton)

        self.stopButton = QPushButton('结束录音', self)
        self.stopButton.clicked.connect(self.stopRecording)
        self.layout.addWidget(self.stopButton)

        self.resultLabel = QLabel('识别的中文文本:', self)
        self.layout.addWidget(self.resultLabel)

        self.resultText = QTextEdit(self)
        self.resultText.setReadOnly(True)
        self.layout.addWidget(self.resultText)

        self.translationLabel = QLabel('翻译的英文文本:', self)
        self.layout.addWidget(self.translationLabel)

        self.translationText = QTextEdit(self)
        self.translationText.setReadOnly(True)
        self.layout.addWidget(self.translationText)

        self.setLayout(self.layout)

    def startRecording(self):
        self.recorder.start_recording()
        self.resultText.clear()
        self.translationText.clear()

    def stopRecording(self):
        self.recorder.stop_recording()
        threading.Thread(target=self.processRecording).start()

    def processRecording(self):
        TOKEN_ASR = getToken(HOST_ASR)
        speech = get_audio(FILEPATH)
        result_cn = speech2text(speech, TOKEN_ASR)
        self.resultText.setText(result_cn)

        if result_cn:
            TOKEN_MT = getToken(HOST_MT)
            translation = translate_text(result_cn, TOKEN_MT)
            self.translationText.setText(translation)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())