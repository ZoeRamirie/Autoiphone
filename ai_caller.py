"""
Autoiphone 重构版 AI 外呼脚本
核心逻辑：EventBus 驱动 ASR -> LLM -> TTS 流转
"""
import os
import sys
import subprocess
import time
import threading
import ssl
import re
import pyaudio
from core.event_bus import bus
from core.audio.asr_engine import AliyunASREngine
from core.audio.tts_engine import CosyVoiceEngine, EdgeTTSEngine
from core.llm_engine import LLMEngine

# ======= 自动加载 .env 环境配置 =======
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key] = val

ASR_APPKEY = "nk3MO1E3R4smBfzK"
ASR_AK_ID = os.getenv("ASR_AK_ID")
ASR_AK_SECRET = os.getenv("ASR_AK_SECRET")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VOICE_SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "audio", "my_voice.wav")

SYSTEM_PROMPT = """你是一个正在打电话的真人销售，正在推销智能办公系统。

极其重要的规则（必须严格遵守）：
1. 每次回复只说一句话，不超过20个字。多了就像机器人了！
2. 说话像真人打电话：加“嘞”“哈”“对对对”“是的呢”“没错”这种口语词。
3. 绝对禁止用书面语、绝对禁止用“您好我是”开头（开场白除外）。
4. 绝对禁止使用 Markdown、表情符号、括号、引号等任何特殊符号。
5. 客户拒绝就立刻礼貌告别，不要纠缠。
6. 禁止重复说过的话！已经介绍过就不要再介绍。
7. 根据客户回答自然推进对话，别原地打转。
"""

# 音频配置
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 3200
INPUT_DEVICE_INDEX = int(os.getenv("ASR_INPUT_DEVICE_INDEX", "0"))
STRICT_AUDIO_ROUTE = os.getenv("STRICT_AUDIO_ROUTE", "1") == "1"

class AIPhoneCaller:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_active = False
        
        # 引擎
        self.asr = AliyunASREngine(ASR_APPKEY, access_key_id=ASR_AK_ID, access_key_secret=ASR_AK_SECRET)
        self.llm = LLMEngine(LLM_API_KEY, LLM_BASE_URL, SYSTEM_PROMPT)
        self.tts = None
        
        # 状态
        self.ai_is_speaking = False
        self.last_ai_speak_end = 0
        
        # 绑定事件
        self._bind_events()

    def _bind_events(self):
        bus.subscribe("asr_ready", self._on_asr_ready)
        bus.subscribe("customer_speaking", self._on_customer_speaking)
        bus.subscribe("customer_sentence_end", self._on_customer_sentence_end)
        bus.subscribe("ai_text_chunk", self._on_ai_text_chunk)
        bus.subscribe("ai_speak_start", self._on_ai_speak_start)
        bus.subscribe("ai_speak_end", self._on_ai_speak_end)

    def _on_asr_ready(self):
        print(f"[System] ASR Ready, starting audio stream (Input Index: {INPUT_DEVICE_INDEX})...")
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )
        threading.Thread(target=self._push_audio_loop, daemon=True).start()
        
        # 开场白
        threading.Thread(target=lambda: self.llm.think_and_reply("[系统提示: 电话已接通，请开始简短的开场白问候]"), daemon=True).start()

    def _on_customer_speaking(self, text):
        if not self.ai_is_speaking:
            print(f"\r👤 [客户]: {text}        ", end="", flush=True)

    def _on_customer_sentence_end(self, text):
        print(f"\r👤 【客户说】: {text}                    ")
        if not self.llm.is_thinking:
            threading.Thread(target=lambda: self.llm.think_and_reply(text), daemon=True).start()

    def _on_ai_text_chunk(self, text):
        print(f"🤖 【AI 话术】: {text}")
        if self.tts:
            # 专项测试：只播固定测试语句，连播3次
            test_text = "听到请说1"
            for _ in range(3):
                self.tts.speak_streaming(test_text)
            return

    def _on_ai_speak_start(self):
        self.ai_is_speaking = True
        print("  🔊 AI 开始说话...")

    def _on_ai_speak_end(self):
        self.ai_is_speaking = False
        self.last_ai_speak_end = time.time()
        print("  ✅ AI 说话完毕。")

    def _push_audio_loop(self):
        silence = b'\x00' * CHUNK * 2
        try:
            while self.is_active and self.asr.is_active:
                # 强回声抑制逻辑
                if self.ai_is_speaking or (time.time() - self.last_ai_speak_end < 0.4):
                    self.asr.send_audio(silence)
                    if self.stream.get_read_available() > 0:
                        self.stream.read(self.stream.get_read_available(), exception_on_overflow=False)
                else:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    self.asr.send_audio(data)
                time.sleep(0.01)
        except Exception as e:
            print(f"[Audio] Loop error: {e}")

    # ====== 基础外设控制 ======
    def prepare(self):
        print("\n[Init] 🎤 Preparing engines...")
        try:
            self.tts = CosyVoiceEngine(api_key=LLM_API_KEY, prompt_audio_path=VOICE_SAMPLE_PATH)
            if not self.tts.prepare():
                print("  ⚠️ CosyVoice failed, using Edge-TTS")
                self.tts = EdgeTTSEngine()
                self.tts.prepare()
        except Exception as e:
            print(f"  ⚠️ TTS Init error: {e}, using Edge-TTS")
            self.tts = EdgeTTSEngine()
            self.tts.prepare()
        return True

    def _adb(self, args, timeout=8, text=True):
        """统一执行 adb 命令，减少重复代码并补齐错误日志"""
        try:
            return subprocess.run(["adb"] + args, capture_output=True, text=text, timeout=timeout)
        except FileNotFoundError:
            print("  ❌ adb not found. Please install Android platform-tools.")
        except subprocess.TimeoutExpired:
            print(f"  ❌ adb timeout: {' '.join(args)}")
        except Exception as e:
            print(f"  ❌ adb error: {e}")
        return None

    def _ensure_device_ready(self):
        """检查是否有在线设备，避免空跑"""
        res = self._adb(["devices"], timeout=5)
        if not res or res.returncode != 0:
            return False
        lines = [line for line in (res.stdout or "").splitlines()[1:] if line.strip()]
        online = [line for line in lines if "\tdevice" in line]
        if not online:
            print("  ❌ No online Android device found via adb devices.")
            return False
        print(f"  ✅ ADB device ready: {online[0].split()[0]}")
        return True

    def _get_precise_call_state(self):
        """读取 telephony + telecom，返回更可读的通话状态"""
        telephony = self._adb(["shell", "dumpsys", "telephony.registry"], timeout=8)
        if not telephony or telephony.returncode != 0:
            return "UNKNOWN"

        m = re.search(r"mCallState=(\d+)", telephony.stdout or "")
        if not m:
            return "UNKNOWN"

        code = m.group(1)
        if code == "0":
            return "IDLE"
        if code == "1":
            return "RINGING"

        telecom = self._adb(["shell", "dumpsys", "telecom"], timeout=8)
        if telecom and telecom.returncode == 0:
            states = re.findall(r"State:\s*([A-Z_]+)", telecom.stdout or "")
            valid_states = [s for s in states if s in {"DIALING", "ACTIVE", "DISCONNECTED", "CONNECTING"}]
            if valid_states:
                # dumpsys telecom 可能包含历史状态，取最后一个更接近当前实际状态
                return f"OFFHOOK->{valid_states[-1]}"
        return "OFFHOOK"

    def _get_call_audio_route(self):
        """读取当前通话通信路由（headset/headphone/speaker 等）"""
        res = self._adb(["shell", "dumpsys", "audio"], timeout=8)
        if not res or res.returncode != 0:
            return "unknown"

        m = re.search(r"Active communication device:\s*AudioDeviceAttributes:.*?type:([a-z_]+)", res.stdout or "")
        if m:
            return m.group(1)
        return "unknown"

    def dial(self):
        print(f"\n[Dial] 📱 Dialing {self.phone_number}...")
        if not self._ensure_device_ready():
            return False

        call_cmd = ["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{self.phone_number}"]
        call_res = self._adb(call_cmd, timeout=8)
        if not call_res or call_res.returncode != 0:
            print(f"  ❌ Dial command failed: {(call_res.stderr or '').strip() if call_res else 'unknown'}")
            return False

        print("  WAITING for ACTIVE state (timeout 35s)...")
        start = time.time()
        last_state = None
        first_offhook_at = None
        while time.time() - start < 35:
            state = self._get_precise_call_state()
            if state != last_state:
                elapsed = int(time.time() - start)
                print(f"  [{elapsed:02d}s] state => {state}")
                last_state = state

            if state.startswith("OFFHOOK") and first_offhook_at is None:
                first_offhook_at = time.time()

            if "ACTIVE" in state:
                print("  ✅ Call Connected!")
                return True

            # 兜底：部分 ROM 的 telecom 不会稳定给 ACTIVE，但 mCallState=2 持续存在时可视作已建立通话
            if state.startswith("OFFHOOK") and first_offhook_at and (time.time() - first_offhook_at) >= 6:
                if "DISCONNECTED" not in state:
                    print("  ⚠️ ACTIVE not found, fallback to OFFHOOK stable >= 6s as connected.")
                    return True
            time.sleep(1)

        print("  ❌ Call was not connected within timeout.")
        return False

    def hangup(self):
        print("\n[Exit] 📵 Hanging up...")
        self.is_active = False
        self.asr.stop()
        if self.tts:
            self.tts.stop()
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_ENDCALL"], capture_output=True)
        if self.stream:
            self.stream.close()
        self.audio.terminate()

    def run(self):
        if not self.prepare(): return
        if not self.dial(): return

        route = self._get_call_audio_route()
        print(f"[AudioRoute] active communication route: {route}")
        if route == "headphone":
            print("[AudioRoute] ⚠️ 当前是 headphone(仅输出) 而非 headset(带麦)。对端通常听不到本机注入音频。")
            print("[AudioRoute] ⚠️ 请更换支持麦克风的 CTIA TRRS 转接头/线材，或改用蓝牙 HFP。")
            if STRICT_AUDIO_ROUTE:
                print("[AudioRoute] ❌ STRICT_AUDIO_ROUTE=1，已阻止本次外呼以避免无效通话。")
                self.hangup()
                return
            print("[AudioRoute] ⚠️ STRICT_AUDIO_ROUTE=0，继续执行（仅用于临时排障）。")
        
        self.is_active = True
        self.asr.start()
        
        try:
            while self.is_active:
                # 检查通话是否存活
                state = self._get_precise_call_state()
                if state == "IDLE":
                    print("\n[System] Call ended by remote.")
                    break
                time.sleep(3)
        except KeyboardInterrupt:
            print("\n[System] Interrupted.")
        finally:
            self.hangup()

if __name__ == "__main__":
    number = input("Enter phone number: ").strip()
    if number:
        caller = AIPhoneCaller(number)
        caller.run()
