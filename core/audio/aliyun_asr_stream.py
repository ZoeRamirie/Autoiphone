import pyaudio
import websocket
import threading
import time
import json
import uuid
import ssl

# ================= 阿里云配置 =================
APPKEY = "nk3MO1E3R4smBfzK"
TOKEN = "be30e6c3df21443b97bd89c2e47cb4a2"
# 阿里云 WebSocket 接口地址
URL = f"wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1?token={TOKEN}"

# ================= 音频采集配置 =================
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 3200  # 每次读取 200ms 的音频数据送给云端

class AliyunASR:
    def __init__(self):
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.message_id = uuid.uuid4().hex

    def on_open(self, ws):
        print("\n[网络] 🟢 已连接到阿里云大模型语音大脑！")
        
        # 1. 发送开始识别指令
        req = {
            "header": {
                "message_id": uuid.uuid4().hex,
                "task_id": self.message_id,
                "namespace": "SpeechRecognizer",
                "name": "StartRecognition",
                "appkey": APPKEY
            },
            "payload": {
                "format": "pcm",
                "sample_rate": 16000,
                "enable_intermediate_result": True,  # 开启中间结果返回（实现立刻出字的灵魂）
                "enable_punctuation_prediction": True,
                "enable_inverse_text_normalization": True
            }
        }
        ws.send(json.dumps(req))
        
        # 2. 启动录音线程持续推流
        self.is_recording = True
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        threading.Thread(target=self.send_audio_thread, daemon=True).start()
        print("[状态] 🎤 电脑麦克风已开启，您可以随便开始说话了！(按 Ctrl+C 结束)\n")

    def send_audio_thread(self):
        try:
            while self.is_recording and self.ws and self.ws.sock and self.ws.sock.connected:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                # 直接发送二进制的 PCM 音频块给 WebSocket
                self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.01)
        except Exception as e:
            pass

    def on_message(self, ws, message):
        try:
            res = json.loads(message)
            header = res.get('header', {})
            payload = res.get('payload', {})
            name = header.get('name')
            
            text = payload.get('result', '')
            
            if name == 'RecognitionResultChanged':
                # 这里就是“边说边出字”的中间结果！
                # 使用 \r 回车但不换行，实现同一行文字的滚动更新效果
                print(f"\r🗣️ [正在听]: {text}        ", end="", flush=True)
            elif name == 'RecognitionCompleted':
                # AI 判断您的一句话说完了，给出最终加了标点的结果
                print(f"\r🚀 【整句确认】: {text}                          \n")
            elif name == 'TaskFailed':
                print(f"\n[错误] 服务端报错: {header.get('status_text')}")
        except Exception as e:
            print(f"解析出错: {e}")

    def on_error(self, ws, error):
        print(f"\n[网络错误]: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("\n[网络] 🔴 连接已断开。")
        self.stop_recording()

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
    def start(self):
        # 建立长连接
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    print("=== Autoiphone 阿里云流式 ASR 极速测试 ===")
    print(f"加载 Appkey: {APPKEY}")
    asr = AliyunASR()
    try:
        asr.start()
    except KeyboardInterrupt:
        asr.stop_recording()
        print("\n[手动停止] 程序已结束。")
