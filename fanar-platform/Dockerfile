# Fanar API — Phase 0 image.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src ./src
ENV PYTHONPATH=/app/src

EXPOSE 8000
# Runs the FastAPI app over HTTPS in prod (terminate TLS at the proxy or pass certs); dev shown here.
CMD ["uvicorn", "fanar.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
