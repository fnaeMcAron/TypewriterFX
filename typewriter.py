
import os
import glob
import random
import threading
import select

import pygame
from evdev import InputDevice, list_devices, ecodes

BASE = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.path.join(BASE, "sounds")

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)

def load_sound(name):
    path = os.path.join(SOUNDS, name)
    if os.path.isfile(path):
        return pygame.mixer.Sound(path)
    return None

# Несколько вариантов звука обычной клавиши
key_files = glob.glob(os.path.join(SOUNDS, "key*.wav"))
key_sounds = [pygame.mixer.Sound(f) for f in key_files]

space_sound = load_sound("space.wav")
enter_sound = load_sound("enter.wav")
return_sound = load_sound("return.wav")
backspace_sound = load_sound("backspace.wav")

# Клавиши, которые должны издавать обычный звук
normal_keys = set()

for name in (
    [f"KEY_{c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    + [f"KEY_{c}" for c in "1234567890"]
    + [
        "KEY_MINUS", "KEY_EQUAL", "KEY_LEFTBRACE",
        "KEY_RIGHTBRACE", "KEY_BACKSLASH",
        "KEY_SEMICOLON", "KEY_APOSTROPHE",
        "KEY_GRAVE", "KEY_COMMA", "KEY_DOT",
        "KEY_SLASH"
    ]
):
    if hasattr(ecodes, name):
        normal_keys.add(getattr(ecodes, name))

def play(sound):
    if sound:
        sound.play()

def handle_keyboard(path):
    try:
        device = InputDevice(path)
        print("Клавиатура:", device.name)

        for event in device.read_loop():
            if event.type != ecodes.EV_KEY:
                continue

            # 0 = отпускание, 1 = нажатие, 2 = автоповтор
            if event.value not in (1, 2):
                continue

            code = event.code

            if code == ecodes.KEY_SPACE:
                play(space_sound)

            elif code == ecodes.KEY_ENTER:
                play(enter_sound)
                if return_sound:
                    threading.Timer(
                        0.4, play, args=(return_sound,)
                    ).start()

            elif code == ecodes.KEY_BACKSPACE:
                play(backspace_sound)

            elif code in normal_keys and key_sounds:
                play(random.choice(key_sounds))

    except Exception as e:
        print(f"Ошибка клавиатуры {path}: {e}")

def main():
    devices = []

    for path in list_devices():
        try:
            device = InputDevice(path)
            keys = device.capabilities().get(ecodes.EV_KEY, [])

            if ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys:
                devices.append(path)

        except Exception:
            pass

    if not devices:
        print("Клавиатуры не найдены или нет доступа к input.")
        return

    print("TypewriterFX запущен. Ctrl+C для выхода.")

    threads = []

    for path in devices:
        thread = threading.Thread(
            target=handle_keyboard,
            args=(path,),
            daemon=True
        )
        thread.start()
        threads.append(thread)

    try:
        while True:
            for thread in threads:
                thread.join(timeout=1)

    except KeyboardInterrupt:
        print("\nTypewriterFX остановлен.")

if __name__ == "__main__":
    main()
