# flask_prediction_api/Dockerfile

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app and model files
COPY main.py ./
COPY models/ ./models/

# Expose port for Flask/Cloud Run
EXPOSE 8080

# Run the Flask app
CMD ["python", "main.py"]
