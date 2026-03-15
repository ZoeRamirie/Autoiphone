import subprocess
import time
import sys
import re

def run_adb_command(command):
    """运行 ADB 命令并返回输出结果"""
    try:
        result = subprocess.run(
            ['adb'] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None

def check_device_connected():
    output = run_adb_command("devices")
    if not output: return False
    lines = output.split('\n')[1:]
    devices = [line.split('\t')[0] for line in lines if '\t' in line and line.strip()]
    return len(devices) > 0

def make_call(phone_number):
    print(f"\n[操作] 正在向手机发送拨打指令: {phone_number}")
    command = f"shell am start -a android.intent.action.CALL -d tel:{phone_number}"
    run_adb_command(command)

def end_call():
    print("[操作] 正在向手机发送系统挂断指令...")
    run_adb_command("shell input keyevent 6")

def get_call_state():
    """获取当前精准的通话状态"""
    registry = run_adb_command("shell dumpsys telephony.registry")
    if not registry: return "UNKNOWN"
    
    # mCallState 官方定义: 0=空闲, 1=响铃中, 2=摘机(拨号或通话中)
    match = re.search(r'mCallState=(\d+)', registry)
    if not match: return "UNKNOWN"
    
    state_code = match.group(1)
    if state_code == '0':
        return "IDLE (空闲/已挂断)"
    elif state_code == '1':
        return "RINGING (外来响铃)"
    elif state_code == '2':
        # 当摘机时，进一步读取 telecom 分析具体是 “在拨号” 还是 “已接听”
        telecom = run_adb_command("shell dumpsys telecom")
        if telecom:
            # 搜索系统底层的 State: 属性
            telecom_states = re.findall(r'State:\s*([A-Z_]+)', telecom)
            if telecom_states:
                valid_states = [s for s in telecom_states if s in ['DIALING', 'ACTIVE', 'DISCONNECTED']]
                if valid_states:
                    return f"OFFHOOK -> {valid_states[0]}"
        return "OFFHOOK (摘机/拨号中)"
    
    return "UNKNOWN"

def track_call(phone_number):
    make_call(phone_number)
    
    print(f"[{phone_number}] 开始通过信令追踪通话状态 (最长追踪 25 秒)...")
    start_time = time.time()
    last_state = None
    
    # 轮询状态
    while time.time() - start_time < 25:
        current_state = get_call_state()
        if current_state != last_state:
            print(f"  --> [{int(time.time() - start_time):02d}秒] 状态变更: {current_state}")
            last_state = current_state
            
            if "ACTIVE" in current_state:
                print("  >>> 【系统判定】对方已接听！(AI可在此刻开始播放语音)")
            elif "IDLE" in current_state and (time.time() - start_time > 2):
                print("  >>> 【系统判定】电话已挂断 (拒接/忙音/接通后挂断)。")
                break
                
        time.sleep(1) # 每隔 1 秒读取一次状态
        
    print(f"[{phone_number}] 追踪结束，发送系统挂断指令以防万一...")
    end_call()
    print("-" * 60)

if __name__ == "__main__":
    print("=== Autoiphone 连续批拨与强状态感知测试 ===")
    
    if not check_device_connected():
        print("未检测到设备。")
        sys.exit(1)
        
    # 如果没有传递命令行参数，使用用户指定的3个号码
    if len(sys.argv) > 1:
        numbers = sys.argv[1:]
    else:
        numbers = ["18903710501", "18803767777", "13164319000"]
    
    print(f"即将依次全自动拨打并实时追踪以下号码:")
    for i, num in enumerate(numbers):
        print(f"  {i+1}. {num}")
    print("\n")
    
    for num in numbers:
        track_call(num)
        print("休息 3 秒钟后开始下一通任务...\n")
        time.sleep(3)
        
    print("全部拨打轮播测试任务完毕！")
