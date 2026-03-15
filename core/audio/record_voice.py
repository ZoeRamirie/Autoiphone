import pyaudio
import wave
import sys
import time

def record_voice(output_filename="my_voice.wav", record_seconds=10):
    # 音频配置参数 (为阿里云 CosyVoice 优化的 16k 采样率, 单声道, 16bit)
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()

    print("\n" + "="*50)
    print("🎙️ 声音克隆母本录制工具")
    print("="*50)
    print("\n⚠️ 准备好了吗？")
    print("请找一段文字（随便什么都行，比如读一段新闻）。")
    print(f"我们将录制 {record_seconds} 秒的音频。")
    print("请尽量保持自然流利的说话语调，避免周围有太大的杂音。\n")
    
    input("👉 按下回车键 (Enter) 立即开始录音...")

    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"打开麦克风失败: {e}")
        sys.exit(1)

    print("\n🔴 正在录音中... 请开始说话！(倒计时)")

    frames = []

    # 循环读取音频流
    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        # 简单打印一下进度条
        progress = int((i / (RATE / CHUNK * record_seconds)) * 100)
        if progress % 10 == 0:
             print(f"\r⏳ 进度: {progress}% [{'=' * (progress // 5)}{' ' * (20 - progress // 5)}]", end="")

    print("\n\n✅ 录音结束！")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存为 WAV 格式
    try:
        wf = wave.open(output_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"\n🎉 完美！您的原声文件已保存至项目目录: {output_filename}")
        print("接下来我们就可以把它喂给 CosyVoice 大模型，让它用您的声音打电话了！\n")
    except Exception as e:
             print(f"保存文件失败: {e}")

if __name__ == "__main__":
    import os
    # 保存到当前运行目录下的 core/audio 文件夹中
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_voice.wav")
    record_voice(output_path, 30)
