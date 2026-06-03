FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libpango-1.0-0 libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY hub ./hub

RUN pip install --no-cache-dir .

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "hub.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
