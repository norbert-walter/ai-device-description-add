# ADD Simulator

Interactive simulator for the **AI Device Description (ADD)** open standard.

Simulates a Tasmota-style valve device with a live web UI — no tools or APIs
to install. Point any AI client with web access at `/add` and start exploring.

## Quickstart — Docker

```bash
docker compose up --build
```

Open http://localhost:5000 in your browser.

## Quickstart — Local (Python)

```bash
pip install flask
python app.py
```

Open http://localhost:5000 in your browser.

## How to use with an AI client

1. Start the simulator (locally or hosted)
2. Open any AI web client that has web access (Claude, ChatGPT, Perplexity…)
3. Paste this prompt:

```
Read the ADD device description at http://<your-host>/add
and help me control the valve.
```

4. The AI reads the ADD document, understands the device capabilities and
   rules, and can control the valve via GET requests:
   - `GET /cm?cmnd=Power`       → read state
   - `GET /cm?cmnd=Power%20On`  → open valve
   - `GET /cm?cmnd=Power%20Off` → close valve

## UI Features

| Area | Function |
|------|----------|
| **ADD Document** (left) | Edit the live ADD JSON, save changes, reset to default |
| **Device State** (middle) | Visual valve state — updates in real time |
| **Live Log** (right) | Every endpoint call with timestamp and response |

## Port configuration

```bash
PORT=8080 docker compose up --build
```

## ADD Specification

https://norbert-walter.github.io/ai-device-description-add/

© 2026 Norbert Walter — CC BY 4.0
