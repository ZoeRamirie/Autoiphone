import collections
import threading

class EventBus:
    """
    极简事件总线，支持订阅和发布模式
    """
    def __init__(self):
        self._subscribers = collections.defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type, callback):
        """订阅事件"""
        with self._lock:
            self._subscribers[event_type].append(callback)

    def publish(self, event_type, **kwargs):
        """发布事件"""
        # print(f"[EventBus] Publish: {event_type} - {kwargs}")
        with self._lock:
            callbacks = self._subscribers.get(event_type, []).copy()
        
        for callback in callbacks:
            try:
                callback(**kwargs)
            except Exception as e:
                print(f"[EventBus] Callback error in {event_type}: {e}")

# 全局单例
bus = EventBus()
