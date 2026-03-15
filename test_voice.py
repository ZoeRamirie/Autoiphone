import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService
import os

dashscope.api_key = "sk-a7f14f9ea7b34373b8c4f72e013b651e"
service = VoiceEnrollmentService()

try:
    voice_id = service.create_voice(
        target_model="cosyvoice-v1",
        prefix="user",
        url="file://" + os.path.abspath("core/audio/my_voice.wav")
    )
    print("Voice ID:", voice_id)
except Exception as e:
    print("Error:", e)
