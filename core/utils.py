import time
import functools

def retry(msg="Retrying...", max_retries=3, delay=2):
    """
    通用重试装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    print(f"[Retry] {msg} ({retries}/{max_retries}) Error: {e}")
                    if retries < max_retries:
                        time.sleep(delay)
                    else:
                        raise e
        return wrapper
    return decorator
