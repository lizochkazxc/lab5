"""
Приложение видеозахвата — Вариант 4:
- Отображение видео с веб-камеры в реальном времени
- Фильтр "Оттенки серого"
- Сохранение снимка текущего кадра
- Захват и сохранение скриншота экрана
"""

import sys
import cv2
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from screenshot_utils import capture_screen, save_screenshot


class VideoCaptureApp(QMainWindow):
    """Главное окно приложения видеозахвата с фильтром оттенков серого."""

    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.current_frame = None  # Хранит последний обработанный кадр (BGR или Gray)

        self.setWindowTitle("Видеозахват — Вариант 4 (Фильтры и скриншоты)")
        self.resize(840, 660)

        self.init_ui()
        self.init_camera()

    def init_ui(self) -> None:
        """Инициализация графического интерфейса."""
        self.video_label = QLabel("Инициализация камеры...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(
            "background-color: #141414; color: #e0e0e0; border: 1px solid #333;"
        )

        self.status_label = QLabel("Статус: ожидание запуска")

        self.grayscale_checkbox = QCheckBox('Фильтр "Оттенки серого"')
        self.grayscale_checkbox.setChecked(False)

        self.frame_button = QPushButton("Сделать снимок кадра")
        self.frame_button.clicked.connect(self.capture_frame)

        self.screenshot_button = QPushButton("Сделать скриншот экрана")
        self.screenshot_button.clicked.connect(self.take_screenshot)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.grayscale_checkbox)
        controls_layout.addStretch()
        controls_layout.addWidget(self.frame_button)
        controls_layout.addWidget(self.screenshot_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label, stretch=1)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def init_camera(self) -> None:
        """Открывает веб-камеру и запускает таймер захвата."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.frame_button.setEnabled(False)
            self.video_label.setText(
                f"Ошибка: камера с индексом {self.camera_index} не найдена или недоступна"
            )
            self.status_label.setText("Статус: камера недоступна (доступен скриншот экрана)")
            return

        self.frame_button.setEnabled(True)
        self.status_label.setText(f"Статус: съёмка с камеры #{self.camera_index}")
        self.timer.start(30)  # ~33 FPS

    def apply_filter(self, frame):
        """Применяет выбранный фильтр к кадру."""
        if self.grayscale_checkbox.isChecked():
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

    def update_frame(self) -> None:
        """Читает кадр с камеры, применяет фильтр и обновляет QLabel."""
        if not hasattr(self, "cap") or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.timer.stop()
            self.frame_button.setEnabled(False)
            self.video_label.setText("Ошибка чтения кадра с камеры")
            self.status_label.setText("Статус: сбой потока видео")
            return

        processed_frame = self.apply_filter(frame)
        self.current_frame = processed_frame

        if processed_frame.ndim == 2:
            # Одноканальное изображение (оттенки серого)
            h, w = processed_frame.shape
            bytes_per_line = w
            qimage = QImage(
                processed_frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_Grayscale8,
            ).copy()
        else:
            # Трехканальное изображение (BGR -> RGB)
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, _ = rgb_frame.shape
            bytes_per_line = 3 * w
            qimage = QImage(
                rgb_frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            ).copy()

        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def capture_frame(self) -> None:
        """Сохраняет текущий кадр с камеры в файл с таймстампом."""
        if self.current_frame is None:
            self.status_label.setText("Статус: нет доступного кадра для сохранения")
            return

        try:
            saved_path = save_screenshot(self.current_frame, prefix="frame")
            self.status_label.setText(f"Кадр сохранён: {saved_path}")
            print(f"Кадр сохранён: {saved_path}")
        except Exception as exc:
            self.status_label.setText(f"Ошибка сохранения кадра: {exc}")
            print(f"Ошибка сохранения кадра: {exc}")

    def take_screenshot(self) -> None:
        """Делает скриншот экрана и сохраняет его с таймстампом."""
        try:
            screen_bgr = capture_screen(monitor_index=1)
            saved_path = save_screenshot(screen_bgr, prefix="screenshot")
            self.status_label.setText(f"Скриншот сохранён: {saved_path}")
            print(f"Скриншот сохранён: {saved_path}")
        except Exception as exc:
            self.status_label.setText(f"Ошибка скриншота: {exc}")
            print(f"Ошибка скриншота: {exc}")

    def closeEvent(self, event) -> None:
        """Останавливает таймер и корректно освобождает камеру при закрытии окна."""
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "cap") and self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.current_frame = None
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = VideoCaptureApp(camera_index=0)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()