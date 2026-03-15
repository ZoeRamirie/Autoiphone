import speech_recognition as sr
import time
import sys

def main():
    print("=== Autoiphone ASR (实时语音转文字) 模块预研测试 ===")
    
    # 实例化语音识别器
    r = sr.Recognizer()
    
    # 设置动态能量阈值（用于自动 VAD 截断判断什么时候开始说话，什么时候结束）
    r.dynamic_energy_threshold = True
    
    try:
        # 使用 Mac 默认的物理麦克风
        # 等音频线到了之后，这里可以直接切换为 "USB Audio Device"
        mic = sr.Microphone()
    except Exception as e:
        print(f"麦克风初始化失败: {e}")
        print("提示: 缺少底层音频库。Mac 可能需要先运行 'brew install portaudio'，然后再运行 'pip3 install pyaudio'。")
        sys.exit(1)

    print("\n[初始化] 正在采集环境底噪样本以校准麦克风...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1.5)
        print(f"[初始化] 校准完成，基准音量阈值为: {r.energy_threshold}")
        
        print("\n=======================================================")
        print("▶ 测试已就绪！")
        print("▶ 请直接对着您 Mac 的自带麦克风说话 (例如：喂，您好能听到吗)")
        print("▶ 按 Ctrl+C 可以退出测试程序")
        print("=======================================================\n")
        
        while True:
            try:
                print("[系统] 🟢 正在聆听中... (请说话 👇)")
                # listen 方法自带 VAD (语音活动检测)
                # 只要您说话，它就录音；您一停顿，它就自动截断并扔给大模型
                audio = r.listen(source, timeout=None, phrase_time_limit=15)
                
                print("[系统] 🟡 正在将语音发送至云端识别...")
                
                # 这里暂时使用内置的免费 Google 引擎演示一下流程，无需配置 API Key
                # 等正式对接时，只需把这一行替换成调用 阿里云/DeepSeek/微信的 接口即可
                text = r.recognize_google(audio, language="zh-CN")
                
                print(f"🗣️ 【您说的是】: {text}\n")
                
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                print("🗣️ 【系统提示】: (没检测到说话，或者声音太小未听清)\n")
            except sr.RequestError as e:
                print(f"⚠️ 网络请求错误 (可能需要科学上网环境): {e}\n")
            except KeyboardInterrupt:
                print("\n\n测试结束，已退出。")
                break

if __name__ == "__main__":
    main()
