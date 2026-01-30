FROM python:3.12-slim

WORKDIR /app

# Copy only requirements first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application folders
COPY api/ /app/api/
COPY model_handlers/ /app/model_handlers/
COPY messaging/ /app/messaging/
COPY syncer/ /app/syncer/
COPY templates/ /app/templates/
COPY static/ /app/static/

# Copy root-level modules
COPY tf_serving_manager.py /app/
COPY utils.py /app/

EXPOSE 8086

# Start Flask API
CMD ["python", "-m", "api.rest_api"]