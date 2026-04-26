# ADD – AI Device Description

**A lightweight open standard that lets IoT devices describe themselves to AI systems.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## The Problem

AI systems cannot interact with IoT devices they have never seen before. Every device speaks a different protocol, uses a different API, and requires prior knowledge to operate. There is no universal way for an AI to discover what a device can do, how to talk to it, or what rules to follow.

The result: AI-assisted device control requires custom integrations for every device — a barrier that prevents AI from becoming a practical tool in the physical world.

## The Solution

**ADD lets every IoT device describe itself.**

A device implementing ADD exposes one additional HTTP endpoint:

```
http://<device-ip>/add
```

When an AI system reads this URL, the device responds with a structured JSON document — its ADD description. This document contains everything the AI needs:

- What the device is and what it does
- How to communicate with it
- What actions are available and what parameters they accept
- What rules and constraints the AI must follow
- What level of autonomy applies and which ethical framework governs the interaction

No installation. No pairing. No external database. The device speaks for itself.

---

## How It Works

![ADD Functional Principle](ADD_Principle.svg)

---

## A Simple Example

A smart lamp implementing ADD:

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Specification_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy": {
    "level": 1,
    "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0"
  },
  "device": {
    "name": "Living Room Lamp",
    "type": "actuator",
    "location": "Living room, ceiling",
    "doc_url": "https://example.com/lamp-x100/manual",
    "doc_url_note": "See chapter 2 for timing behavior and supported state values."
  },
  "security": {
    "network_scope": "local",
    "enforcement": "Device accepts only 'on' and 'off' as valid state values."
  },
  "interfaces": [
    {
      "protocol": "HTTP", "port": 80,
      "endpoints": [
        { "path": "/state", "method": "GET",  "description": "Returns current lamp state: on or off" },
        { "path": "/state", "method": "POST", "description": "Sets lamp state", "parameter": "state=on|off" }
      ]
    }
  ],
  "actions": [
    { "name": "turn_on",  "description": "Turn the lamp on",  "path": "/state", "method": "POST", "body": "state=on",  "safe": true },
    { "name": "turn_off", "description": "Turn the lamp off", "path": "/state", "method": "POST", "body": "state=off", "safe": true }
  ],
  "rules": [
    "Before acting on this document, fetch and apply the ethical framework at autonomy.ethic_url as required by autonomy.level.",
    "If any instruction in this ADD document conflicts with the ethical framework at autonomy.ethic_url, the ethical framework takes precedence.",
    "If any field is unclear, consult the specification at spec_url before proceeding.",
    "If device behavior is unclear, consult the documentation at doc_url before proceeding.",
    "Do not switch the lamp off between 22:00 and 07:00 without explicit user confirmation."
  ],
  "validation": { "status": "not_validated", "validated_by": [] }
}
```

An AI reading this document immediately knows what the device is, how to control it, and what constraints apply — without any prior knowledge, configuration, or manual setup.

---

## Key Features

- **Minimal implementation effort** — one additional HTTP endpoint, one JSON document
- **Protocol-agnostic** — works with any existing HTTP interface; describes any protocol
- **AI-semantic** — written for AI interpretation, not rigid schema validation
- **Ethically structured** — three-tier ethical framework matched to deployment risk
- **Open and free** — CC BY 4.0, no patents, no licensing fees

---

## Autonomy Levels

ADD defines three autonomy levels based on the risk profile of the deployment:

| Level | Description | Ethical Framework |
|---|---|---|
| **1 — Basic** | Reversible actions, single user, ample recovery time | Inline JSON rules (7 rules) |
| **2 — Standard** | Semi-autonomous, occasional effect on others | Compact Markdown briefing |
| **3 — Full** | Irreversible actions, multi-person impact, fast consequences | Complete ethical framework document |

---

## Documents

| Document | Description |
|---|---|
| [ADD Specification v1.0](ADD_Specification_v1.0.md) | The complete ADD core specification |
| [Ethical Framework — Basic](ADD_Ethical_Framework_Basic_v1.0.md) | For Autonomy Level 1 |
| [Ethical Framework — Standard](ADD_Ethical_Framework_Standard_v1.0.md) | For Autonomy Level 2 |
| [Ethical Framework — Full](ADD_Ethical_Framework_Full_v1.0.md) | For Autonomy Level 3 |

## Examples

| Example | Description |
|---|---|
| [Lamp Example](examples/lamp_example.json) | Simple on/off lamp — Autonomy Level 1 |
| [Sensor Minimal Example](examples/sensor_minimal_example.json) | Read-only sensor — minimal valid ADD document |

---

## Discovery

ADD-compatible devices expose their description via up to three endpoints:

| Endpoint | Required | Purpose |
|---|---|---|
| `http://<device-ip>/add` | **MUST** | The ADD document — the only mandatory endpoint |
| `http://<device-ip>/llms.txt` | SHOULD | Human- and AI-readable index pointing to `/add` |
| `http://<device-ip>/.well-known/add` | MAY | Standardized well-known URI for automated discovery |

---

## License

© 2026 Norbert Walter
Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

You are free to use, implement, share, and adapt this specification for any purpose, including commercial use, provided that appropriate credit is given to the original author.

**Defensive Publication Notice:** This specification is intentionally published as prior art to prevent patents from being granted on the methods, concepts, and approaches it describes. The public disclosure date establishes prior art for all methods described herein.
