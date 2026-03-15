import pyaudio
import websocket
import threading
import time
import json
import uuid
import ssl
from openai import OpenAI

# ================= 阿里云流式 ASR 配置 =================
ASR_APPKEY = "nk3MO1E3R4smBfzK"
ASR_TOKEN = "be30e6c3df21443b97bd89c2e47cb4a2"
ASR_URL = f"wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1?token={ASR_TOKEN}"

# ================= 大模型核心配置 (DeepSeek R1/V3) =================
# 这里我们使用完全兼容 OpenAI 接口的免费国内大模型平替（如硅基流动/通义千问等）
# 稍后会让您填入您的 API Key
LLM_API_KEY = "sk-a7f14f9ea7b34373b8c4f72e013b651e"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 以阿里云百炼(通义千问)的兼容接口为例，您也可以换成硅基流动的 DeepSeek

# 初始化大模型客户端
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

# 销售机器人的原始人设
SYSTEM_PROMPT = """你是一个专业的销售客服。
你的目标是简洁、口语化地回应客户。
每次回复不能超过 2 句话，必须像真人在打电话一样，不要使用任何 Markdown 格式，不要说废话。"""

# ================= 录音配置 =================
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 3200

class AIPhoneBot:
    def __init__(self):
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.message_id = uuid.uuid4().hex
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.llm_busy = False # 防止大模型正在思考时被重复触发

    def call_llm(self, customer_text):
        """调用大模型进行思考和回复"""
        self.llm_busy = True
        print(f"\n🧠 [大模型正在思考如何回复...]")
        
        self.conversation_history.append({"role": "user", "content": customer_text})
        
        try:
            # 调用通义千问或 DeepSeek
            response = client.chat.completions.create(
                model="qwen-plus", # 如果用千问就写 qwen-plus/qwen-turbo，如果用 DeepSeek 就写 deepseek-v3
                messages=self.conversation_history,
                temperature=0.7,
            )
            ai_reply = response.choices[0].message.content.strip()
            
            print(f"\n🤖 【AI 销售的话术生成完毕】: {ai_reply}\n")
            
            # 将 AI 的回复存入上下文，以便它记得刚才说了啥
            self.conversation_history.append({"role": "assistant", "content": ai_reply})
            
            print("[等待您继续说话...] 👇")
            
        except Exception as e:
            print(f"\n❌ 大模型请求失败: {e}。请检查您的 API Key 是否正确填写！")
        finally:
            self.llm_busy = False

    def on_open(self, ws):
        print("\n[网络] 🟢 ASR 语音大脑连接成功。请直接对着麦克风说话！")
        # 使用 SpeechTranscriber（实时转写），它会自动断句并触发 SentenceEnd
        req = {
            "header": {
                "message_id": uuid.uuid4().hex,
                "task_id": self.message_id,
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription",
                "appkey": ASR_APPKEY
            },
            "payload": {
                "format": "pcm",
                "sample_rate": 16000,
                "enable_intermediate_result": True,
                "enable_punctuation_prediction": True,
                "enable_inverse_text_normalization": True
            }
        }
        ws.send(json.dumps(req))
        self.is_recording = True
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        threading.Thread(target=self.send_audio_thread, daemon=True).start()

    def send_audio_thread(self):
        try:
            while self.is_recording and self.ws and self.ws.sock and self.ws.sock.connected:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                # 即使大模型正在思考，我们也持续推流，以便检测用户打断
                self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.01)
        except Exception:
            pass

    def on_message(self, ws, message):
        try:
            res = json.loads(message)
            name = res.get('header', {}).get('name')
            payload = res.get('payload', {})
            text = payload.get('result', '')
            
            if name == 'TranscriptionResultChanged' and text:
                # 中间结果：边说边出字
                print(f"\r🗣️ [客户正在说]: {text}        ", end="", flush=True)
            elif name == 'SentenceEnd' and text:
                # 阿里云检测到一句话说完了！这是触发大模型的关键事件
                print(f"\r🚀 【客户说完了】: {text}                          \n")
                # 立刻扔给大模型大脑
                if not self.llm_busy:
                    threading.Thread(target=self.call_llm, args=(text,), daemon=True).start()
            elif name == 'TranscriptionStarted':
                print("[系统] 实时转写已启动，请开始说话...\n")
            elif name == 'TranscriptionCompleted':
                print("\n[系统] ASR 识别流正常结束。")
            elif name == 'TaskFailed':
                print(f"\n[错误] 服务端报错: {res.get('header', {}).get('status_text')}")
                
        except Exception as e:
            print(f"解析出错: {e}, 原始消息: {message}")

    def on_error(self, ws, error):
        print(f"\n[网络错误]: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("\n[网络] 🔴 连接断开。")
        self.stop_recording()

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def start(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            ASR_URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    if LLM_API_KEY == "PLEASE_REPLACE_WITH_YOUR_KEY":
        print("大模型 API Key 尚未配置。为了测试，请先在代码中替换 LLM_API_KEY！")
    else:
        bot = AIPhoneBot()
        try:
            bot.start()
        except KeyboardInterrupt:
            bot.stop_recording()
            print("\n[手动停止] 会话结束。")
