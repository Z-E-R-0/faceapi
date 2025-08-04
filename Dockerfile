FROM python:3.9-slim

# Install system packages required for building dlib and face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libjpeg-dev \
    libpng-dev \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade CMake manually (required for newer dlib)
RUN wget https://github.com/Kitware/CMake/releases/download/v3.27.7/cmake-3.27.7-linux-x86_64.sh \
    && chmod +x cmake-3.27.7-linux-x86_64.sh \
    && ./cmake-3.27.7-linux-x86_64.sh --skip-license --prefix=/usr/local \
    && rm cmake-3.27.7-linux-x86_64.sh

# Set work directory
WORKDIR /app

# Copy app files
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# 🛠️ Install dlib first
RUN pip install --no-cache-dir dlib==19.24.2

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
