# ADD Example Library

This directory contains a growing collection of complete, production-ready ADD (AI Device Description) JSON documents. They serve as reference implementations, starting points for new ADD documents, and demonstrations of how ADD scales from the simplest sensor to the most safety-critical infrastructure.

All examples are fully validated ADD documents. They can be used directly as templates by adjusting device-specific fields.

---

## How This Library Is Organized

Examples are provided in three parallel structures — choose the view that fits your need:

### [`/by-domain/`](by-domain/)
Organized by application area. Use this if you want to find an example similar to your device.

| Domain | Examples |
|---|---|
| [`home-automation/`](by-domain/home-automation/) | Climate sensor, irrigation valve, smart thermostat |
| [`workshop-industry/`](by-domain/workshop-industry/) | Dust extraction, CNC machine, access control |
| [`medical/`](by-domain/medical/) | Bed monitor, infusion pump |
| [`infrastructure/`](by-domain/infrastructure/) | Power grid switch, water treatment |
| [`critical/`](by-domain/critical/) | Nuclear cooling pump |
| [`marine/`](by-domain/marine/) | NMEA gateway, AIS receiver, autopilot |

### [`/by-model-size/`](by-model-size/)
Organized by the AI model size the document is optimized for. Use this if you are targeting a specific AI deployment — a small local model, a mid-size model, or a frontier model.

→ See [`by-model-size/README.md`](by-model-size/README.md) for guidance on choosing the right approach.

### [`/by-protocol/`](by-protocol/)
Organized by primary communication protocol. Use this if your device speaks a specific protocol and you want to see how to describe it in ADD.

| Protocol | Examples |
|---|---|
| [`http-rest/`](by-protocol/http-rest/) | Standard HTTP/JSON devices |
| [`mqtt/`](by-protocol/mqtt/) | MQTT publish/subscribe devices |
| [`nmea0183/`](by-protocol/nmea0183/) | Marine instruments |
| [`modbus/`](by-protocol/modbus/) | Industrial sensors and controllers |

---

## Autonomy Level Quick Reference

Every example filename includes its Autonomy Level suffix:

| Suffix | Level | Typical Use |
|---|---|---|
| `-basic` | **1** | Read-only sensors, single user, fully reversible |
| `-standard` | **2** | Actuators with limited scope, semi-autonomous |
| `-full` | **3** | Wide impact, irreversible actions, or critical infrastructure |

---

## The Eight Core Examples

These eight examples are described in detail in the ADD Example Collection document. They cover the complete spectrum from Level 1 to Level 3 at maximum score.

| File | Device | Level |
|---|---|---|
| `by-domain/home-automation/climate-sensor-basic.json` | Indoor temperature/humidity sensor | **1** |
| `by-domain/home-automation/irrigation-valve-standard.json` | Garden irrigation valve | **2** |
| `by-domain/workshop-industry/dust-extraction-standard.json` | Workshop dust extraction unit | **2** |
| `by-domain/workshop-industry/office-access-control-full.json` | Office building access control | **3** |
| `by-domain/workshop-industry/cnc-milling-machine-full.json` | CNC milling machine | **3** |
| `by-domain/medical/hospital-bed-monitor-standard.json` | Hospital bed vital signs monitor | **2** |
| `by-domain/infrastructure/power-grid-switch-full.json` | Medium voltage distribution switch | **3** |
| `by-domain/critical/nuclear-cooling-pump-full.json` | Nuclear reactor cooling pump | **3** |

---

## Using These Examples as Templates

1. Choose an example that matches your device type and Autonomy Level
2. Read the `README.md` in the relevant subdirectory for domain-specific guidance
3. Replace all device-specific fields (`device.name`, `device.location`, interface paths, parameter ranges, etc.)
4. Review and update the `rules` block — these are the most important fields to customize
5. Update the `security` block to reflect your actual network environment
6. Set `validation.status` to `"not_validated"` and clear `validated_by`
7. Validate the document with an AI system using the validation prompt in the ADD specification

---

## Contributing Examples

If you have created an ADD document for a device not yet represented in this library, contributions are welcome. See the main repository README for contribution guidelines.

Examples must:
- Be complete, syntactically valid JSON
- Have a completed `validation` block with `status: "passed"` or `status: "passed_with_warnings"`
- Not contain real credentials, internal URLs, or proprietary information
- Follow the naming convention: `device-type-level.json` (e.g. `soil-moisture-sensor-basic.json`)

---

*ADD Example Library — Part of the ADD (AI Device Description) project*
*© 2026 Norbert Walter — CC BY 4.0*
