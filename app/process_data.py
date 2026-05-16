import cv2
import numpy as np


def process_frame(frame):
    """Обрабатывает один кадр: находит капли, возвращает изображение, размеры и позиции."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sizes = []
    positions = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 5:  # фильтрация по минимальной площади
            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2

            # Рисуем прямоугольник вокруг капли
            cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)

            sizes.append((area, w, h))
            positions.append((center_x, center_y))

    return gray, sizes, positions


def is_same_droplet(new_droplet, previous_droplet,
                    area_ratio=0.10, dim_ratio=0.10, position_threshold=100.0):
    """
    Проверяет, является ли new_droplet той же каплей, что и previous_droplet.

    Параметры:
    new_droplet, previous_droplet -- кортежи (area, width, height, x, y).
    area_ratio -- допустимое относительное изменение площади.
    dim_ratio -- допустимое относительное изменение ширины/высоты.
    position_threshold -- максимальное расстояние между центрами (пиксели).
    """
    area_diff_ratio = abs(new_droplet[0] - previous_droplet[0]) / previous_droplet[0]
    width_diff_ratio = abs(new_droplet[1] - previous_droplet[1]) / previous_droplet[1]
    height_diff_ratio = abs(new_droplet[2] - previous_droplet[2]) / previous_droplet[2]

    position_distance = np.linalg.norm(np.array(new_droplet[3:]) - np.array(previous_droplet[3:]))

    return (area_diff_ratio < area_ratio and
            width_diff_ratio < dim_ratio and
            height_diff_ratio < dim_ratio and
            position_distance < position_threshold)