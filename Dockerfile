FROM python:3.9-slim

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

RUN wget https://github.com/Kitware/CMake/releases/download/v3.27.7/cmake-3.27.7-linux-x86_64.sh \
    && chmod +x cmake-3.27.7-linux-x86_64.sh \
    && ./cmake-3.27.7-linux-x86_64.sh --skip-license --prefix=/usr/local \
    && rm cmake-3.27.7-linux-x86_64.sh

WORKDIR /app
COPY . .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
