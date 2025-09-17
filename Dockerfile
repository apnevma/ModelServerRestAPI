FROM python:3.12-slim

WORKDIR /app

# Copy project files, but exclude models/
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8086

# Start Flask API
CMD ["python", "RestAPI.py"]