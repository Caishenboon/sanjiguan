FROM python:3.12.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/packages/sanji-engine/src:/app
WORKDIR /app
RUN groupadd --system sanji && useradd --system --gid sanji --home-dir /app sanji
COPY apps/api/requirements.txt /tmp/requirements.txt
COPY packages/sanji-engine /app/packages/sanji-engine
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY apps /app/apps
COPY packages /app/packages
COPY scripts /app/scripts
COPY infra /app/infra
COPY knowledge /app/knowledge
COPY research-data /app/research-data
RUN chown -R sanji:sanji /app
USER sanji
EXPOSE 8000
CMD ["uvicorn", "apps.api.app.postgres_app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
