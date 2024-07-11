import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit
from recorder import Recorder, FILEPATH
from baidu_api import getToken, get_audio, speech2text, translate_text, HOST_ASR, HOST_MT

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

    def stopRecording(self):
        self.recorder.stop_recording()
        threading.Thread(target=self.processRecording).start()

    def processRecording(self):
        TOKEN_ASR = getToken(HOST_ASR)  # 获取语音识别的access_token
        speech = get_audio(FILEPATH)  # 获取音频数据
        result_cn = speech2text(speech, TOKEN_ASR)  # 语音识别
        if result_cn:
            self.resultText.setText(result_cn)
            TOKEN_MT = getToken(HOST_MT)  # 获取机器翻译的access_token
            translation = translate_text(result_cn, TOKEN_MT)  # 翻译文本
            self.translationText.setText(translation)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())