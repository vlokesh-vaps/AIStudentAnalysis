FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8051 \
    FLASK_ENV=production \
    WORKERS=2 \
    THREADS=4

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8051

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8051'); prefix = os.getenv('APPLICATION_ROOT', os.getenv('URL_PREFIX', '')).strip('/'); path = f'/{prefix}/api/health' if prefix else '/api/health'; res = urllib.request.urlopen(f'http://127.0.0.1:{port}{path}'); exit(0 if res.getcode() == 200 else 1)" || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
