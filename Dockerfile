# Multi-stage Dockerfile for Enterprise Agentic Semantic Layer (EASL)
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r easl && useradd -r -g easl -d /app -s /sbin/nologin easl

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN chown -R easl:easl /app
USER easl

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

ENTRYPOINT ["easl"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
