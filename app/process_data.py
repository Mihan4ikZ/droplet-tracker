import sys

import cv2
import numpy as np
import pandas as pd


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

    return (area_diff_ratio < area_ratio
            and width_diff_ratio < dim_ratio
            and height_diff_ratio < dim_ratio
            and position_distance < position_threshold)


def process_video(input_video, output_video, output_csv,
                  position_threshold=100.0, area_ratio=0.10, dim_ratio=0.10):
    """
    Открывает видео, покадрово обрабатывает, отслеживает капли
    и сохраняет результаты в CSV и видеофайл.
    """
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть видеофайл.")
        sys.exit(1)

    # Параметры исходного видео
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Создание VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Список данных капель
    data = []                 # список словарей для итогового CSV
    previous_droplets = []    # капли предыдущего кадра
    previous_time = None      # время предыдущего кадра

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        processed_frame, sizes, current_positions = process_frame(frame)

        # Формируем список текущих капель: (x, y, area, width, height)
        current_droplets = []
        for i in range(len(sizes)):
            area, w, h = sizes[i]
            x, y = current_positions[i]
            current_droplets.append((x, y, area, w, h))

        angles_deg = [None] * len(current_droplets)
        speeds = [None] * len(current_droplets)

        if previous_droplets and current_droplets:
            for i, curr in enumerate(current_droplets):
                best_match_idx = None
                best_distance = float('inf')
                # Перебираем все предыдущие капли
                for j, prev in enumerate(previous_droplets):
                    # Евклидово расстояние между центрами
                    pos_dist = np.linalg.norm(np.array(curr[:2]) - np.array(prev[:2]))
                    if pos_dist > position_threshold:
                        continue  # слишком далеко – не та капля
                    # Вектор для проверки is_same_droplet: (area, width, height, x, y)
                    new_vec = (curr[2], curr[3], curr[4], curr[0], curr[1])
                    prev_vec = (prev[2], prev[3], prev[4], prev[0], prev[1])
                    if is_same_droplet(new_vec, prev_vec, area_ratio, dim_ratio, position_threshold):
                        # Выбираем ближайшую по расстоянию среди подходящих
                        if pos_dist < best_distance:
                            best_distance = pos_dist
                            best_match_idx = j
                if best_match_idx is not None:
                    prev = previous_droplets[best_match_idx]
                    dx = curr[0] - prev[0]
                    dy = curr[1] - prev[1]
                    angle_rad = np.arctan2(dy, dx)
                    angles_deg[i] = np.degrees(angle_rad)
                    if previous_time is not None:
                        dt = current_time - previous_time
                        speeds[i] = np.sqrt(dx**2 + dy**2) / dt

        # Запись данных в список
        for i in range(len(sizes)):
            area, width_, height_ = sizes[i]
            center_x, center_y = current_positions[i]
            data.append({
                'Area': area,
                'Width': width_,
                'Height': height_,
                'Center X': center_x,
                'Center Y': center_y,
                'Angle': angles_deg[i],
                'Speed': speeds[i],
            })

        previous_droplets = current_droplets.copy()
        previous_time = current_time

        # Записываем обработанный кадр в выходной файл
        out.write(processed_frame)

    # Освобождение ресурсов
    cap.release()
    out.release()

    # Сохранение CSV
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
