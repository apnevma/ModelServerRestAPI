FROM python:3.12-slim

WORKDIR /app

# Copy only requirements first
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of project files, but exclude models/
COPY *.py ./

# Copy all models into the container
COPY /models /models

EXPOSE 8086

# Start Flask API
CMD ["python", "RestAPI.py"]