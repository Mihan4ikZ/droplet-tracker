import argparse
# Чтение аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser(description='Обработка видео с каплями')
    parser.add_argument('input_video', help='Путь к входному видеофайлу')
    parser.add_argument('output_video', help='Путь для сохранения обработанного видео')
    parser.add_argument('output_csv', help='Путь для сохранения CSV с результатами')
    parser.add_argument('--position-threshold', type=float, default=100.0, help='Максимальное расстояние между центрами капель (пиксели)')
    parser.add_argument('--area-ratio', type=float, default=0.10, help='Допустимое относительное изменение площади (например, 0.10 = 10%%)')
    parser.add_argument('--dim-ratio', type=float, default=0.10, help='Допустимое относительное изменение ширины/высоты')
    return parser.parse_args()