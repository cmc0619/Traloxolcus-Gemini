FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for pg_config if needed)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8080

# Run
CMD ["uvicorn", "soccer_platform.main:app", "--host", "0.0.0.0", "--port", "8080"]
