FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Interne Ports des Containers:
# ADD_PORT     = 5001
# CONTROL_PORT = 4001
EXPOSE 5001 4001

# Nur EIN Worker, da Relay-State, ADD-Preset und Log
# gemeinsam im Prozessspeicher gehalten werden.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5001 --workers 1 --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-30} app:app"]
