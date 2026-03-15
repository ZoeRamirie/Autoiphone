import os
import sys
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
import pyaudio

# ================= 阿里云百炼配置 =================
# 这里复用您刚才的通义千问 API KEY
dashscope.api_key = "sk-a7f14f9ea7b34373b8c4f72e013b651e"

import requests
from dashscope.audio.tts_v2 import VoiceEnrollmentService

# 全局忽略 Mac Python 环境下自带 SSL 根证书缺失的报错
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def upload_to_catbox(file_path):
    print(f"[系统] 正在准备您的声音母本...")
    try:
        url = "https://litterbox.catbox.moe/resources/internals/api.php"
        data = {'reqtype': 'fileupload', 'time': '1h'}
        with open(file_path, 'rb') as f:
            r = requests.post(url, data=data, files={'fileToUpload': f}, timeout=15)
        if r.status_code == 200 and r.text.startswith("https"):
            return r.text.strip()
    except Exception as e:
        print(f"上传声音母本失败: {e}")
    return None

def clone_and_speak(text_to_speak, prompt_audio_path="my_voice.wav"):
    """
    使用 CosyVoice 零样本声音克隆技术，将文字转化为指定音色的声音并实时播放
    """
    if not os.path.exists(prompt_audio_path):
        print(f"❌ 找不到原声音频文件: {prompt_audio_path}")
        print("请确认您刚刚是否成功运行了录音脚本！")
        return
        
    print(f"\n[系统] 正在准备使用您的音色朗读这句话: \n「{text_to_speak}」\n")

    # 1. 自动上传录音拿到公网直链
    prompt_url = upload_to_catbox(prompt_audio_path)
    if not prompt_url:
        print("❌ 无法获取临时语音链接，克隆中止。")
        return
        
    # 2. 调用百炼创建专属声音 ID
    print("[大模型] 正在百炼平台实时训练您的音色 (只需一瞬)...")
    service = VoiceEnrollmentService()
    try:
        # 给当前克隆生成一个随机前缀
        import uuid
        prefix = "user" + uuid.uuid4().hex[:6]
        voice_id = service.create_voice(
            target_model="cosyvoice-v1",
            prefix=prefix,
            url=prompt_url
        )
    except Exception as e:
        print(f"❌ 生成克隆声纹失败: {e}")
        print("请检查阿里云百炼的权限设置。")
        return

    # 3. 初始化实时播放器
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,  # CosyVoice 默认吐出 22050Hz 的高音质音频
                    output=True)

    # 语音回调类，用于边生成边播放（流式TTS）
    class Callback(dashscope.audio.tts_v2.ResultCallback):
        def on_open(self):
            print("[大模型] 🟢 云端克隆就绪，开始发音...")

        def on_complete(self):
            print("\n[大模型] 🔴 朗读完毕。")

        def on_error(self, message):
            print(f"\n❌ [网络错误]: {message}")

        def on_close(self):
            pass

        def on_event(self, message):
            # 将云端传来的每一块（chunk）音频直接推给喇叭
            if isinstance(message, bytes):
                stream.write(message)
                
    callback = Callback()

    # 初始化 CosyVoice 流式合成器
    # 填入刚刚生成的 voice_id
    synthesizer = SpeechSynthesizer(
        model="cosyvoice-v1",
        voice=voice_id,
        callback=callback
    )

    try:
        # 触发合成
        synthesizer.call(text=text_to_speak)
    except Exception as e:
        print(f"声音合成失败: {e}")
    finally:
        import time
        time.sleep(0.5)
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    test_text = "哈喽大家好，这句声音可不是我自己在说话，这是我刚刚给苹果电脑接上的一个大模型，它在一秒钟内学会了我的声音，正在代替我向你们推销呢！"
    file_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(file_dir, "my_voice.wav")
    
    print("=== Autoiphone 声音克隆 (TTS) 测试 ===")
    clone_and_speak(test_text, prompt_path)
