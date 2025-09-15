# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and dlib
RUN apt-get update && apt-get install -y \\
    build-essential \\
    cmake \\
    libopencv-dev \\
    libgtk-3-dev \\
    libboost-all-dev \\
    libdlib-dev \\
    libopenblas-dev \\
    liblapack-dev \\
    libjpeg-dev \\
    libpng-dev \\
    libtiff-dev \\
    libavcodec-dev \\
    libavformat-dev \\
    libswscale-dev \\
    libv4l-dev \\
    libxvidcore-dev \\
    libx264-dev \\
    libfontconfig1-dev \\
    libcairo2-dev \\
    libgdk-pixbuf2.0-dev \\
    libpango1.0-dev \\
    libgtk2.0-dev \\
    libgtk-3-dev \\
    libatlas-base-dev \\
    gfortran \\
    wget \\
    unzip \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p data/faces data/encodings data/attendance logs models assets/images

# Expose the port Streamlit runs on
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
