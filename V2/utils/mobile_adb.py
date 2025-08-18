import subprocess
import os
import time

def adb_screenshot(save_path="temp/mobile_screen.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cmd = f'adb exec-out screencap -p > "{save_path}"'
    result = subprocess.run(cmd, shell=True)
    time.sleep(0.4)
    return os.path.exists(save_path)

def adb_tap(x, y):
    cmd = f'adb shell input tap {int(x)} {int(y)}'
    subprocess.run(cmd, shell=True)
