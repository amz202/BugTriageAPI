FROM python:3.11-slim

# Set environment variables to optimize Python output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /code

# Install system dependencies required for asyncpg and building packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application (including Alembic configs and ML artifacts)
COPY . .

# Expose the port Uvicorn runs on
EXPOSE 8000

# Run Uvicorn strictly with 1 worker to survive the 4GB RAM limit
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]