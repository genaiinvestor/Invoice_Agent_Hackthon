# ==============================
# Base image
# ==============================
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside container
WORKDIR /app

# Install system dependencies (needed for PyMuPDF, PDFPlumber, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY Project/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY Project/ ./Project

# Set Streamlit environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_DISABLE_USAGE_STATS=true

# Expose Cloud Run port
EXPOSE 8080

# Run Streamlit app
CMD ["streamlit", "run", "Project/main.py", "--server.port=8080", "--server.address=0.0.0.0"]
