# Use an official Python runtime as a parent image
# you may also need to change dockerhub mirror to the ustc one in docker desktop settings by adding to daemon.json:
# { "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"] }
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set apt mirror; not needed if outside China
RUN sed -i 's|http://deb.debian.org/debian|https://mirrors.ustc.edu.cn/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|https://mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app
# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the ELSA package
RUN pip install .

# Change to the test directory
WORKDIR /app/test

# Make test.sh executable
RUN chmod +x test.sh

# Run tests when the container launches
CMD ["./test.sh"]
