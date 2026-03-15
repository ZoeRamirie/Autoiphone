import math
import os
import struct
import time

import pyaudio


def main():
    device_index = int(os.getenv("TTS_OUTPUT_DEVICE_INDEX", "0"))
    channels = int(os.getenv("TTS_OUTPUT_CHANNELS", "2"))
    rate = int(os.getenv("PROBE_RATE", "22050"))
    seconds = float(os.getenv("PROBE_SECONDS", "6"))
    freq = float(os.getenv("PROBE_FREQ", "1000"))
    volume = float(os.getenv("PROBE_VOLUME", "0.85"))

    p = pyaudio.PyAudio()
    info = p.get_device_info_by_index(device_index)
    print(f"[Probe] output_device_index={device_index}, name={info.get('name')}, channels={channels}")
    print(f"[Probe] rate={rate}, seconds={seconds}, freq={freq}, volume={volume}")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        output=True,
        output_device_index=device_index,
    )

    frame_count = int(rate * seconds)
    chunk = 1024
    i = 0
    while i < frame_count:
        n = min(chunk, frame_count - i)
        buf = bytearray()
        for k in range(n):
            t = (i + k) / rate
            s = int(32767 * volume * math.sin(2 * math.pi * freq * t))
            frame = struct.pack("<h", s)
            if channels == 2:
                buf.extend(frame)
                buf.extend(frame)
            else:
                buf.extend(frame)
        stream.write(bytes(buf))
        i += n

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("[Probe] Done.")


if __name__ == "__main__":
    main()
