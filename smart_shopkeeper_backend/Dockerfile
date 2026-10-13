FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

# Code lives in /code/app, so config.py resolves data/ and outputs/ to /code/data and /code/outputs
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY data ./data
COPY outputs/models ./outputs/models
# Run as a normal user; data/ and outputs/ are writable and meant to be mounted as volumes
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /code/data /code/outputs/charts /code/outputs/models \
    && chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]