import os
import sys
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
import requests
from dashscope.audio.tts_v2 import VoiceEnrollmentService
import uuid
import ssl
import subprocess

ssl._create_default_https_context = ssl._create_unverified_context
dashscope.api_key = "sk-a7f14f9ea7b34373b8c4f72e013b651e"

def upload_to_catbox(file_path):
    print("[系统] 正在上传您的声音母本...")
    url = "https://litterbox.catbox.moe/resources/internals/api.php"
    data = {'reqtype': 'fileupload', 'time': '1h'}
    with open(file_path, 'rb') as f:
        r = requests.post(url, data=data, files={'fileToUpload': f}, timeout=30)
    if r.status_code == 200 and r.text.startswith("https"):
        return r.text.strip()
    return None

def main():
    file_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(file_dir, "my_voice.wav")
    output_path = os.path.join(file_dir, "cloned_output.wav")
    
    text = "哈喽大家好，这句声音可不是我自己在说话，这是大模型在一秒钟内学会了我的声音。"
    
    if not os.path.exists(prompt_path):
        print("❌ 找不到 my_voice.wav")
        return
    
    # 1. 上传原声
    prompt_url = upload_to_catbox(prompt_path)
    if not prompt_url:
        print("❌ 上传失败")
        return
    print(f"[系统] 上传成功: {prompt_url}")
    
    # 2. 在百炼创建 voice_id
    print("[大模型] 正在训练您的音色...")
    service = VoiceEnrollmentService()
    prefix = "u" + uuid.uuid4().hex[:6]
    voice_id = service.create_voice(
        target_model="cosyvoice-v2",
        prefix=prefix,
        url=prompt_url
    )
    print(f"[大模型] 音色注册成功! voice_id = {voice_id}")
    
    # 3. 直接用同步模式合成，指定输出格式为 WAV
    print("[大模型] 🟢 正在合成您的声音...")
    synthesizer = SpeechSynthesizer(
        model="cosyvoice-v2",
        voice=voice_id,
        format=AudioFormat.WAV_22050HZ_MONO_16BIT
    )
    audio_data = synthesizer.call(text=text)
    
    if not audio_data or len(audio_data) == 0:
        print("❌ 没有收到任何音频数据！")
        return
    
    print(f"[系统] 成功收到 {len(audio_data)} 字节音频数据。")
    
    # 4. 直接保存为 WAV 文件（云端已经返回了完整的 WAV 格式，无需手动加头）
    with open(output_path, 'wb') as f:
        f.write(audio_data)
    
    print(f"[系统] 音频已保存至: {output_path}")
    
    # 5. 用 Mac 系统播放器播放
    print("[系统] 🔊 正在用系统播放器为您播放...")
    subprocess.run(["afplay", output_path])
    print("[系统] ✅ 播放结束！")

if __name__ == "__main__":
    print("=== Autoiphone 声音克隆 v2 (保存+播放) ===")
    main()
