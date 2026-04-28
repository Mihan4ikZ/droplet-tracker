# 1. Используем официальный легковесный образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 3. Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь код нашего приложения
COPY process_data.py .
# 5. Команда, которая будет выполнена при запуске контейнера
ENTRYPOINT ["python", "process_data.py"]