FROM python:3.12-slim

# рабочая директория
WORKDIR /app

# установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# скопировать код
COPY app.py .

# запуск uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
