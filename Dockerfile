FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Let op: exact 1 worker. De spelstatus zit in het geheugen van het proces
# (plus 1 JSON-bestand), dus meerdere workers zouden elk een eigen staat krijgen.
# --threads 8 laat wel gelijktijdige polls van meerdere TV-schermen toe.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "app:app"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
