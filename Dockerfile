FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System libraries that PDF/XML packages (xhtml2pdf, svglib, lxml) can need to build.
# If your build succeeds without this block, you can delete it for a smaller image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first so Docker caches this layer until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the app code
COPY . .

EXPOSE 8000

# API keys are NOT baked into the image; they're passed at runtime (see README / compose file).
# Render sets $PORT; locally it falls back to 8000.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
