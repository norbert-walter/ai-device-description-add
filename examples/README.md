# ADD Example Library

A curated collection of ADD documents demonstrating the specification across device types, protocols, and deployment contexts. All examples are validated and ready to use as templates.

---

## Browse by Domain

Real-world device deployments organized by application area.

→ [by-domain/](by-domain/)

| Domain | Devices |
|---|---|
| Home automation | Irrigation valve, climate sensor |
| Workshop & industry | CNC machine, dust extraction, access control |
| Medical | Hospital bed monitor |
| Infrastructure | Power grid switch |
| Critical | Nuclear cooling pump |

---

## Browse by Protocol

ADD document examples for specific communication protocols.

→ [by-protocol/](by-protocol/)

| Protocol | Example device |
|---|---|
| HTTP REST | Climate sensor |
| MQTT | Smart home switch |
| Modbus TCP | Industrial energy meter |
| NMEA 0183 | Marine wind sensor |

---

## Browse by Model Size

The same device described for small, medium, and large AI models — showing how document complexity must match model capability.

→ [by-model-size/](by-model-size/)

| Model class | Example |
|---|---|
| Small (1B–13B) | Irrigation valve — simplified, ethic_core, 8 rules |
| Small (1B–13B) | Generic switch — minimal universal device, 2 actions |
| Medium (13B–70B) | Irrigation valve — ethic_url, doc_url, 12 rules |
| Large / Frontier | Irrigation valve — full rule set, 15 rules |
| Multi-model | Irrigation valve validated with 3 models — one fails |

---

## How to Use These Examples

- Use as templates — copy and adapt to your device
- Compare small vs. medium vs. large versions to understand simplification
- Read the `validation.summary` and `findings` fields to understand what was tested and what was found
- Check `improvements_applied` to see what changed during validation

For the complete guide to writing ADD documents, see the [ADD Developer Guide](../ADD_Developer_Guide_v1_0.md).
