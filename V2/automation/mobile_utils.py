import os

def tap_mobile_screen(x, y, adb_path='adb'):
    os.system(f"{adb_path} shell input tap {int(x)} {int(y)}")
