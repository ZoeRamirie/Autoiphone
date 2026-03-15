import time
from openai import OpenAI
from core.event_bus import bus

class LLMEngine:
    """
    封装 LLM 思考逻辑，订阅 ASR 事件并发布思考完成事件
    """
    def __init__(self, api_key, base_url, system_prompt):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.system_prompt = system_prompt
        self.conversation = [{"role": "system", "content": system_prompt}]
        self.is_thinking = False
        self._abort = False

    def think_and_reply(self, customer_text):
        """流式思考并发布结果"""
        self.is_thinking = True
        self._abort = False
        self.conversation.append({"role": "user", "content": customer_text})
        
        bus.publish("llm_think_start")
        
        try:
            response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=self.conversation,
                temperature=0.7,
                stream=True
            )
            
            punctuations = set(['。', '！', '？', '，', '；', ',', '!', '?'])
            collected_chunk = ""
            full_reply = ""
            
            for chunk in response:
                if self._abort or not chunk.choices:
                    break
                
                text = chunk.choices[0].delta.content or ""
                collected_chunk += text
                full_reply += text
                
                # 遇到标点即刻送播
                if any(p in text for p in punctuations):
                    fragment = collected_chunk.strip()
                    if fragment:
                        bus.publish("ai_text_chunk", text=fragment)
                        collected_chunk = ""
            
            # 补齐尾巴
            fragment = collected_chunk.strip()
            if fragment and not self._abort:
                bus.publish("ai_text_chunk", text=fragment)
                
            self.conversation.append({"role": "assistant", "content": full_reply})
            bus.publish("llm_think_end", full_text=full_reply)
                
        except Exception as e:
            print(f"[LLM] Error: {e}")
            bus.publish("llm_error", error=str(e))
        finally:
            self.is_thinking = False

    def abort(self):
        """中止当前的思考流程"""
        self._abort = True
