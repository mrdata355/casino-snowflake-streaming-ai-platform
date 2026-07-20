FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn snowflake-connector-python cryptography pydantic PyJWT[crypto]

COPY services ./services
RUN chown -R app:app /app
USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "services.feature_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
