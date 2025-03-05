import sounddevice as sd
import numpy as np
from threading import Lock

class MicrophoneAmplifier:
    def __init__(self):
        # Параметры аудио
        self.sample_rate = 44100  # Частота дискретизации
        self.channels = 1  # Моно
        self.dtype = np.float32  # Тип данных для аудио
        self.block_size = 1024  # Размер блока для обработки
        self.gain = 5.0  # Начальное значение усиления
        self.gain_lock = Lock()  # Для потокобезопасного изменения усиления
        
    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
        
        with self.gain_lock:
            # Применяем усиление
            outdata[:] = indata * self.gain
        
        # Ограничиваем значения для предотвращения искажений
        np.clip(outdata, -1, 1, out=outdata)
    
    def run(self):
        try:
            # Создаем поток аудио
            stream = sd.Stream(
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            
            print("\n=== Усилитель микрофона ===")
            print("Микрофон активирован! Управление:")
            print("- Введите число больше 1 для изменения усиления")
            print("- Введите 'q' для выхода")
            print(f"Текущее усиление: {self.gain}x\n")
            
            # Запускаем поток
            with stream:
                while True:
                    user_input = input("Введите коэффициент усиления > ")
                    
                    if user_input.lower() == 'q':
                        break
                        
                    try:
                        new_gain = float(user_input)
                        if new_gain > 0:
                            with self.gain_lock:
                                self.gain = new_gain
                            print(f"Усиление установлено на: {self.gain}x")
                        else:
                            print("Ошибка: коэффициент должен быть больше 0")
                    except ValueError:
                        print("Ошибка: введите число или 'q' для выхода")

        except KeyboardInterrupt:
            print("\nПрограмма остановлена")
        except Exception as e:
            print(f"\nОшибка: {str(e)}")
        finally:
            print("\nУсилитель микрофона выключен")

if __name__ == "__main__":
    amplifier = MicrophoneAmplifier()
    amplifier.run()