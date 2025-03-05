import PyInstaller.__main__
import sys
import os

# Путь к основному файлу приложения
script_path = os.path.abspath("mic_amplifier_gui.py")

# Настройки для PyInstaller
PyInstaller.__main__.run([
    script_path,
    '--name=Усилитель микрофона',
    '--onefile',
    '--noconsole',
    '--clean',
    '--add-data=requirements.txt;.',
    '--hidden-import=numpy',
    '--hidden-import=sounddevice',
    '--hidden-import=PySide6',
]) 