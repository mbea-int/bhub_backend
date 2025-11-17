# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port for Gunicorn
EXPOSE 8000

# CMD: migrate + collectstatic + start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn business_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile -"]
