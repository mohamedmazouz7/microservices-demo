FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

EXPOSE 8080
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
