"""
Утилиты для захвата и сохранения скриншотов экрана.
"""

from datetime import datetime
from pathlib import Path
import cv2
import mss
import numpy as np


def generate_timestamp_filename(prefix: str = "screenshot", ext: str = "png") -> str:
    """Генерирует уникальное имя файла с текущим таймстампом."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    clean_ext = ext.lstrip(".")
    return f"{prefix}_{timestamp}.{clean_ext}"


def capture_screen(monitor_index: int = 1) -> np.ndarray:
    """
    Захватывает экран и возвращает изображение в формате BGR (совместимом с OpenCV).
    """
    with mss.mss() as sct:
        monitors = sct.monitors
        target_monitor = monitors[monitor_index] if monitor_index < len(monitors) else monitors[0]
        raw_shot = sct.grab(target_monitor)
        bgra_img = np.asarray(raw_shot, dtype=np.uint8)
        return cv2.cvtColor(bgra_img, cv2.COLOR_BGRA2BGR)


def save_screenshot(
    frame: np.ndarray,
    prefix: str = "screenshot",
    output_dir: str | Path = ".",
) -> str:
    """Сохраняет изображение в файл с таймстампом и возвращает путь к нему."""
    if frame is None or frame.size == 0:
        raise ValueError("Передан пустой кадр для сохранения")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = generate_timestamp_filename(prefix=prefix, ext="png")
    filepath = str(target_dir / filename)

    if not cv2.imwrite(filepath, frame):
        raise IOError(f"Не удалось записать файл: {filepath}")

    return filepath