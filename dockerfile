FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]