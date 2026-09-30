# Start with lightweight official Python 3.11 image
FROM python:3.11-slim

# Create non-root user for container security
RUN useradd -m -u 1000 appuser

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first for layer caching optimization
COPY requirements.txt .

# Install dependencies with no-cache-dir to keep image size minimal
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8000 for incoming traffic
EXPOSE 8000

# Command to launch FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
