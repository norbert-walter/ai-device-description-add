FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Interne Ports des Containers:
# ADD_PORT     = 5005
# CONTROL_PORT = 4005
EXPOSE 5005 4005

# Nur EIN Worker, da Relay-State, ADD-Preset und Log
# gemeinsam im Prozessspeicher gehalten werden.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5005 --workers 1 --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-30} app:app"]
