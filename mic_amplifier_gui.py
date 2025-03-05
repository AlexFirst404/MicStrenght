import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QComboBox, QLabel, QSlider, QPushButton,
                           QStyleFactory, QFrame, QLineEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
import sounddevice as sd
import numpy as np
from threading import Lock
import os

class CustomFrame(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #a935e8;")
        layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        layout.addLayout(self.content_layout)

class MicAmplifierGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Усилитель микрофона")
        self.setMinimumSize(600, 500)
        
        # Иконка приложения
        icon_path = os.path.join(os.path.dirname(__file__), "mic_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Инициализация аудио параметров
        self.sample_rate = 48000
        self.channels = 2
        self.dtype = np.float32
        self.block_size = 4096
        self.gain = 5.0
        self.gain_lock = Lock()
        self.buffer = np.zeros((self.block_size, self.channels), dtype=self.dtype)
        self.stream = None
        
        # Настройка темной темы
        self.setup_dark_theme()
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        title = QLabel("Усилитель микрофона")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #a935e8; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Секция выбора устройств
        devices_frame = CustomFrame("Настройка устройств")
        devices_layout = devices_frame.content_layout
        
        # Выбор входного устройства
        input_label = QLabel("Входное устройство (микрофон):")
        input_label.setStyleSheet("font-weight: bold;")
        self.input_combo = QComboBox()
        self.input_combo.setMinimumHeight(35)
        devices_layout.addWidget(input_label)
        devices_layout.addWidget(self.input_combo)
        devices_layout.addSpacing(10)
        
        # Выбор выходного устройства
        output_label = QLabel("Выходное устройство:")
        output_label.setStyleSheet("font-weight: bold;")
        self.output_combo = QComboBox()
        self.output_combo.setMinimumHeight(35)
        devices_layout.addWidget(output_label)
        devices_layout.addWidget(self.output_combo)
        
        layout.addWidget(devices_frame)
        
        # Секция управления усилением
        gain_frame = CustomFrame("Настройка усиления")
        gain_layout = gain_frame.content_layout
        
        gain_label = QLabel("Уровень усиления (0.0 - 20.0):")
        gain_label.setStyleSheet("font-weight: bold;")
        self.gain_input = QLineEdit()
        self.gain_input.setText("5.0")
        self.gain_input.setAlignment(Qt.AlignCenter)
        self.gain_input.setMinimumHeight(35)
        
        gain_layout.addWidget(gain_label)
        gain_layout.addWidget(self.gain_input)
        
        layout.addWidget(gain_frame)
        
        # Кнопки управления
        buttons_frame = CustomFrame("Управление")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.start_button = QPushButton("СТАРТ")
        self.stop_button = QPushButton("СТОП")
        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        
        buttons_frame.content_layout.addLayout(buttons_layout)
        layout.addWidget(buttons_frame)
        
        # Статус
        status_frame = CustomFrame("Статус")
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #a935e8;")
        status_frame.content_layout.addWidget(self.status_label)
        layout.addWidget(status_frame)
        
        # Подключение сигналов
        self.gain_input.textChanged.connect(self.update_gain)
        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        
        # Заполнение списков устройств
        self.refresh_devices()
        
    def setup_dark_theme(self):
        self.setStyle(QStyleFactory.create("Fusion"))
        
        dark_palette = QPalette()
        
        # Определение цветов
        dark_color = QColor(28, 28, 28)
        darker_color = QColor(35, 35, 35)
        disabled_color = QColor(127, 127, 127)
        text_color = QColor(255, 255, 255)
        highlight_color = QColor(142, 45, 197)
        alternate_base = QColor(60, 60, 60)
        
        # Применение цветов
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, darker_color)
        dark_palette.setColor(QPalette.AlternateBase, alternate_base)
        dark_palette.setColor(QPalette.ToolTipBase, text_color)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, highlight_color)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, text_color)
        
        self.setPalette(dark_palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1c;
            }
            QFrame {
                border: 2px solid #8e2dc5;
                border-radius: 10px;
                padding: 15px;
                background-color: #232323;
            }
            QPushButton {
                background-color: #8e2dc5;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #a935e8;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #7825a3;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QComboBox {
                border: 2px solid #8e2dc5;
                border-radius: 8px;
                padding: 5px 15px;
                background-color: #2d2d2d;
                color: white;
                min-width: 200px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #a935e8;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #8e2dc5;
                width: 8px;
                height: 8px;
                border-radius: 4px;
                background: #8e2dc5;
            }
            QLineEdit {
                border: 2px solid #8e2dc5;
                border-radius: 8px;
                padding: 8px 15px;
                background-color: #2d2d2d;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #a935e8;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
    
    def refresh_devices(self):
        # Получение списка устройств
        devices = sd.query_devices()
        
        self.input_combo.clear()
        self.output_combo.clear()
        
        # Заполнение списков устройств
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                self.input_combo.addItem(f"{device['name']}", i)
            if device['max_output_channels'] > 0:
                self.output_combo.addItem(f"{device['name']}", i)
    
    def update_gain(self):
        try:
            text = self.gain_input.text().replace(',', '.')  # Заменяем запятую на точку
            value = float(text)
            if value < 0:
                value = 0
            elif value > 20:
                value = 20
                self.gain_input.setText("20.0")
            
            with self.gain_lock:
                self.gain = value
                
        except ValueError:
            # Если введено некорректное значение, оставляем предыдущее
            with self.gain_lock:
                self.gain_input.setText(f"{self.gain:.1f}")
    
    def audio_callback(self, indata, outdata, frames, time, status):
        if status and not 'priming output' in str(status):
            self.status_label.setText(f"Ошибка: {status}")
        
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
                
                # Записываем в выходной буфер
                outdata[:] = processed
                
        except Exception as e:
            self.status_label.setText(f"Ошибка в обработке звука: {e}")
            outdata[:] = indata
    
    def start_stream(self):
        try:
            input_device = self.input_combo.currentData()
            output_device = self.output_combo.currentData()
            
            self.stream = sd.Stream(
                device=(input_device, output_device),
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=self.audio_callback,
                latency=0.2
            )
            
            self.stream.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.input_combo.setEnabled(False)
            self.output_combo.setEnabled(False)
            
            self.status_label.setText("Микрофон активен")
            
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
    
    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.input_combo.setEnabled(True)
            self.output_combo.setEnabled(True)
            
            self.status_label.setText("Готов к работе")
    
    def closeEvent(self, event):
        self.stop_stream()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MicAmplifierGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 