FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Interne Ports des Containers:
# ADD_PORT     = 5002
# CONTROL_PORT = 4002
EXPOSE 5002 4002

# Nur EIN Worker, da Relay-State, ADD-Preset und Log
# gemeinsam im Prozessspeicher gehalten werden.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5002 --workers 1 --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-30} app:app"]
