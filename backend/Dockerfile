FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Configure environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV USE_MOCK_APIS=true
ENV DB_FILE=/data/articles_db.json

# Create data directory for persistence
RUN mkdir -p /data
VOLUME /data

# Expose API port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 