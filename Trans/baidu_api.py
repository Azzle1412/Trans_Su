import requests
import base64
import urllib3

# 关闭HTTPS请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 百度语音识别API密钥和密钥
APIKey_ASR = "AtyMxF2zsxDyuMrfK8cKg8uk"
SecretKey_ASR = "lrtDArdly4i3CAfa0ykdbztYDGGhLrM2"
HOST_ASR = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={APIKey_ASR}&client_secret={SecretKey_ASR}"

# 百度机器翻译API密钥和密钥
APIKey_MT = "lH4qWAZewQQSb7QquKosyDOl"
SecretKey_MT = "pDjb3YOVu2drXKRCPIZk0chLdlPc0Zuc"
HOST_MT = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={APIKey_MT}&client_secret={SecretKey_MT}"

def getToken(host):
    res = requests.post(host, verify=False)
    return res.json()['access_token']

def get_audio(file):
    with open(file, 'rb') as f:
        data = f.read()
    return data

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
    r = requests.post(url, json=data, headers=headers, verify=False)
    Result = r.json()
    return Result.get('result', [None])[0]

def translate_text(query, token):
    url_mt = 'https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1'
    headers_mt = {'Content-Type': 'application/json'}
    payload_mt = {'q': query, 'from': 'auto', 'to': 'en'}
    try:
        response = requests.post(url_mt, json=payload_mt, headers=headers_mt, params={'access_token': token}, verify=False)
        response.raise_for_status()  # 如果请求返回了失败的状态码，将抛出异常
        result = response.json()

        if 'result' in result:
            translation_result = result['result']
            if 'trans_result' in translation_result:
                return translation_result['trans_result'][0]['dst']
            else:
                print("警告：在 'result' 字典中没有找到 'trans_result' 字段")
        else:
            print("警告：API响应中没有找到 'result' 字典")
            if 'error_msg' in result:
                print(f"错误信息：{result['error_msg']}")

    except requests.exceptions.RequestException as e:
        print(f"请求翻译API时发生错误：{e}")
        return None