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
        self.setMinimumSize(400, 300)
        
        # Иконка приложения
        icon_path = os.path.join(os.path.dirname(__file__), "mic_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Инициализация аудио параметров
        self.sample_rate = 48000
        self.channels = 2
        self.dtype = np.float32
        self.block_size = 4096
        self.gain = 1.0
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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Выбор устройств
        devices_layout = QVBoxLayout()
        
        # Выбор входного устройства
        self.input_combo = QComboBox()
        self.input_combo.setPlaceholderText("Выберите микрофон")
        devices_layout.addWidget(self.input_combo)
        
        # Выбор выходного устройства
        self.output_combo = QComboBox()
        self.output_combo.setPlaceholderText("Выберите выход")
        devices_layout.addWidget(self.output_combo)
        
        layout.addLayout(devices_layout)
        
        # Слайдер усиления
        gain_layout = QVBoxLayout()
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setMinimum(0)
        self.gain_slider.setMaximum(100000)
        self.gain_slider.setValue(100)
        self.gain_slider.setTracking(True)
        
        self.gain_label = QLabel("Усиление: 1.0")
        self.gain_label.setAlignment(Qt.AlignCenter)
        
        gain_layout.addWidget(self.gain_label)
        gain_layout.addWidget(self.gain_slider)
        layout.addLayout(gain_layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("СТАРТ")
        self.stop_button = QPushButton("СТОП")
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        
        layout.addLayout(buttons_layout)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Подключение сигналов
        self.gain_slider.valueChanged.connect(self.update_gain)
        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        
        # Заполнение списков устройств
        self.refresh_devices()
        
    def setup_dark_theme(self):
        self.setStyle(QStyleFactory.create("Fusion"))
        
        dark_palette = QPalette()
        
        # Определение цветов
        dark_color = QColor(18, 18, 18)
        darker_color = QColor(25, 25, 25)
        text_color = QColor(255, 255, 255)
        accent_color = QColor(82, 82, 82)
        
        # Применение цветов
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, darker_color)
        dark_palette.setColor(QPalette.AlternateBase, darker_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.Highlight, accent_color)
        dark_palette.setColor(QPalette.HighlightedText, text_color)
        
        self.setPalette(dark_palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QPushButton {
                background-color: #525252;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #626262;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
            QPushButton:disabled {
                background-color: #323232;
                color: #666666;
            }
            QComboBox {
                border: 1px solid #525252;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #1a1a1a;
                color: white;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #626262;
            }
            QSlider::groove:horizontal {
                border: 1px solid #525252;
                height: 6px;
                background: #1a1a1a;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #525252;
                border: none;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #626262;
            }
            QLabel {
                color: white;
                font-size: 12px;
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
            value = self.gain_slider.value()
            with self.gain_lock:
                self.gain = value / 100.0  # Преобразуем значение слайдера в коэффициент усиления
                self.gain_label.setText(f"Усиление: {self.gain:.1f}")
                
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
    
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