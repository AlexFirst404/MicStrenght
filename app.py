import sounddevice as sd
import numpy as np
from threading import Lock
import sys

class MicrophoneAmplifier:
    def __init__(self):
        self.sample_rate = 48000
        self.channels = 2
        self.dtype = np.float32
        self.block_size = 4096  # Увеличиваем размер буфера
        self.gain = 5.0
        self.gain_lock = Lock()
        self.input_device = None
        self.output_device = None
        self.buffer = np.zeros((self.block_size, self.channels), dtype=self.dtype)
        
    def list_devices(self):
        """Показать все доступные аудио устройства"""
        print("\n=== Доступные аудио устройства ===")
        devices = sd.query_devices()
        input_devices = []
        output_devices = []
        
        print("\n--- Устройства ввода (микрофоны) ---")
        print("Формат: [номер] название (каналы, частота дискретизации)")
        print("-" * 60)
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                channels = min(device['max_input_channels'], 2)
                sample_rate = int(device['default_samplerate'])
                hostapi = sd.query_hostapis(device['hostapi'])['name']
                
                print(f"[{i}] {device['name']}")
                print(f"    Каналов: {channels}")
                print(f"    Частота: {sample_rate} Гц")
                print(f"    Драйвер: {hostapi}")
                print("-" * 60)
                
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': channels,
                    'default_samplerate': sample_rate,
                    'hostapi': hostapi
                })
        
        if not input_devices:
            print("Микрофоны не найдены!")
            print("-" * 60)
        
        print("\n--- Устройства вывода ---")
        print("Формат: [номер] название (каналы, частота дискретизации)")
        print("-" * 60)
        
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                channels = min(device['max_output_channels'], 2)
                sample_rate = int(device['default_samplerate'])
                hostapi = sd.query_hostapis(device['hostapi'])['name']
                
                print(f"[{i}] {device['name']}")
                print(f"    Каналов: {channels}")
                print(f"    Частота: {sample_rate} Гц")
                print(f"    Драйвер: {hostapi}")
                print("-" * 60)
                
                output_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': channels,
                    'default_samplerate': sample_rate,
                    'hostapi': hostapi
                })
        
        if not output_devices:
            print("Устройства вывода не найдены!")
            print("-" * 60)
        
        # Показываем текущие устройства по умолчанию
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        print("\n--- Устройства по умолчанию ---")
        print(f"Микрофон: [{default_input['index']}] {default_input['name']}")
        print(f"Динамики: [{default_output['index']}] {default_output['name']}")
        
        return input_devices, output_devices
    
    def select_devices(self, input_devices, output_devices):
        """Выбор устройств ввода и вывода"""
        while True:
            try:
                print("\nВыберите устройство ВВОДА (ваш микрофон):")
                input_id = int(input("Номер устройства > "))
                
                for device in input_devices:
                    if device['id'] == input_id:
                        self.input_device = device
                        break
                if not self.input_device:
                    print("Ошибка: Неверный номер устройства ввода")
                    continue
                
                print("\nВыберите устройство ВЫВОДА (виртуальный кабель):")
                print("Рекомендуется выбрать CABLE Input или похожее виртуальное устройство")
                output_id = int(input("Номер устройства > "))
                
                for device in output_devices:
                    if device['id'] == output_id:
                        self.output_device = device
                        break
                if not self.output_device:
                    print("Ошибка: Неверный номер устройства вывода")
                    continue
                
                # Устанавливаем фиксированные параметры для всех устройств
                self.sample_rate = 48000  # Стандартная частота дискретизации
                self.channels = 2  # Стерео
                self.block_size = 1024  # Уменьшенный размер буфера
                
                # Пробуем создать тестовый поток с WASAPI
                try:
                    # Получаем индексы WASAPI-устройств
                    devices = sd.query_devices()
                    wasapi_devices = []
                    
                    for i, device in enumerate(devices):
                        if device['hostapi'] == sd.query_hostapis().index('Windows WASAPI'):
                            wasapi_devices.append(i)
                    
                    # Находим WASAPI-эквиваленты выбранных устройств
                    wasapi_input = self.input_device['id']
                    wasapi_output = self.output_device['id']
                    
                    for dev_id in wasapi_devices:
                        device = devices[dev_id]
                        if device['name'] == self.input_device['name']:
                            wasapi_input = dev_id
                        if device['name'] == self.output_device['name']:
                            wasapi_output = dev_id
                    
                    # Создаем тестовый поток с WASAPI
                    test_stream = sd.Stream(
                        device=(wasapi_input, wasapi_output),
                        channels=self.channels,
                        samplerate=self.sample_rate,
                        dtype=self.dtype,
                        blocksize=self.block_size,
                        latency='low'
                    )
                    
                    # Если поток создался успешно, закрываем его
                    test_stream.close()
                    
                    # Сохраняем WASAPI-индексы
                    self.input_device['id'] = wasapi_input
                    self.output_device['id'] = wasapi_output
                    
                    print("\nУстройства успешно настроены через WASAPI")
                    return True
                    
                except Exception as e:
                    print(f"\nОшибка при использовании WASAPI: {str(e)}")
                    print("Пробуем стандартный режим...")
                    
                    try:
                        # Пробуем создать поток в стандартном режиме
                        test_stream = sd.Stream(
                            device=(self.input_device['id'], self.output_device['id']),
                            channels=self.channels,
                            samplerate=self.sample_rate,
                            dtype=self.dtype,
                            blocksize=self.block_size,
                            latency='high'  # Увеличиваем латентность для стабильности
                        )
                        test_stream.close()
                        print("\nУстройства настроены в стандартном режиме")
                        return True
                        
                    except Exception as e2:
                        print(f"\nОшибка: Устройства несовместимы")
                        print("Попробуйте другую комбинацию устройств")
                        print(f"Техническая информация: {str(e2)}")
                        self.input_device = None
                        self.output_device = None
                        continue
                
            except ValueError:
                print("Ошибка: Введите число")
            except Exception as e:
                print(f"Ошибка: {str(e)}")
                continue
    
    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            # Игнорируем ошибки буферизации при запуске
            if not 'priming output' in str(status):
                print(f"Ошибка: {status}")
        
        try:
            with self.gain_lock:
                # Копируем входные данные в промежуточный буфер
                self.buffer[:frames] = indata
                
                # Применяем усиление с мягким клиппингом
                amplified = self.buffer[:frames] * self.gain
                
                # Применяем мягкое ограничение для уменьшения искажений
                processed = np.tanh(amplified)
                
                # Нормализация для предотвращения перегрузки
                max_val = np.max(np.abs(processed))
                if max_val > 0.95:
                    processed *= 0.95 / max_val
                
                # Записываем в выходной буфер с плавным переходом
                outdata[:] = processed
                
        except Exception as e:
            print(f"Ошибка в обработке звука: {e}")
            outdata[:] = indata
    
    def run(self):
        try:
            print("\n=== Усилитель микрофона ===")
            print("ВАЖНО: Для работы требуется установить VB-CABLE Virtual Audio Device")
            print("Скачать можно здесь: https://vb-audio.com/Cable/")
            
            # Показываем доступные устройства
            input_devices, output_devices = self.list_devices()
            if not input_devices or not output_devices:
                print("Ошибка: Не найдены необходимые аудио устройства")
                return
            
            # Выбираем устройства
            if not self.select_devices(input_devices, output_devices):
                return
            
            print(f"\nНастройка завершена:")
            print(f"Вход: {self.input_device['name']}")
            print(f"Выход: {self.output_device['name']}")
            print(f"Каналов: {self.channels}")
            print(f"Частота дискретизации: {self.sample_rate} Гц")
            
            # Создаем поток аудио с оптимизированными настройками
            stream = sd.Stream(
                device=(self.input_device['id'], self.output_device['id']),
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=self.audio_callback,
                latency=0.2,  # Увеличиваем латентность для стабильности
                prime_output_buffers_using_stream_callback=False  # Отключаем предварительную буферизацию
            )
            
            print("\nУправление:")
            print("- Введите число больше 1 для изменения усиления")
            print("- Введите 'q' для выхода")
            print("- Введите 'r' для выбора других устройств")
            print(f"Текущее усиление: {self.gain}x\n")
            
            print("ВАЖНО: В настройках приложений выберите устройство вывода")
            print(f"'{self.output_device['name']}' как микрофон\n")
            
            # Запускаем поток
            with stream:
                while True:
                    user_input = input("Введите команду > ").lower()
                    
                    if user_input == 'q':
                        break
                    elif user_input == 'r':
                        print("\nПереключение устройств...")
                        stream.stop()
                        return self.run()
                    
                    try:
                        new_gain = float(user_input)
                        if new_gain > 0:
                            with self.gain_lock:
                                self.gain = new_gain
                            print(f"Усиление установлено на: {self.gain}x")
                            if new_gain > 10:
                                print("Внимание: Большое усиление может вызвать искажения!")
                        else:
                            print("Ошибка: коэффициент должен быть больше 0")
                    except ValueError:
                        if user_input not in ['q', 'r']:
                            print("Ошибка: введите число, 'q' для выхода или 'r' для смены устройств")

        except KeyboardInterrupt:
            print("\nПрограмма остановлена")
        except Exception as e:
            print(f"\nОшибка: {str(e)}")
        finally:
            print("\nУсилитель микрофона выключен")

def main():
    try:
        amplifier = MicrophoneAmplifier()
        amplifier.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()