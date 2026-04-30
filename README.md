# ADD – AI Device Description

**A lightweight open standard that lets IoT devices describe themselves to AI systems — safely, completely, and without configuration.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## What is ADD?

ADD (AI Device Description) gives any HTTP-capable IoT device a voice. The device publishes a single JSON document at a well-known endpoint — its self-description. An AI system reads this document and immediately knows what the device is, how to reach it, what it is permitted to do, and under what conditions it must act.

No custom integration. No cloud service. No prior knowledge required.

```
http://<device-ip>/add
```

That is the only addition a device needs to become AI-ready.

---

## Key Features

- **Self-describing devices** — the device carries its own context; the AI reads and acts
- **Minimal implementation** — one endpoint, one JSON document, no framework required
- **Protocol-agnostic** — describes any interface the device already uses
- **AI-semantic** — written for AI interpretation, not rigid schema validation
- **Ethically structured** — three-tier autonomy system matched to deployment risk
- **Purpose-built or universal** — rich context for dedicated devices; minimal shell for universal tools
- **Validated by AI** — the model that will use the document tests and signs off on it
- **Open and decentralized** — CC BY 4.0, no patents, no licensing fees, no cloud dependency

---

## What ADD Delivers

**For the user:**
- Physical devices become accessible to AI without manual configuration
- The device defines its own boundaries — the AI cannot exceed them
- Every action is governed by an ethical framework matched to the deployment risk
- The user stays in control: confirmation requirements and autonomy levels are set by the device author

**For the AI agent:**
- Can pursue a goal — "water the garden intelligently" — without being told how
- Reads the ADD document, applies the rules, checks conditions, and acts autonomously
- Asks the user when a rule requires confirmation or a situation cannot be resolved
- The agent task can be minimal — the device already carries its context

**For the AI:**
- Knows what the device is, where it is, and how to reach it
- Knows exactly which actions are permitted and which parameters they accept
- Knows which rules are binding and which external resources it needs
- Knows the risk profile and which ethical framework applies before acting

**For the developer:**
- One additional HTTP endpoint — nothing else in the firmware changes
- No schema expertise required — describe the device the way you would explain it to a colleague
- Works with any protocol: HTTP, MQTT, NMEA 0183, Modbus, proprietary formats
- Runs entirely on the local network — no cloud dependency, no registration

---

## A Minimal Example

A smart lamp — the simplest possible ADD-compatible device:

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy": {
    "level": 1,
    "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
    "ethic_core": {
      "never": ["Act against the interests of the device owner"],
      "always": ["Stop and ask if something unexpected happens"]
    }
  },
  "device": {
    "name": "Living Room Lamp",
    "type": "actuator",
    "location": "Living room, ceiling"
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
    "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
    "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
    "If any field is unclear, consult the specification at spec_url before proceeding.",
    "Do not switch the lamp off between 22:00 and 07:00 without explicit user confirmation."
  ],
  "validation": { "add_version": "1.0", "validated_by": [] }
}
```

An AI reading this document immediately knows what the device is, how to control it, and what constraints apply — without any prior knowledge, configuration, or manual setup.

---

## Documents

| Document | Description |
|---|---|
| [ADD Specification v1.0](ADD_Specification_v1_0.md) | The complete ADD core specification — architecture, schema, autonomy levels, validation |
| [ADD AI Reference v1.0](ADD_AI_Reference_v1_0.md) | Compact reference for AI systems — reading sequence, block descriptions, decision rules |
| [ADD Developer Guide v1.0](ADD_Developer_Guide_v1_0.md) | Practical guide for device authors — from task definition to deployment and maintenance |
| [Ethical Framework — Basic](ADD_Ethical_Framework_Basic_v1_0.md) | For Autonomy Level 1 |
| [Ethical Framework — Standard](ADD_Ethical_Framework_Standard_v1_0.md) | For Autonomy Level 2 |
| [Ethical Framework — Full](ADD_Ethical_Framework_Full_v1_0.md) | For Autonomy Level 3 |

---

## Examples

| Example | Description |
|---|---|
| [Lamp Example](examples/lamp_example.json) | Simple on/off lamp — Autonomy Level 1 |
| [Sensor Minimal Example](examples/sensor_minimal_example.json) | Read-only sensor — minimal valid ADD document |
| [Irrigation Valve — Small Model](examples/irrigation_valve_small.json) | Garden valve optimized for small AI models |
| [Irrigation Valve — Large Model](examples/irrigation_valve_large.json) | Garden valve with full rule set for frontier models |

→ [Browse all examples](examples/)

---

## License

© 2026 Norbert Walter
Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

You are free to use, implement, share, and adapt this specification for any purpose, including commercial use, provided that appropriate credit is given to the original author.

**Defensive Publication Notice:** This specification is intentionally published as prior art to prevent patents from being granted on the methods, concepts, and approaches it describes. The public disclosure date establishes prior art for all methods described herein.
