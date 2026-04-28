# Droplet Tracker

Обработка видео с каплями воды (распознавание, отслеживание, определение скорости и угла движения).

## Docker: сборка образа и запуск
```bash
docker build -t droplet-tracker .

docker run --rm -v E:\\путь_к\\папке\\с_видео:/app/data droplet-tracker /app/data/input.mp4 /app/data/output.avi /app/data/results.csv --position-threshold 100 --area-ratio 0.10 --dim-ratio 0.10
```
### Параметры

| Параметр | Значение по умолчанию | Описание |
|----------|----------------------|-----------|
| `--position-threshold` | 100 | Максимальное расстояние между центрами капель (пиксели) |
| `--area-ratio` | 0.10 | Допустимое изменение площади (0.10 = 10%) |
| `--dim-ratio` | 0.10 | Допустимое изменение размеров (0.10 = 10%) |