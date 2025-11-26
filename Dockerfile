FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Порт (Cloud Apps автоматически назначает через переменную PORT)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

# Запуск через gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} \
    --workers ${WORKERS:-2} \
    --threads ${THREADS:-4} \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app