import json
import uuid
import time
import threading
import websocket
import ssl
import sys
import requests
import hmac
import hashlib
import base64
import datetime
import urllib.parse
from core.event_bus import bus

class AliyunASREngine:
    """
    封装阿里云 ASR 识别引擎，支持基于 AK/SK 自动获取 Token
    """
    def __init__(self, appkey, token=None, access_key_id=None, access_key_secret=None):
        self.appkey = appkey
        self.token = token
        self.ak_id = access_key_id
        self.ak_secret = access_key_secret
        self.url_base = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
        self.ws = None
        self.is_active = False
        self.task_id = None
        self._should_reconnect = False
        self._reconnect_delay = 5

    def _get_token(self):
        """使用 AK/SK 手动签名获取最新的 Token (不依赖阿里云 SDK)"""
        if not self.ak_id or not self.ak_secret:
            return self.token
            
        print("[ASR] 🔑 Fetching fresh token via OpenAPI (Direct)...")
        try:
            # 阿里云 RPC 签名逻辑
            params = {
                'AccessKeyId': self.ak_id,
                'Action': 'CreateToken',
                'Format': 'JSON',
                'RegionId': 'cn-shanghai',
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureNonce': str(uuid.uuid4()),
                'SignatureVersion': '1.0',
                'Timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'Version': '2019-02-28'
            }
            
            # 1. 按照参数名排序
            sorted_params = sorted(params.items())
            # 2. 构造规范化查询字符串
            query_string = urllib.parse.urlencode(sorted_params)
            # 3. 构造待签名字符串
            string_to_sign = 'POST&%2F&' + urllib.parse.quote(query_string, safe='')
            # 4. 计算 HMAC-SHA1 签名
            secret = self.ak_secret + '&'
            h = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
            signature = base64.b64encode(h.digest()).decode('utf-8')
            # 5. 添加签名到参数
            params['Signature'] = signature
            
            # 发送请求
            url = "http://nls-meta.cn-shanghai.aliyuncs.com"
            resp = requests.post(url, data=params, timeout=10)
            res_json = resp.json()
            
            new_token = res_json.get('Token', {}).get('Id')
            if new_token:
                self.token = new_token
                print(f"[ASR] ✅ Token updated successfully")
                return new_token
            else:
                print(f"[ASR] ❌ Token response error: {res_json}")
        except Exception as e:
            print(f"[ASR] ❌ Failed to fetch token: {e}")
        return self.token

    def start(self):
        """建立连接并启动 ASR"""
        self._should_reconnect = True
        self._connect()
        # 启动重连心跳线程
        threading.Thread(target=self._reconnect_monitor, daemon=True).start()

    def _connect(self):
        """执行具体的连接逻辑"""
        curr_token = self._get_token()
        url = f"{self.url_base}?token={curr_token}"
        self.task_id = uuid.uuid4().hex
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        threading.Thread(target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}), daemon=True).start()

    def _reconnect_monitor(self):
        """监控连接状态并自动重连"""
        while self._should_reconnect:
            time.sleep(self._reconnect_delay)
            if not self.is_active and self._should_reconnect:
                print(f"[ASR] 🔄 Attempting to reconnect...")
                self._connect()

    def stop(self):
        """停止 ASR"""
        self._should_reconnect = False
        self.is_active = False
        if self.ws:
            self.ws.close()

    def send_audio(self, pcm_data):
        """发送音频数据到后台"""
        if self.is_active and self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(pcm_data, opcode=websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f"[ASR] Send error: {e}")

    def _on_open(self, ws):
        print("[ASR] 🟢 Connection established")
        req = {
            "header": {
                "message_id": uuid.uuid4().hex,
                "task_id": self.task_id,
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription",
                "appkey": self.appkey
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
        bus.publish("asr_ready")

    def _on_message(self, ws, message):
        res = json.loads(message)
        name = res.get('header', {}).get('name')
        text = res.get('payload', {}).get('result', '')

        if name == 'TranscriptionResultChanged' and text:
            bus.publish("customer_speaking", text=text)
        elif name == 'SentenceEnd' and text:
            print(f"\n[ASR] Sentence complete: {text}")
            bus.publish("customer_sentence_end", text=text)

    def _on_error(self, ws, error):
        print(f"[ASR] 🔴 Network error: {error}")
        bus.publish("asr_error", error=str(error))

    def _on_close(self, ws, code, msg):
        print(f"[ASR] ⚪ Connection closed: {code} {msg}")
        self.is_active = False
        bus.publish("asr_closed")
