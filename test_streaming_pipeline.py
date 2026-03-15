import os
import sys
import time
import ssl
from openai import OpenAI
from core.audio.tts_engine import CosyVoiceEngine, EdgeTTSEngine

ssl._create_default_https_context = ssl._create_unverified_context

LLM_API_KEY = "sk-a7f14f9ea7b34373b8c4f72e013b651e"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
llm_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

prompt_audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "audio", "my_voice.wav")
# engine = EdgeTTSEngine()
engine = CosyVoiceEngine(api_key=LLM_API_KEY, prompt_audio_path=prompt_audio_path)

print("\n=== 初始化 TTS 引擎 ===")
engine.prepare()

def run_pipeline(test_query):
    print(f"\n🗣️ 测试客户说: {test_query}")
    print("⏳ 记录开始时间...")
    start_t = time.time()
    first_audio_t = 0
    
    # 模拟一个标点切分的流式管道
    def on_playback_start():
        nonlocal first_audio_t
        first_audio_t = time.time()
        print(f"    🔊 [TTS首字节播放] => 距请求发出耗时: {first_audio_t - start_t:.3f} 秒 ⚡️🏆")

    print("🧠 [LLM 开始流式思考]...")
    response = llm_client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "你是一个销售，口语化回答，最多一句话20个字。"},
            {"role": "user", "content": test_query}
        ],
        temperature=0.7,
        stream=True
    )
    
    collected_chunk = ""
    # 标点切分集
    punctuations = set(['。', '！', '？', '，', '；', ',', '!', '?'])
    
    first_token_t = 0
    full_text = ""
    
    for chunk in response:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content or ""
        if not first_token_t and text:
            first_token_t = time.time()
            print(f"    💡 [LLM拉出首个Token]: {text}  => 耗时: {first_token_t - start_t:.3f} 秒")
        
        collected_chunk += text
        full_text += text
        
        if any(p in text for p in punctuations):
            # 遇到标点，切片拿去播放
            fragment = collected_chunk.strip()
            if fragment:
                print(f"    🚀 [切片推入TTS]: {fragment}")
                # 只有第一片触发回调打印耗时
                cb = on_playback_start if first_audio_t == 0 else None
                engine.speak_streaming(fragment, playback_callback=cb)
                collected_chunk = ""
                
    # 扫尾
    if collected_chunk.strip():
        print(f"    🚀 [末尾切片推入TTS]: {collected_chunk.strip()}")
        engine.speak_streaming(collected_chunk.strip())
        
    print(f"\n✅ AI 完整回复内容: {full_text}")
    print(f"⏱️ 管道总耗时 (含全部文字朗读完): {time.time() - start_t:.3f} 秒\n")

if __name__ == "__main__":
    print("========================================")
    print("🏎️ LLM Streaming + TTS Streaming 降延迟测试")
    print("========================================")
    run_pipeline("那你们这个系统贵不贵啊？")
    time.sleep(1)
    run_pipeline("太贵了买不起。")
