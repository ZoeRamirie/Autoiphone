import os
import sys
import uuid
import time
import asyncio
import threading
import ssl
import subprocess
import requests
import pyaudio

# 全局忽略 Mac 环境下自带 SSL 根证书缺失的报错
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where()

ssl._create_default_https_context = ssl._create_unverified_context
import websocket
websocket.setdefaulttimeout(15)
# 强制 websocket-client 忽略证书验证 (DashScope 使用该库)
os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = ""

# 尝试导入 CosyVoice 依赖
try:
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer, ResultCallback
    from dashscope.audio.tts_v2 import VoiceEnrollmentService
    HAS_DASH_SCOPE = True
except ImportError:
    HAS_DASH_SCOPE = False

class TTSEngineBase:
    """TTS 引擎基类约定接口，供 ai_caller 统一调用"""
    def __init__(self):
        self.is_speaking = False
        
    def prepare(self):
        """引擎初始化准备工作（例如注册声音、加载模型）"""
        pass
        
    def speak_streaming(self, text, playback_callback=None):
        """
        流式合成文本并立即播放
        :param text: 要朗读的一段文本（一般是从LLM流切分出的一句话）
        :param playback_callback: 当开始真正发出声音时的回调（用于打日志和计算首字节时间）
        """
        pass
        
    def stop(self):
        """打断正在进行的播放"""
        pass


class EdgeTTSEngine(TTSEngineBase):
    """
    备选方案：微软 Edge-TTS (用于没有阿里或声音克隆额度时降级使用)
    采用流式获取音频帧并播放架构，消除存文件的时间
    """
    def __init__(self, voice_id="zh-CN-YunxiNeural"):
        super().__init__()
        import edge_tts
        self.voice_id = voice_id
        self.edge_tts = edge_tts
        self._current_task = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    def prepare(self):
        print(f"  ✅ [Edge-TTS] 引擎已就绪，使用音色: {self.voice_id}")
        return True

    def speak_streaming(self, text, playback_callback=None):
        if not text.strip():
            return
            
        # 因 Edge-TTS 产出的是 mp3，pyaudio 无法直接硬解 mp3 流
        # 为了极速体验和避免库依赖，临时使用 afplay 播放，但去除存文件时间是不行的，mp3 需要完整文件
        # 所以在 Edge-TTS 我们依然采用写 /tmp 文件后播放，只作为降级方案
        # （要彻底流式建议用 ffmpeg 管道，这里保持简单，因为不是主推方案）
        import tempfile
        tmp_mp3 = f"/tmp/edge_tts_{uuid.uuid4().hex[:6]}.mp3"
        
        async def _save():
            comm = self.edge_tts.Communicate(text, self.voice_id)
            await comm.save(tmp_mp3)
            
        future = asyncio.run_coroutine_threadsafe(_save(), self._loop)
        try:
            future.result(timeout=10) # 挂起等待合成完成
        except Exception as e:
            print(f"  ❌ [Edge-TTS] 合成失败: {e}")
            return

        if os.path.exists(tmp_mp3):
            self.is_speaking = True
            if playback_callback:
                playback_callback()
            self._current_task = subprocess.Popen(["afplay", tmp_mp3])
            self._current_task.wait()
            self._current_task = None
            self.is_speaking = False
            try:
                os.remove(tmp_mp3)
            except:
                pass

    def stop(self):
        if self._current_task:
            try:
                self._current_task.kill()
            except:
                pass
        self.is_speaking = False


class CosyVoiceEngine(TTSEngineBase):
    """
    主打方案：阿里云百炼 CosyVoice-V1 零样本声音克隆流式引擎
    完美符合：听到即发丝级响应，支持 pcm 流边下边播
    """
    def __init__(self, api_key, prompt_audio_path):
        super().__init__()
        if not HAS_DASH_SCOPE:
            raise ImportError("请先安装 dashscope 库: pip install dashscope")
        
        dashscope.api_key = api_key
        self.prompt_audio_path = prompt_audio_path
        self.voice_id = None
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.synthesizer = None
        # 控制打断的标志
        self._abort = False

    def _upload_to_catbox(self):
        print(f"  [系统] 正在上传原声母本到稳定中转站 (uguu.se) 供百炼下载...")
        try:
            url = "https://uguu.se/upload.php"
            with open(self.prompt_audio_path, 'rb') as f:
                r = requests.post(url, files={'files[]': f}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get('success') and data.get('files'):
                    return data['files'][0]['url']
        except Exception as e:
            print(f"  ❌ 上传母本失败: {e}")
        return None

    def prepare(self):
        """执行一次性的声音复刻训练"""
        if not os.path.exists(self.prompt_audio_path):
            print(f"  ❌ [CosyVoice] 找不到原声音频文件: {self.prompt_audio_path}")
            return False

        prompt_url = self._upload_to_catbox()
        if not prompt_url:
            print("  ❌ [CosyVoice] 获取语音外链失败，无法初始化。")
            return False

        print("  [大模型] 正在百炼平台实时训练您的音色 (极速)...")
        service = VoiceEnrollmentService()
        try:
            prefix = "u" + uuid.uuid4().hex[:6]
            self.voice_id = service.create_voice(
                target_model="cosyvoice-v1",
                prefix=prefix,
                url=prompt_url
            )
            print(f"  ✅ [CosyVoice] 您专属的音色克隆模型已就绪 (ID: {self.voice_id})")
            return True
        except Exception as e:
            print(f"  ❌ [CosyVoice] 生成克隆声纹失败: {e}")
            return False

    def speak_streaming(self, text, playback_callback=None):
        if not self.voice_id or not text.strip() or self._abort:
            return

        self.is_speaking = True
        self._abort = False
        first_chunk_played = False
        
        # 准备扬声器推流器 (CosyVoice v1 默认返回 22050Hz, 16bit MONO pcm数据流)
        if self.stream is None or not self.stream.is_active():
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=22050, 
                output=True
            )

        class AudioCallback(ResultCallback):
            def __init__(self, engine_ref):
                self.engine = engine_ref
                
            def on_open(self):
                pass
                
            def on_complete(self):
                pass
                
            def on_error(self, message):
                print(f"\n  [CosyVoice 错误]: {message}")
                
            def on_close(self):
                pass
                
            def on_event(self, message):
                # 碰到用户打断，直接丢弃收到的网络包
                if self.engine._abort:
                    return
                # 将下发的 pcm 二进制音频块直接怼给喇叭，实现极速播放
                if isinstance(message, bytes) and len(message) > 0:
                    nonlocal first_chunk_played
                    if not first_chunk_played:
                        if playback_callback:
                            playback_callback()
                        first_chunk_played = True
                    try:
                        self.engine.stream.write(message)
                    except Exception as e:
                        print(f"  [流写入报错]: {e}")

        self.synthesizer = SpeechSynthesizer(
            model="cosyvoice-v1",
            voice=self.voice_id,
            callback=AudioCallback(self)
        )

        try:
            # 阻塞调用，但 callback 会在云端首包到达立刻异步触发播放
            self.synthesizer.call(text=text)
        except Exception as e:
            print(f"  ❌ [CosyVoice] 合成过程异常: {e}")
        finally:
            self.is_speaking = False

    def stop(self):
        self._abort = True
        self.is_speaking = False
        # 清空 pyaudio 里的残余声音
        if self.stream and not self.stream.is_stopped():
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except:
                pass


# ========== 开发独立测试桩 ==========
if __name__ == "__main__":
    print("=== TTS流式引擎独立测试 ===")
    
    # 模式选择
    test_mode = "edge" # or "cosy"
    
    if test_mode == "edge":
        engine = EdgeTTSEngine()
        engine.prepare()
        
        start_t = time.time()
        def on_first_audio():
            print(f"    [!] TTS首包延迟: {time.time() - start_t:.3f} 秒")
            
        print("[>] 喂入第一句话...")
        engine.speak_streaming("你好，我是Edge机器音，由于我缓存文件播放，延迟肯定有点高。", playback_callback=on_first_audio)
        
    elif test_mode == "cosy":
        api_key = "sk-a7f14f9ea7b34373b8c4f72e013b651e"
        audio_path = os.path.join(os.path.dirname(__file__), "my_voice.wav")
        engine = CosyVoiceEngine(api_key, audio_path)
        
        if engine.prepare():
            start_t = time.time()
            def on_first_audio():
                print(f"    [!] 哇！TTS首包延迟仅耗时: {time.time() - start_t:.3f} 秒！")
            
            print("[>] 喂入第一句文本...")
            engine.speak_streaming("你好，我是CosyVoice！你能感觉到我回话的速度非常快吗？", playback_callback=on_first_audio)
