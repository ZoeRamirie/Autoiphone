"""
Autoiphone 全链路 AI 外呼脚本
ADB 拨号 → 阿里云 ASR 实时听取 → 通义千问流式思考 → CosyVoice 零样本流式播报 
"""
import os
import sys
import subprocess
import time
import json
import uuid
import threading
import ssl
import asyncio

import pyaudio
import websocket
import requests
import dashscope
from openai import OpenAI
from core.audio.tts_engine import CosyVoiceEngine, EdgeTTSEngine

# ======= 全局 SSL 修复 =======
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context

# ======= 配置区 =======
ASR_APPKEY = "nk3MO1E3R4smBfzK"
ASR_TOKEN = "be30e6c3df21443b97bd89c2e47cb4a2"
ASR_URL = f"wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1?token={ASR_TOKEN}"

LLM_API_KEY = "sk-a7f14f9ea7b34373b8c4f72e013b651e"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
dashscope.api_key = LLM_API_KEY

llm_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

SYSTEM_PROMPT = """你是一个正在打电话的真人销售，正在推销智能办公系统。

极其重要的规则（必须严格遵守）：
1. 每次回复只说一句话，不超过20个字。多了就像机器人了！
2. 说话像真人打电话：加“嘞”“哈”“对对对”“是的呢”“没错”这种口语词。
3. 绝对禁止用书面语、绝对禁止用“您好我是”开头（开场白除外）。
4. 绝对禁止使用 Markdown、表情符号、括号、引号等任何特殊符号。
5. 客户拒绝就立刻礼貌告别，不要纠缠。
6. 禁止重复说过的话！已经介绍过就不要再介绍。
7. 根据客户回答自然推进对话，别原地打转。

话术风格示例：
- “嘞您现在方便聊两句不？”
- “对对对，就是这个意思”
- “哈那我加您微信发您看看？”
- “行不打扰您了，再见哈”"""

VOICE_SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "audio", "my_voice.wav")

# 音频配置
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 3200

class AIPhoneCaller:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_active = False
        self.task_id = uuid.uuid4().hex
        self.llm_busy = False
        self.conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.call_connected = False
        
        # 新增引擎与回声处理标志
        self.engine = None
        self.last_ai_speak_end = 0

    # ====== 第 0 步：准备声纹 ======
    def prepare_voice(self):
        print("\n[步骤 0/4] 🎤 准备语音引擎...")
        try:
            self.engine = CosyVoiceEngine(api_key=LLM_API_KEY, prompt_audio_path=VOICE_SAMPLE_PATH)
            if not self.engine.prepare():
                print("  ⚠️ CosyVoice 初始化失败，降级使用 Edge-TTS")
                self.engine = EdgeTTSEngine()
                self.engine.prepare()
        except Exception as e:
            print(f"  ⚠️ 初始化引擎报错: {e}，降级 Edge-TTS")
            self.engine = EdgeTTSEngine()
            self.engine.prepare()
        return True

    # ====== 通话状态检测辅助方法 ======
    def _get_call_state(self):
        result = subprocess.run(["adb", "shell", "dumpsys", "telecom"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        in_mcalls = False
        mcalls_lines = []
        for line in lines:
            if 'mCalls:' in line:
                in_mcalls = True
                continue
            if in_mcalls:
                if line.strip() and not line.startswith('  '):
                    break
                mcalls_lines.append(line)
                if len(mcalls_lines) > 30:
                    break
        
        mcalls_text = '\n'.join(mcalls_lines)
        if not mcalls_text.strip():
            return "IDLE"
        
        if 'ACTIVE' in mcalls_text:
            return "ACTIVE"
        elif 'DIALING' in mcalls_text or 'CONNECTING' in mcalls_text:
            return "DIALING"
        elif 'RINGING' in mcalls_text:
            return "RINGING"
        elif 'DISCONNECTED' in mcalls_text or 'DISCONNECTING' in mcalls_text:
            return "DISCONNECTED"
        
        for line in lines[:10]:
            if 'Active dialing, or connecting calls:' in line:
                idx = lines.index(line)
                next_line = lines[idx + 1] if idx + 1 < len(lines) else ''
                if next_line.strip():
                    return "DIALING"
        
        return "UNKNOWN"

    def _is_call_alive(self):
        result = subprocess.run(["adb", "shell", "dumpsys", "telephony.registry"], capture_output=True, text=True)
        states = [line.strip() for line in result.stdout.split('\n') if 'mCallState=' in line]
        for s in states:
            if 'mCallState=2' in s or 'mCallState=1' in s:
                return True
        return False

    # ====== 第 1 步：ADB 拨号 ======
    def dial(self):
        print(f"\n[步骤 1/4] 📱 正在拨打 {self.phone_number}...")
        subprocess.run(["adb", "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{self.phone_number}"], capture_output=True)
        
        print("  📞 已拨出（音频走线缆），等待对方接听...")
        
        dialing_detected = False
        for i in range(60):
            state = self._get_call_state()
            
            if state == "ACTIVE":
                print(f"\n  ✅ 对方已接听！通话正式建立！")
                self.call_connected = True
                return True
            elif state in ["DIALING", "UNKNOWN"]:
                dialing_detected = True
                if i % 5 == 0:
                    print(f"  📞 对方手机正在响铃中... ({i}s)")
            elif state in ["DISCONNECTED", "IDLE"]:
                if dialing_detected:
                    print("  ❌ 对方拒接或未接听。")
                    return False
            time.sleep(1)
        
        print("  ⏰ 等待 60 秒超时，对方未接听。")
        return False

    # ====== 第 2 步：ASR 开始监听 ======
    def start_listening(self):
        print(f"\n[步骤 2/4] 👂 启动 ASR 实时监听...")
        
        def on_open(ws):
            print("  🟢 ASR 连接成功，正在监听对话...")
            req = {
                "header": {
                    "message_id": uuid.uuid4().hex,
                    "task_id": self.task_id,
                    "namespace": "SpeechTranscriber",
                    "name": "StartTranscription",
                    "appkey": ASR_APPKEY
                },
                "payload": {
                    "format": "pcm", "sample_rate": 16000,
                    "enable_intermediate_result": True,
                    "enable_punctuation_prediction": True,
                    "enable_inverse_text_normalization": True
                }
            }
            ws.send(json.dumps(req))
            self.is_active = True
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            threading.Thread(target=self._push_audio, daemon=True).start()
            
            # 电话接通后，AI 先主动开口（利用新流式引擎极速响应，无需预合成文件）
            threading.Thread(target=self._ai_speak_first, daemon=True).start()

        def on_message(ws, message):
            # ===== 强回声消除逻辑 =====
            if self.engine and self.engine.is_speaking:
                return # 忽略 AI 播发期间的任何听测
            if time.time() - self.last_ai_speak_end < 0.4:
                return # 给麦克风留 400ms 冷静期，防止残余回声
                
            res = json.loads(message)
            name = res.get('header', {}).get('name')
            text = res.get('payload', {}).get('result', '')
            
            if name == 'TranscriptionResultChanged' and text:
                print(f"\r  👤 [客户]: {text}        ", end="", flush=True)
            elif name == 'SentenceEnd' and text:
                print(f"\r  👤 【客户说】: {text}                    ")
                if not self.llm_busy:
                    threading.Thread(target=self._think_and_reply, args=(text,), daemon=True).start()

        def on_error(ws, error):
            if self.is_active:
                print(f"\n  [ASR 网络异常]: {error}")

        def on_close(ws, code, msg):
            print("\n  [ASR 连接关闭]")

        self.ws = websocket.WebSocketApp(ASR_URL, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        threading.Thread(target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}), daemon=True).start()

    def _push_audio(self):
        silence = b'\x00' * CHUNK * 2
        try:
            while self.is_active and self.ws and self.ws.sock and self.ws.sock.connected:
                # 播报或冷静期内：下发静音数据并强行清空本地缓冲区积攒的声音
                if (self.engine and self.engine.is_speaking) or (time.time() - self.last_ai_speak_end < 0.4):
                    self.ws.send(silence, opcode=websocket.ABNF.OPCODE_BINARY)
                    if self.stream.get_read_available() > 0:
                        self.stream.read(self.stream.get_read_available(), exception_on_overflow=False)
                else:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.01)
        except:
            pass

    # ====== 第 3 步：LLM 流式思考与 TTS 切片播报 ======
    def _ai_speak_first(self):
        time.sleep(0.3)
        self._think_and_reply("[系统提示: 电话刚刚接通，请你先开口问好并自我介绍，不超过15个字]")

    def _think_and_reply(self, customer_text):
        self.llm_busy = True
        print(f"\n  🧠 [AI 思考中...]")
        
        self.conversation.append({"role": "user", "content": customer_text})
        try:
            start_t = time.time()
            response = llm_client.chat.completions.create(
                model="qwen-turbo",
                messages=self.conversation,
                temperature=0.7,
                stream=True
            )
            
            punctuations = set(['。', '！', '？', '，', '；', ',', '!', '?'])
            collected_chunk = ""
            full_reply = ""
            
            first_fragment = True
            for chunk in response:
                if not chunk.choices or (self.engine and getattr(self.engine, '_abort', False)):
                    break
                text = chunk.choices[0].delta.content or ""
                collected_chunk += text
                full_reply += text
                
                # 遇到标点即刻送播
                if any(p in text for p in punctuations):
                    fragment = collected_chunk.strip()
                    if fragment:
                        if first_fragment:
                            print(f"  ⚡️ [首包耗时: {time.time()-start_t:.2f}s]")
                            first_fragment = False
                        print(f"  🤖 【AI 话术】: {fragment}")
                        if self.engine:
                            self.engine.speak_streaming(fragment)
                        collected_chunk = ""
            
            # 补齐尾巴
            fragment = collected_chunk.strip()
            if fragment and not (self.engine and getattr(self.engine, '_abort', False)):
                print(f"  🤖 【AI 话术尾缀】: {fragment}")
                if self.engine:
                    self.engine.speak_streaming(fragment)
                
            self.conversation.append({"role": "assistant", "content": full_reply})
            if self.engine:
                self.last_ai_speak_end = time.time() # 记录播报确切结束的时间，开始 400ms 冷静期
            print(f"  ✅ 播报完毕。")
                
        except Exception as e:
            print(f"  ❌ LLM/TTS 管道错误: {e}")
        finally:
            self.llm_busy = False

    # ====== 挂断 ======
    def hangup(self):
        print("\n[系统] 📵 正在挂断电话...")
        self.is_active = False
        
        if self.engine:
            self.engine.stop()
        
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_ENDCALL"], capture_output=True)
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        print("[系统] 通话结束。\n")

    # ====== 主流程 ======
    def run(self):
        print("=" * 55)
        print("🚀 Autoiphone AI 全自动外呼系统 (流式超低延迟版)")
        print("=" * 55)
        
        if not self.prepare_voice():
            return
        
        if not self.dial():
            return
            
        self.start_listening()
        
        print("\n[系统] 等待 ASR 连接就绪...")
        for _ in range(10):
            if self.is_active:
                break
            time.sleep(1)
        
        if not self.is_active:
            print("[系统] ❌ ASR 连接超时，中止。")
            self.hangup()
            return
        
        print("\n[系统] 🟢 AI 外呼全链路已启动！")
        print("[系统] 按 Ctrl+C 可手动挂断结束测试。\n")
        try:
            while self.is_active:
                if not self._is_call_alive():
                    print("\n[系统] 检测到通话已结束。")
                    break
                time.sleep(3)
        except KeyboardInterrupt:
            print("\n[系统] 手动中止。")
        
        self.hangup()
        
        print("\n" + "=" * 55)
        print("📝 本次通话完整对话记录：")
        print("=" * 55)
        for msg in self.conversation:
            if msg["role"] == "user" and not msg["content"].startswith("[系统"):
                print(f"  👤 客户: {msg['content']}")
            elif msg["role"] == "assistant":
                print(f"  🤖 AI:   {msg['content']}")
        print("=" * 55)

if __name__ == "__main__":
    test_number = input("请输入要拨打的测试号码（建议用自己的另一个手机）: ").strip()
    if not test_number:
        print("未输入号码，退出。")
        sys.exit(0)
    
    os.environ["SSL_CERT_FILE"] = subprocess.run(["python3", "-m", "certifi"], capture_output=True, text=True).stdout.strip()
    
    caller = AIPhoneCaller(test_number)
    caller.run()
