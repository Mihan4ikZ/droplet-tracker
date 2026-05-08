# 1. Используем официальный легковесный образ Python
FROM python:3.13-slim AS build-base

# 2. Устанавливаем системные зависимости для сборки opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libopenblas-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libv4l-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Создаём виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 4. Устанавливаем рабочую директорию на время сборки
WORKDIR /app

# 5. Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем код из папки
COPY app/ .

# 7. Финальный образ
FROM python:3.13-slim

# 8. Устанавливаем только runtime-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libavcodec61 \
    libavformat61 \
    libavutil59 \
    libswscale8 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    libv4l-0 \
    && rm -rf /var/lib/apt/lists/*

# 9. Копируем виртуальное окружение из стадии build-base
COPY --from=build-base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 10. Устанавливаем рабочую директроию в финальном образе
WORKDIR /app

# 11. Копируем код приложения
COPY app/ .

# 12. Команда, которая будет выполнена при запуске контейнера
ENTRYPOINT ["python", "process_data.py"]