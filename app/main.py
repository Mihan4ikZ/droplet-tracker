import cv2
import numpy as np
import pandas as pd
import sys
from cli import parse_args
from process_data import process_frame, is_same_droplet


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

        # Отображаем обработанный кадр
        #out.write(processed_frame)   # Записываем обработанный кадр в выходной файл
        #cv2.imshow('Water Droplets Detection', processed_frame)

        # Задержка для замедления воспроизведения (например, на основе частоты кадров)
        #delay = int(1000 / fps)   # Задержка на основе частоты кадров

        # Выход при нажатии клавиши 'q'
        #if cv2.waitKey(delay) & 0xFF == ord('q'):
            #break

    # Освобождение ресурсов
    cap.release()
    out.release()

    # Сохранение CSV
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)


def main():
    args = parse_args()
    process_video(
        input_video=args.input_video,
        output_video=args.output_video,
        output_csv=args.output_csv,
        position_threshold=args.position_threshold,
        area_ratio=args.area_ratio,
        dim_ratio=args.dim_ratio
    )

#cv2.destroyAllWindows()

if __name__ == '__main__':
    main()