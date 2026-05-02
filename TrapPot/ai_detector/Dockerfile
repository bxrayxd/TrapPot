# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your model, encoder, and the detection script
COPY trappot_model.pkl .
COPY label_encoder.pkl .
COPY detector.py .

# Command to run the detector
CMD ["python", "detector.py"]
