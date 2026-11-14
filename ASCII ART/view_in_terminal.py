#!/usr/bin/env python3
"""
Prints Jezali's TrueColor Terminal Face Art (De-fringed & blended to site background)
Run: python "ASCII ART/view_in_terminal.py"
"""
import sys
import os

if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

DIR = os.path.dirname(os.path.abspath(__file__))
ans_file = os.path.join(DIR, "face_truecolor.ans")

if os.path.exists(ans_file):
    print("\033[2J\033[H", end="")
    with open(ans_file, "r", encoding="utf-8") as f:
        print(f.read())
    print("\033[0m")
else:
    print(f"File not found: {ans_file}")
