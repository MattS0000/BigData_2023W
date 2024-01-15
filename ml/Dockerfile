FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY beam.py .
COPY gcc-key.json .
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/gcc-key.json"
CMD ["python", "-u", "beam.py"]