# Examples by Protocol

ADD document examples organized by communication protocol. Each example demonstrates how ADD describes a specific protocol in plain language — without a formal schema, so the AI can interpret it semantically.

| Protocol | Examples |
|---|---|
| [http-rest](http-rest/) | Climate sensor — standard HTTP REST with JSON responses |
| [mqtt](mqtt/) | Smart home switch — MQTT topics, QoS, retained messages |
| [modbus](modbus/) | Industrial energy meter — Modbus TCP, register addressing, float conversion |
| [nmea0183](nmea0183/) | Marine wind sensor — NMEA 0183 sentences over TCP serial bridge |

ADD is protocol-agnostic. The `interfaces` block describes any protocol in plain language — the AI understands it without needing a formal schema or built-in protocol support.
