from flask import Flask, request, jsonify
import threading
import requests
import json
import base64
from pyaudio import PyAudio, paInt16
import wave

app = Flask(__name__)

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

# 录音控制
is_recording = False

def input_thread():
    global is_recording
    while True:
        command = input()
        if command == '1':
            is_recording = True
            print('正在录音...')
        elif command == '2':
            is_recording = False
            print('录音结束.')

# 录音函数
def my_record():
    global is_recording
    pa = PyAudio()
    stream = pa.open(format=paInt16, channels=channels,
                     rate=framerate, input=True, frames_per_buffer=num_samples)
    my_buf = []

    # 启动输入线程
    thread = threading.Thread(target=input_thread)
    thread.daemon = False
    thread.start()

    while True:
        if is_recording:
            string_audio_data = stream.read(num_samples)
            my_buf.append(string_audio_data)
        elif not is_recording and my_buf:
            save_wave_file(FILEPATH, my_buf)
            stream.close()
            return

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
                return "翻译结果解析失败"
        else:
            return "API响应中没有找到 'result' 字典"
    except requests.exceptions.RequestException as e:
        return f"请求翻译API时发生错误：{e}"

@app.route('/record', methods=['POST'])
def record():
    global is_recording
    is_recording = not is_recording
    if is_recording:
        threading.Thread(target=my_record).start()
        return jsonify({"status": "recording"})
    else:
        return jsonify({"status": "stopped"})

@app.route('/process', methods=['POST'])
def process_audio():
    TOKEN_ASR = getToken(HOST_ASR)  # 获取语音识别的access_token
    speech = get_audio(FILEPATH)  # 获取音频数据
    result_cn = speech2text(speech, TOKEN_ASR)  # 语音识别
    if result_cn:
        TOKEN_MT = getToken(HOST_MT)  # 获取机器翻译的access_token
        translation = translate_text(result_cn, TOKEN_MT)  # 翻译文本
        return jsonify({"speech_result": result_cn, "translation_result": translation})
    else:
        return jsonify({"error": "语音识别失败"})

if __name__ == '__main__':
    app.run(debug=True)