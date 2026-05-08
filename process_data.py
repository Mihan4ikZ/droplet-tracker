import cv2
import numpy as np
import pandas as pd
import sys
import argparse

# Функция для обработки каждого кадра
def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sizes = []  # Список хранения размеров капель
    positions = []  # Список хранения позиций капель

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 5:  # Фильтрация по площади
            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Рисуем прямоугольник вокруг капли
            cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            sizes.append((area, w, h))  # Сохранение площади и размеров
            positions.append((center_x, center_y))  # Сохранение позиции капли

    return gray, sizes, positions

# Чтение аргументов командной строки
parser = argparse.ArgumentParser(description='Обработка видео с каплями')
parser.add_argument('input_video', help='Путь к входному видеофайлу')
parser.add_argument('output_video', help='Путь для сохранения обработанного видео')
parser.add_argument('output_csv', help='Путь для сохранения CSV с результатами')
parser.add_argument('--position-threshold', type=float, default=100.0, help='Максимальное расстояние между центрами капель (пиксели)')
parser.add_argument('--area-ratio', type=float, default=0.10, help='Допустимое относительное изменение площади (например, 0.10 = 10%%)')
parser.add_argument('--dim-ratio', type=float, default=0.10, help='Допустимое относительное изменение ширины/высоты')

args = parser.parse_args()

video = args.input_video
result_video = args.output_video
results_csv = args.output_csv

position_threshold = args.position_threshold
size_threshold_area_ratio = args.area_ratio
size_threshold_dimension_ratio = args.dim_ratio

cap = cv2.VideoCapture(video)  # Захват видео из файла

# Проверка успешного открытия видеофайла
if not cap.isOpened():
    print("Ошибка: Не удалось открыть видеофайл.")
    sys.exit(1)

# Получение параметров исходного видео
fps = cap.get(cv2.CAP_PROP_FPS)  # Частота кадров
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Ширина
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Высота

# Создание объекта VideoWriter для сохранения обработанного видео
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Кодек
out = cv2.VideoWriter(result_video, fourcc, fps, (width, height))

# Список данных капель
data = []
previous_droplets = []
previous_time = None   # Для хранения времени предыдущего кадра

def is_same_droplet(new_droplet, previous_droplet):
    area_diff_ratio = abs(new_droplet[0] - previous_droplet[0]) / previous_droplet[0]
    width_diff_ratio = abs(new_droplet[1] - previous_droplet[1]) / previous_droplet[1]
    height_diff_ratio = abs(new_droplet[2] - previous_droplet[2]) / previous_droplet[2]
    
    position_distance = np.linalg.norm(np.array(new_droplet[3:]) - np.array(previous_droplet[3:]))
    
    return (area_diff_ratio < size_threshold_area_ratio and 
            width_diff_ratio < size_threshold_dimension_ratio and 
            height_diff_ratio < size_threshold_dimension_ratio and 
            position_distance < position_threshold)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0   # Текущее время в секундах
    
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
                # Проверяем размеры через is_same_droplet
                # Вектор новой капли: (area, width, height, x, y)
                new_vec = (curr[2], curr[3], curr[4], curr[0], curr[1])
                prev_vec = (prev[2], prev[3], prev[4], prev[0], prev[1])
                if is_same_droplet(new_vec, prev_vec):
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

    # Отображаем обработанный кадр
    #out.write(processed_frame)   # Записываем обработанный кадр в выходной файл
    #cv2.imshow('Water Droplets Detection', processed_frame)

    # Задержка для замедления воспроизведения (например, на основе частоты кадров)
    #delay = int(1000 / fps)   # Задержка на основе частоты кадров

    # Выход при нажатии клавиши 'q'
    #if cv2.waitKey(delay) & 0xFF == ord('q'):
        #break

# Освобождаем ресурсы
cap.release()
out.release()

# Запись в файл с добавлением угла разлета и скорости капель
df_all_droplets = pd.DataFrame(data)
df_all_droplets.to_csv(results_csv, index=False)

#cv2.destroyAllWindows()