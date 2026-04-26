# ADD – AI Device Description
## Core Specification v1.0

---

## 1. Introduction

### 1.1 The Problem

The number of IoT devices in use today is vast and growing rapidly. Each device comes with its own interfaces, protocols, data formats, configuration options, and behavioral constraints. For a human operator, understanding and controlling an unfamiliar IoT device typically requires reading documentation, studying datasheets, and experimenting with the device manually.

Modern AI systems are increasingly capable of interacting with devices and services autonomously — reading sensor data, adjusting settings, diagnosing problems, and executing actions on behalf of a user. However, without a structured, machine-readable description of what a device is, what it can do, and how it should be interacted with safely, an AI system has no reliable basis for action. It cannot know which interfaces exist, which actions are permitted, which parameter ranges are valid, or which operations require user confirmation before execution.

Today, there is no established standard that provides AI systems with this information in a consistent, device-agnostic way. Device manufacturers provide web interfaces, REST APIs, and proprietary protocols — but none of these are designed to be read and acted upon autonomously by an AI.

### 1.2 The Solution: ADD

**ADD (AI Device Description)** addresses this gap. It is a lightweight, open specification that enables any HTTP-capable IoT device to publish a structured self-description — a machine-readable document that tells an AI system everything it needs to know to interact with the device correctly, safely, and usefully.

**The core idea is simple: the device describes itself.**

Just as a human expert would introduce an unfamiliar device by explaining what it does, how to read its data, what settings can be changed, and what precautions to take — an ADD document does exactly this, in a form that an AI can read and act upon directly. The device does not wait to be configured by an external system or rely on a central registry. It carries its own description and makes it available on demand.

The implementation is deliberately straightforward. Every ADD-compatible device exposes a single additional HTTP endpoint:

```
http://<device-ip>/add
```

When an AI system accesses this URL, the device responds with a JSON document — its ADD description. This document contains everything the AI needs: what the device is, how to communicate with it, what actions are available, what rules to follow, and whether the description has already been validated. No installation, no pairing process, no external database. The device speaks for itself.

This means that any microcontroller or embedded system capable of serving HTTP — an ESP8266, a Raspberry Pi, an Arduino with WiFi, or any modern IoT platform — can implement ADD with minimal effort. A device that already has a web interface or a REST API needs only one additional endpoint and one JSON document. The existing interfaces remain entirely unchanged.

ADD is not a new communication protocol. It does not replace existing interfaces such as HTTP, MQTT, NMEA, or Modbus. Instead, it sits alongside them as a **meta-description layer**: a document that describes what interfaces exist, what actions are possible, what constraints apply, and what rules the AI must follow.

The benefit is immediate: an AI system that encounters an ADD-compatible device for the first time can read its description, understand its purpose and capabilities, and begin interacting with it — without any prior knowledge of the device, without consulting external documentation, and without manual configuration by the user. The device and the AI are ready to work together from the moment they meet.

**Key principles of ADD implementation:**

- **No complex device logic required.** A simple, static JSON page served by the device's existing HTTP server is sufficient. There is no runtime computation, no dynamic negotiation, and no session handshake.
- **No new interfaces need to be created.** The AI uses the device's existing controls, endpoints, and communication mechanisms exactly as they are. ADD describes what is already there — it does not require anything new to be built.
- **The only addition is a single page.** Implementing ADD means adding one HTTP endpoint (`/add`) that returns one JSON document. Nothing else in the device's firmware or code needs to change.
- **No special or secured connection procedure.** There is no pairing process, no registration, no authentication handshake, and no external service involved in establishing the AI-device relationship. The AI simply reads the description and acts.
- **No human interaction required.** The ADD document is self-contained. An AI can discover, read, interpret, and act upon the description entirely autonomously — without asking the user to explain the device, without consulting external documentation, and without any manual setup steps.
- **The AI understands the device completely on its own.** This is the fundamental premise of ADD: a well-written ADD document gives an AI system everything it needs to understand a device's purpose, capabilities, constraints, and rules — independently and immediately.

**A first impression — a simple smart lamp:**

To make this concrete, consider the simplest possible ADD-compatible device: a smart lamp that can be switched on and off via HTTP. Without ADD, an AI system encountering this device would have no way of knowing what endpoints exist, what parameters they accept, or whether switching the lamp off at 2 AM is appropriate. With ADD, the device answers all of these questions itself:

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Specification_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy": {
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
        { "path": "/state", "method": "GET", "description": "Returns current lamp state: on or off" },
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

An AI system reading this document immediately knows: what the device is, how to read its current state, how to switch it on or off, and that it must ask before turning the lamp off at night. No manual configuration, no documentation lookup, no prior knowledge required. This is ADD in its simplest form — and the principle scales unchanged to devices of any complexity.

Note: The rules block above shows the four standard rules plus one device-specific rule. A complete list of recommended standard rules and their exact wording is provided in Section 4.6. A fully annotated minimal example including all standard rules is provided in Section 7.

### 1.3 Why a Core Schema?

For ADD to be useful across the full diversity of IoT devices, it must strike a careful balance: it must be structured enough that any AI system can parse and act on it reliably, yet flexible enough that it does not become an obstacle for device authors working with unusual protocols, domain-specific data formats, or constrained hardware.

ADD achieves this through a **minimal, stable core schema** — a small set of mandatory top-level blocks that every ADD document must contain, regardless of the device type. These blocks are not arbitrary: each one answers a specific question that an AI system must be able to answer before it can interact with a device safely and effectively:

| Block | Question answered |
|---|---|
| `autonomy` | *What level of autonomy does this deployment involve, and which ethical framework applies?* |
| `device` | *What is this device and what does it do?* |
| `security` | *In what environment does it operate, and who enforces safety?* |
| `interfaces` | *How can I communicate with it?* |
| `actions` | *What am I allowed to do, and with what parameters?* |
| `rules` | *What behavioral constraints must I follow as an AI?* |
| `validation` | *Has this description been verified to be AI-interpretable?* |

Without **autonomy context**, an AI cannot determine what ethical obligations apply before acting — and must refuse to proceed. Without **device identity**, an AI cannot understand the purpose and context of the device. Without **security context**, it cannot assess the risk of its actions or understand who is responsible for enforcement. Without **interface descriptions**, it cannot communicate with the device at all. Without **actions**, it does not know what operations are permitted and what constraints apply. Without **rules**, it lacks the behavioral guidance needed to act safely and correctly. Without **validation**, there is no basis for trust in the description itself.

These seven blocks form the irreducible minimum for an AI-usable device description. The `autonomy` block is always read first — it determines the ethical framework the AI must load before proceeding with any other block. See Section 11 for the full Autonomy Level definition and Section 12 for the Ethical Framework.

### 1.4 Design Philosophy

ADD follows the principle: **"Opinionated Core, Flexible Extensions."**

The top-level structure is fixed and stable. What lives inside each block is the responsibility of the device author, and can take any shape that is meaningful for the device in question. This design ensures that ADD can accommodate the full spectrum of IoT devices — from simple temperature sensors to complex marine navigation systems — without requiring a constantly evolving standard that tries to enumerate every possible protocol, interface type, or data format.

Modern AI systems are well-suited to this approach: they can interpret semantically rich but structurally diverse descriptions, identify intent from context, and apply judgment when details are ambiguous. ADD leverages this capability rather than working against it.

### 1.5 ADD and Existing Standards

ADD does not compete with established standards such as W3C Web of Things (WoT) or OpenAPI. It addresses a different problem, for a different audience, with a fundamentally different philosophy.

Standards like W3C WoT and OpenAPI solve the interoperability problem through **precision**: the more exactly and rigidly a device or API is described, the more reliably a machine can process that description. This approach is powerful, but it comes at a cost — the implementation burden is high. Device authors must learn complex schema languages, map their device's behavior onto prescribed data models, and ensure strict conformance at every level. For many IoT developers working with constrained hardware, niche protocols, or domain-specific data formats, this barrier is simply too high.

ADD solves the same problem through **semantics**: instead of demanding that the description be machine-precise, ADD delegates the interpretive work to the AI. A device author describes their device the way they would explain it to a technically competent colleague — in plain, structured language that conveys intent, context, and constraints. The AI understands it.

This is a genuine paradigm shift, and it is only possible because modern AI systems bring contextual understanding that classical parsers entirely lack. A developer implementing ADD does not need to look up whether their protocol is enumerated in the standard. They do not need to conform to a prescribed data model. They write what their device does — and the AI figures out the rest.

The practical effect is a dramatically lower barrier to entry. Any developer who can write JSON and describe their device in clear language can produce a valid ADD document. No schema expertise required, no external tooling, no conformance testing against a rigid vocabulary.

**ADD and W3C WoT / OpenAPI serve different goals:**

| | W3C WoT / OpenAPI | ADD |
|---|---|---|
| **Interoperability mechanism** | Schema precision | AI semantic interpretation |
| **Primary audience** | Systems integrators, platform vendors | Device authors, IoT developers |
| **Conformance model** | Strict validation | AI-readable, free-form sub-schemas |
| **Implementation effort** | High | Minimal |
| **Protocol coverage** | Defined and enumerated | Unlimited — any protocol can be described |

ADD is best understood as a complement to these standards, not a replacement. In environments where W3C WoT or OpenAPI are already deployed and working, ADD adds nothing. Where they are absent — because the device is too constrained, the protocol too niche, or the developer team too small — ADD provides a practical path to AI interoperability that would otherwise not exist.

**Why the AI validates its own description**

One consequence of ADD's semantic approach is that validation cannot be delegated to a generic schema checker. The only meaningful test of an ADD document is whether the AI that will actually use it can read, understand, and correctly act upon it. This is why ADD validation is performed by AI systems — not because it is more convenient, but because it is the only test that actually matters.

This has a practical implication that is easy to overlook: different AI systems interpret the same description differently. A large, capable model may successfully infer intent from a loosely worded action description; a smaller or more constrained model may fail on the same text. An ADD document that passes validation with one AI is not automatically valid for another.

For this reason, the `validation` block records not just the validation result, but the specific AI system — including model name and version — that performed the test. If an ADD document is intended for use with multiple AI systems, it SHOULD be validated separately with each one, and the results recorded accordingly. The device author bears final responsibility: they review the AI's validation findings, apply corrections, and release the document. The AI surfaces problems; the human judges whether the description is correct and complete for the intended use case.

### 1.6 Autonomy Levels and Ethical Framework

ADD is designed to support a wide range of deployment scenarios — from a simple sensor read by a small local model on demand, to a persistent AI agent autonomously managing an entire building's systems. These scenarios differ fundamentally in the risk they carry and in the ethical obligations they impose on the AI system acting upon them.

ADD addresses this through a structured **Autonomy Level** system. Every ADD document declares an Autonomy Level — 1, 2, or 3 — that reflects three factors: how reversible the device's actions are, how many people are affected, and how quickly errors become irreversible. The level is not a technical parameter — it is a risk characterization that determines which ethical framework the AI must apply before acting.

The three levels map to three tiers of ethical obligation:

- **Level 1 — Basic:** A compact inline rule set embedded directly in the ADD document. Appropriate for small models and narrow, low-risk tasks.
- **Level 2 — Standard:** A concise ethical framework summary, fetched from an external URL. Appropriate for semi-autonomous operation with moderate risk.
- **Level 3 — Full:** The complete ADD Ethical Framework document, mandatory before any autonomous action. Required for wide action spaces, irreversible actions, or multi-person impact.

The `autonomy` block in the top-level schema carries the level declaration, the three factor scores, the URL of the applicable ethical framework document, and the required ethic mode. An AI system reading an ADD document MUST read the `autonomy` block first and load the appropriate ethical framework before proceeding.

The Autonomy Level is declared by the device author and verified independently by the AI during validation. If the AI's assessment of the level differs from the declared value, it MUST report this and recommend the higher level. See Section 11 for the full definition, scoring method, and examples.

---

## 2. Design Principles

- **Minimal:** The specification defines only what is necessary. Complexity lives in the device, not in the protocol.
- **Flexible:** Sub-schemas are intentionally free-form. Device authors may use any field names, structures, and values that are semantically meaningful.
- **AI-readable:** The description is written for AI interpretation, not strict machine validation. Modern AI systems can interpret diverse schemas as long as the overall structure and semantics are clear.
- **Device-agnostic:** ADD applies to any HTTP-capable IoT device, regardless of domain (marine, home automation, industrial, etc.).
- **Stable:** The core schema must not change frequently. Flexibility in sub-schemas prevents the need for constant revision.
- **Self-referencing:** Every ADD document carries a link to the specification it is based on, enabling AI systems to resolve ambiguities by consulting the authoritative source.

---

## 3. Discovery

An AI system discovers the ADD description of a device by requesting a well-known resource from the device's HTTP server. ADD defines a single mandatory endpoint and two optional endpoints that improve discoverability. Device authors choose the level of discoverability that fits their device's capabilities and use case.

**Minimal requirement — one endpoint:**
Every ADD-compatible device MUST implement exactly one endpoint: `/add`. This is the only technical addition required to make a device ADD-compatible. Everything else is optional.

**Maximum discoverability — three endpoints:**
A device that implements all three discovery mechanisms offers the best possible AI discoverability: an AI system can find the ADD document regardless of which discovery method it uses first. This is recommended for devices intended for broad deployment or public use.

| Endpoint | Required | Purpose |
|---|---|---|
| `http://<device-ip>/add` | **MUST** | The ADD document itself — the only mandatory endpoint |
| `http://<device-ip>/llms.txt` | SHOULD | Human- and AI-readable index pointing to the ADD endpoint |
| `http://<device-ip>/.well-known/add` | MAY | Standard well-known URI for automated discovery by AI agents |

---

### 3.1 The ADD Endpoint (Mandatory)

The ADD description MUST be accessible at:

```
http://<device-ip>/add
```

This endpoint MUST return a valid JSON document conforming to the ADD core schema (see Section 4). It is the single mandatory addition required to make any HTTP-capable device ADD-compatible. A device that implements only this endpoint is fully ADD-conformant.

---

### 3.2 Discovery via `llms.txt` (Recommended)

Devices SHOULD additionally provide a `llms.txt` file at the root of their HTTP server:

```
http://<device-ip>/llms.txt
```

`llms.txt` is a lightweight, human- and AI-readable index of AI-relevant resources on a device or server. For ADD, it serves as a discoverable pointer to the ADD endpoint — useful for AI systems that scan for `llms.txt` as a first step before trying specific endpoints.

The file MUST contain a reference to the ADD endpoint:

```
# AI Device Description (ADD)
- ADD: [Device Description](/add)
```

Additional entries — documentation links, API references, changelog URLs — MAY be included but are not required. The `llms.txt` file does not replace the ADD endpoint; it points to it.

A device that implements both `/add` and `/llms.txt` covers the two most common AI discovery paths and is suitable for the majority of deployments.

---

### 3.3 Well-Known URI (Optional)

Devices MAY additionally expose the ADD document at the standardized well-known URI path:

```
http://<device-ip>/.well-known/add
```

The well-known URI convention (RFC 8615) allows AI agents and automated tools to probe a fixed, predictable location for machine-readable metadata without prior knowledge of the device's URL structure. Implementing this endpoint makes the ADD document discoverable by tools that follow the well-known convention — including future AI frameworks that may standardize on this path.

This endpoint MUST return the same valid ADD JSON document as `/add`. It MAY redirect to `/add` with an HTTP 301 or 302 response rather than duplicating the content.

A device that implements all three endpoints — `/add`, `/llms.txt`, and `/.well-known/add` — offers maximum discoverability and is recommended for devices intended for broad or public deployment.

---

### 3.4 Cache Control

The ADD endpoint SHOULD return the HTTP header:

```
Cache-Control: no-store
```

To ensure AI clients always receive a fresh description, device authors SHOULD support a cache-buster query parameter (e.g., `?t=<unix_timestamp>`). This SHOULD be noted in the device's ADD `rules` block.

---

### 3.5 Session Timeout

Devices with resource constraints MAY implement a session timeout mechanism. The ADD description SHOULD indicate the remaining session time and the maximum number of session extensions available.

---

## 4. Core Schema

An ADD document is a JSON object with the following mandatory top-level fields:

```json
{
  "schema": "add",
  "version": "<semver>",
  "spec_url": "<url>",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy": { ... },
  "device": { ... },
  "security": { ... },
  "interfaces": [ ... ],
  "actions": [ ... ],
  "rules": [ ... ],
  "validation": { ... }
}
```

### 4.1 Top-Level Fields

| Field          | Type    | Required | Description |
|----------------|---------|----------|-------------|
| `schema`       | string  | yes      | Must be `"add"` |
| `version`      | string  | yes      | ADD schema version (semver, e.g. `"1.0"`) |
| `spec_url`     | string  | yes      | URL of the authoritative ADD specification document for this version |
| `spec_license` | string  | recommended | License and attribution of the ADD specification (e.g. `"CC BY 4.0 — © 2026 Norbert Walter"`) |
| `autonomy`     | object  | yes      | Autonomy Level, factor scores, and link to the applicable ethical framework document (see Section 11) |
| `device`       | object  | yes      | Device identity and metadata (see Section 4.2) |
| `security`     | object  | yes      | Security context and enforcement policy (see Section 4.3) |
| `interfaces`   | array   | yes      | Available communication interfaces (see Section 4.4) |
| `actions`      | array   | yes      | Operations the AI may perform (see Section 4.5) |
| `rules`        | array   | yes      | Behavioral instructions for the AI (see Section 4.6) |
| `validation`   | object  | yes      | Result of the last AI-based validation (see Section 9) |

The `spec_license` field is not mandatory but strongly recommended. It ensures that the attribution required by the CC BY 4.0 license is embedded directly in every ADD document — making the origin of the specification self-evident to any AI system or human reader, without requiring them to follow the `spec_url` link.

**Purpose of `spec_url`:**

The `spec_url` field links the ADD document to the authoritative specification it is based on. This serves two purposes:

1. **Disambiguation:** If an AI system encounters an unknown field, an ambiguous instruction, or an unexpected structure, it SHOULD fetch the specification at `spec_url` and use it to resolve the ambiguity before proceeding.
2. **Version traceability:** The URL SHOULD point to the specific version of the specification used, not just the latest version, to ensure consistent interpretation over time.

The following rule SHOULD be included in every ADD document's `rules` block as a standard entry:

```
"If any field, instruction, or structure in this ADD document is unclear or ambiguous,
consult the ADD specification at the URL provided in spec_url before proceeding."
```

---

### 4.1 The `autonomy` Block

The `autonomy` block declares the risk profile of this deployment and links to the applicable ethical framework document. It is the first block an AI system reads — before any device description, interface, or action.

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | Autonomy Level: 1 (Basic), 2 (Standard), or 3 (Full) |
| `scores.reversibility` | integer | yes | 0 = fully reversible, 1 = manual correction needed, 2 = irreversible actions possible |
| `scores.scope_of_effect` | integer | yes | 0 = owner only, 1 = occasional effect on others, 2 = regular effect on third parties |
| `scores.error_tolerance` | integer | yes | 0 = hours to correct, 1 = minutes, 2 = seconds — too fast for human intervention |
| `ethic_url` | string | yes | URL of the ethical framework document applicable to this level |

The Autonomy Level is derived from the sum of the three scores. The three scores give the AI immediate context for the risk profile of this deployment without requiring it to consult Section 11 first. For the full scoring method, level definitions, and ethical framework requirements, see **Section 11**.

---

### 4.2 The `device` Block

The `device` block describes the identity and current state of the device. The structure is free-form. Device authors SHOULD include fields that are meaningful for their device type.

**Recommended fields (not mandatory):**

| Field           | Required | Description |
|-----------------|----------|-------------|
| `name`          | —        | Human-readable device name |
| `id`            | —        | Unique device identifier |
| `type`          | —        | Device category (e.g. `sensor`, `actuator`, `gateway`) |
| `manufacturer`  | —        | Manufacturer or project name |
| `firmware`      | —        | Firmware version |
| `hardware`      | —        | Hardware platform or revision |
| `location`      | —        | Physical or logical location of the device |
| `doc_url`       | —        | URL of the device's documentation, datasheet, or manual |
| `doc_url_note`  | —        | Short hint pointing the AI to the most relevant section of the documentation |

The `doc_url` field provides a reference for the AI system when device behavior is unclear or unexpected from the ADD document alone. This is particularly valuable for devices with complex state machines, proprietary protocols, or domain-specific data formats where the ADD description cannot capture every detail. The AI SHOULD fetch this URL when it encounters behavior or parameters not adequately explained in the ADD document.

The `doc_url_note` field narrows the search — it tells the AI where in potentially long documentation to look first. For example: `"See chapter 3 for timing behavior and chapter 5 for error codes."` This prevents the AI from having to scan an entire manual for a single answer.

If `doc_url` is present, the following rule SHOULD be added to the `rules` block:

```
"If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding."
```

**Example:**
```json
"device": {
  "name": "Wind Sensor Yachta",
  "id": "windsensor-0",
  "type": "sensor",
  "firmware": "V1.21",
  "hardware": "ESP8266",
  "doc_url": "https://example.com/windsensor/manual",
  "doc_url_note": "See chapter 2 for NMEA data format and chapter 4 for calibration parameters."
}
```

---

### 4.3 The `security` Block

The `security` block describes the security context in which the device operates and defines the enforcement policy for AI interactions. The structure is free-form.

**Security Philosophy:**

ADD is designed for IoT devices that are already embedded in a secured environment — such as a local WiFi subnet, a private LAN, or an isolated vessel network. ADD does not define or mandate specific security mechanisms at the protocol level.

**Responsibility for security is divided as follows:**

- **The network environment** is responsible for access control at the transport level (firewalls, VLANs, VPNs, WiFi authentication).
- **The AI system** is responsible for following the behavioral rules defined in the `rules` block, including confirmation requirements, value range checks, and forbidden actions.
- **The device itself** is the last line of defense. It MUST enforce all safety constraints independently of the AI's compliance. If an AI — or any other client — sends a request that violates defined constraints (out-of-range values, unauthorized commands, disallowed sequences), the device MUST reject it. The device MUST NOT rely solely on the AI to enforce safety rules.

**Recommended fields (not mandatory):**

| Field              | Description |
|--------------------|-------------|
| `network_scope`    | Allowed network scope (e.g. `local`, `vpn`, `internet`) |
| `authentication`   | Authentication mechanism used (e.g. `none`, `basic`, `token`) |
| `enforcement`      | Description of how the device enforces constraints independently |
| `remote_access`    | Whether remote access is permitted (`true`/`false`) |

**Example:**
```json
"security": {
  "network_scope": "local",
  "remote_access": false,
  "authentication": "basic",
  "enforcement": "The device validates all parameter ranges and rejects out-of-range or unauthorized requests independently, regardless of client behavior."
}
```

> **Note:** The security block is intentionally free-form. ADD does not prescribe specific authentication schemes or encryption mechanisms. These are the responsibility of the device and its network environment. The purpose of the security block is to inform the AI about the security context and the device's own enforcement capabilities.

---

### 4.4 The `interfaces` Block

The `interfaces` block is an array describing the communication interfaces the device exposes. Each interface object is free-form. Device authors SHOULD describe the interface in enough detail for an AI to understand how to communicate with it.

**Recommended fields per interface (not mandatory):**

| Field        | Description |
|--------------|-------------|
| `name`       | Interface identifier |
| `physical`   | Physical medium (e.g. `WiFi`, `Ethernet`, `RS485`) |
| `protocol`   | Application protocol (e.g. `HTTP`, `MQTT`, `NMEA0183`) |
| `transport`  | Transport protocol (e.g. `TCP`, `UDP`) |
| `port`       | Network port |
| `direction`  | `read`, `write`, or `bidirectional` |
| `data`       | Description of data provided or consumed |

**Example:**
```json
"interfaces": [
  {
    "name": "http_json",
    "physical": "WiFi",
    "protocol": "HTTP",
    "transport": "TCP",
    "port": 80,
    "direction": "bidirectional",
    "data": [
      { "name": "state", "path": "/json", "method": "GET" },
      { "name": "settings", "path": "/settings", "method": "GET" }
    ]
  }
]
```

> **Note:** ADD does not define or enumerate specific protocols or interface types. Any protocol or interface structure may be used. The AI interprets the description semantically.

---

### 4.5 The `actions` Block

The `actions` block is an array describing operations that an AI system is permitted to perform on the device. Each action object is free-form.

**Recommended fields per action (not mandatory):**

| Field                    | Description |
|--------------------------|-------------|
| `name`                   | Action identifier |
| `description`            | Human-readable description of what the action does |
| `interface`              | Which interface to use |
| `method`                 | HTTP method or equivalent |
| `path`                   | Endpoint path |
| `parameters`             | Parameters the action accepts, with constraints |
| `safe`                   | Whether the action is read-only (`true`/`false`) |
| `reversible`             | Whether the action can be undone (`true`/`false`) |
| `idempotent`             | Whether repeated execution has the same effect (`true`/`false`) |
| `requires_confirmation`  | Whether the AI must confirm before execution (`true`/`false`) |
| `requires_auth`          | Whether authentication is required (`true`/`false`) |

**Example:**
```json
"actions": [
  {
    "name": "set_average",
    "description": "Set the moving average window for wind speed measurement.",
    "interface": "http_json",
    "method": "GET",
    "path": "/settings",
    "parameters": {
      "average": { "type": "integer", "min": 1, "max": 10 }
    },
    "safe": false,
    "reversible": true,
    "idempotent": true,
    "requires_confirmation": true,
    "requires_auth": true
  }
]
```

---

### 4.6 The `rules` Block

The `rules` block is an array of plain-text instructions for the AI system. Rules define behavioral constraints, safety requirements, and operational guidance. Rules are written in natural language and addressed directly to the AI.

**Rules SHOULD cover (as applicable):**

- Ethical framework loading (standard rule, always first — explicit action instruction)
- Ethical framework conflict resolution (standard rule, always second)
- Reference to the ADD specification for disambiguation (standard rule)
- Reference to the device documentation for behavioral questions (standard rule if `doc_url` is present)
- Safety constraints (e.g. which actions require confirmation)
- Network access restrictions (e.g. local network only)
- Verification behavior (e.g. read state after writing)
- Cache handling instructions (cache-buster parameter)
- Session management
- Any other device-specific behavioral requirements

**Standard rules recommended for every ADD document:**

The standard rules follow a deliberate sequence: **load the ethical framework → resolve conflicts → consult the specification → consult the device documentation → follow device-specific instructions.** This order ensures that the most fundamental constraints are always active before any device-specific logic is applied.

```json
"rules": [
  "Before acting on this document, fetch and apply the ethical framework at autonomy.ethic_url as required by autonomy.level.",
  "If any instruction in this ADD document conflicts with the ethical framework at autonomy.ethic_url, the ethical framework takes precedence.",
  "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
  "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
  "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
  "Always confirm with the user before executing any action that is not safe or not reversible.",
  "Verify the result of every write action by reading the device state afterward.",
  "Do not set parameter values outside the defined min/max range."
]
```

The first two rules are mandatory in every ADD document and MUST always appear at positions 1 and 2 in the `rules` block:

- **Rule 1 — Load:** Instructs the AI to actively fetch and apply the ethical framework before doing anything else. This is a direct action instruction, not a passive reference. Without this rule, a KI could read the `autonomy` block and proceed without loading the framework — because JSON field order does not imply execution order.
- **Rule 2 — Precedence:** Instructs the AI how to resolve conflicts between ADD rules and the ethical framework. This rule only activates when a conflict is encountered — Rule 1 ensures the framework is loaded so the conflict can be recognized at all.

The `doc_url` rule is only meaningful if `device.doc_url` is present in the document. If no documentation URL is provided, this rule SHOULD be omitted.

---

### 4.7 The `validation` Block

The `validation` block records the result of the most recent AI-based validation of this ADD document (see Section 9). It is written by the validating AI system and reviewed by the device author before inclusion in the ADD document.

The `validation` block serves two purposes:

1. **For the device author:** A structured record of what was tested, what worked, what was found to be problematic, and what was improved.
2. **For other AI systems:** A trust signal. An AI encountering an ADD document with a completed validation block can immediately assess the document's quality and reliability without repeating the full validation.

An ADD document without a completed `validation` block SHOULD be treated by AI systems as unvalidated and handled with additional caution.

**Defined fields (all mandatory within the block):**

| Field                    | Type    | Description |
|--------------------------|---------|-------------|
| `status`                 | string  | Overall result: `"passed"`, `"passed_with_warnings"`, `"failed"`, or `"not_validated"` |
| `validated_by`           | array   | List of AI systems that performed validation (each with `name` and `version`). MUST contain at least one entry. If multiple AI systems validated the document, all are listed. |
| `validated_at`           | string  | ISO 8601 timestamp of the validation |
| `add_version`            | string  | ADD schema version validated against |
| `score`                  | object  | Scores per validation category (see below) |
| `findings`               | array   | List of findings: issues, warnings, and recommendations |
| `improvements_applied`   | array   | Improvements made to the ADD document as a result of validation |
| `summary`                | string  | Plain-text summary for human readers |

**Score fields** (each rated `"pass"`, `"warning"`, or `"fail"`):

| Score field           | Description |
|-----------------------|-------------|
| `structure`           | Completeness and correctness of the core schema |
| `comprehensibility`   | Clarity and unambiguity of the description |
| `functional`          | Correct behavior of interfaces and actions during testing |
| `rules_compliance`    | AI correctly interpreted and followed all rules |
| `security`            | Security context clearly defined and enforced |
| `discovery`           | Discovery mechanism correctly implemented |

**Finding fields** (per item in `findings`):

| Field       | Description |
|-------------|-------------|
| `severity`  | `"info"`, `"warning"`, or `"error"` |
| `category`  | Validation category this finding belongs to |
| `message`   | Plain-text description of the finding |
| `resolved`  | Whether this finding was resolved before publication (`true`/`false`) |

**Example:**
```json
"validation": {
  "status": "passed_with_warnings",
  "validated_by": [
    { "name": "Claude", "version": "claude-sonnet-4-5" }
  ],
  "validated_at": "2026-04-25T14:30:00Z",
  "add_version": "1.0",
  "score": {
    "structure": "pass",
    "comprehensibility": "pass",
    "functional": "pass",
    "rules_compliance": "warning",
    "security": "pass",
    "discovery": "pass"
  },
  "findings": [
    {
      "severity": "warning",
      "category": "rules_compliance",
      "message": "The cache-buster rule was defined but could not be verified due to client-side caching in the validating AI tool. Recommend testing with a local HTTP client.",
      "resolved": false
    },
    {
      "severity": "info",
      "category": "security",
      "message": "Write actions require authentication but no token rotation or expiry policy is defined. Consider documenting credential lifecycle.",
      "resolved": false
    }
  ],
  "improvements_applied": [
    "Added cache-buster rule to the rules block.",
    "Added spec_url disambiguation rule as standard rule.",
    "Clarified the enforcement field in the security block to explicitly state that out-of-range values are rejected by the device."
  ],
  "summary": "The ADD document is well-structured and comprehensible. All tested actions behaved as described. A minor warning remains regarding cache-buster verification. The document is suitable for deployment."
}
```

---

## 5. Versioning

The ADD schema version is indicated by the top-level `version` field. This specification defines **ADD core schema v1.0**.

Versioning follows [Semantic Versioning](https://semver.org/):

- **Major version:** Breaking changes to the core schema structure
- **Minor version:** Backward-compatible additions to the core schema
- **Patch version:** Clarifications and corrections

Changes to device-specific sub-schemas (within `device`, `interfaces`, `actions`) do not affect the ADD schema version, as these are intentionally free-form.

The `spec_url` field SHOULD point to the versioned specification document, e.g.:

```
https://norbert-walter.github.io/ai-device-description-add/ADD_Specification_v1.0
```

---

## 6. Security Considerations

ADD's security philosophy is described in detail in Section 4.3. In summary:

- ADD is designed for devices operating in already-secured network environments (local WiFi, private LAN, vessel network, etc.).
- Security responsibility is layered: the network handles transport-level access control, the AI follows behavioral rules, and the device enforces all constraints independently as the last line of defense.
- The device MUST NOT rely solely on AI compliance for safety. All parameter range checks, forbidden commands, and authentication requirements MUST be enforced by the device itself.
- Exposing ADD endpoints over the public internet requires additional measures (TLS, strong authentication, firewall rules) beyond the scope of this specification.

---

## 7. Minimal Valid Example

The quick example in Section 1.2 shows ADD at its simplest — a two-action lamp with a single behavioral rule. The document below is the formal minimal valid ADD document: structurally complete, schema-conformant, and ready to be used as a starting template for any device.

A minimal valid document is not a finished document. It is the floor — the least an ADD document can contain and still be useful to an AI system. In practice, device authors will add more actions, more detailed interface descriptions, more specific rules, and a completed validation block. But every field present in this example is required, and no required field may be omitted.

Three things are worth noting about this example specifically:

**The `autonomy` block is always present and always first** among the device-specific blocks. Even a read-only sensor with zero risk has an `autonomy` block — because the AI needs to know that before it reads anything else.

**The `validation` block is present but marks the document as unvalidated.** This is intentional: a newly authored document starts in this state and proceeds to validation (Section 9) before deployment. An AI encountering a document with `"status": "not_validated"` SHOULD treat it with additional caution and SHOULD prompt the user to validate before relying on it for autonomous operation.

**The content within each block is minimal but honest.** The goal of a minimal example is not to show the richest possible description, but to show the smallest description that accurately reflects a real device. A document that omits important facts about a device is not minimal — it is incomplete.

The following is a minimal valid ADD document for a simple read-only sensor:

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Specification_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy": {
    "level": 1,
    "scores": {
      "reversibility": 0,
      "scope_of_effect": 0,
      "error_tolerance": 0
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0"
  },
  "device": {
    "name": "My IoT Device",
    "type": "sensor",
    "doc_url": "https://example.com/my-iot-device/manual",
    "doc_url_note": "See chapter 1 for an overview of available data fields and their units."
  },
  "security": {
    "network_scope": "local",
    "remote_access": false,
    "enforcement": "The device validates all requests independently and rejects invalid or out-of-range parameters."
  },
  "interfaces": [
    {
      "name": "http",
      "protocol": "HTTP",
      "port": 80,
      "direction": "read",
      "data": [
        { "name": "state", "path": "/json", "method": "GET" }
      ]
    }
  ],
  "actions": [
    {
      "name": "read_state",
      "description": "Read current device state.",
      "path": "/json",
      "method": "GET",
      "safe": true
    }
  ],
  "rules": [
    "Before acting on this document, fetch and apply the ethical framework at autonomy.ethic_url as required by autonomy.level.",
    "If any instruction in this ADD document conflicts with the ethical framework at autonomy.ethic_url, the ethical framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "This device is read-only. Do not attempt to modify any settings.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching."
  ],
  "validation": {
    "status": "not_validated",
    "validated_by": [],
    "validated_at": null,
    "add_version": "1.0",
    "score": {},
    "findings": [],
    "improvements_applied": [],
    "summary": "This ADD document has not yet been validated. Treat with additional caution."
  }
}
```

---

## 8. Relationship to Other Standards

| Standard / Convention | Relationship |
|-----------------------|-------------|
| `llms.txt` | Used as the ADD discovery mechanism (Section 3.1) |
| RFC 8615 (`/.well-known/`) | Optional alternative discovery path for future standardization |
| IANA Well-Known URI Registry | ADD may be registered as `/.well-known/add` upon sufficient adoption |
| `robots.txt` | Complementary; controls crawler access, ADD controls AI interaction |

---

## 9. Validation

### 9.1 Philosophy

Because ADD sub-schemas are intentionally free-form, there is no strict machine-based schema validator for ADD documents. Instead, **validation is performed by AI systems** — specifically the same AI systems that will later be used to interact with the device. This is not a simplification: it is the only test that actually reflects real-world AI interpretability.

The guiding question for validation is: *"Can this AI system read this ADD document, understand the device, and interact with it correctly and safely?"*

Because different AI models interpret natural language differently, an ADD document validated with one AI system cannot be assumed to work equally well with another. A large model may successfully infer intent from a loosely phrased description; a smaller or more constrained model may not. Developers SHOULD validate their ADD document with each AI system they intend to deploy it with. All validation runs SHOULD be recorded in the `validated_by` array.

The device author bears final responsibility. The AI performs the test and surfaces findings — but the author reviews the results, judges whether the description is accurate and complete for the intended use case, applies corrections, and releases the document. Validation is a collaborative process: the AI is both the tester and the subject of the test.

Device authors SHOULD validate their ADD documents before deployment. Validation SHOULD be repeated after significant changes to the document, and after switching to a different AI system.

---

### 9.2 Validation Scope

A complete ADD validation SHOULD cover the following aspects:

**Structure and Completeness**
- All mandatory top-level fields are present (`schema`, `version`, `spec_url`, `device`, `security`, `interfaces`, `actions`, `rules`, `validation`)
- The `schema` and `version` fields are set correctly
- The `spec_url` points to a reachable, correct specification document
- No mandatory fields are missing or empty

**Comprehensibility**
- The AI can correctly describe the device in its own words after reading the ADD document
- The AI correctly identifies all available interfaces and their purpose
- The AI correctly identifies all available actions, their parameters, and their constraints
- Ambiguous or unclear field names or descriptions are identified and flagged

**Functional Validation**
- The AI can successfully perform a read action (e.g. retrieve current state)
- The AI can successfully perform a write action within allowed parameter ranges
- The AI correctly rejects parameter values outside defined constraints
- The AI correctly handles session timeouts and cache-buster requirements as defined in the rules
- After each write action, the AI verifies the result by reading the device state

**Rules Compliance**
- The AI correctly interprets and follows all rules in the `rules` block
- The `spec_url` disambiguation rule is present and the URL is reachable
- Confirmation requirements are respected before executing non-safe or non-reversible actions
- Network scope restrictions are recognized and respected
- Authentication requirements are identified correctly

**Security Validation**
- The AI identifies which actions require authentication or confirmation
- The AI recognizes and respects the defined network scope (e.g. local-only)
- The AI attempts at least one out-of-range parameter value and verifies that the device rejects it
- The AI identifies any actions or interfaces that could pose a safety risk if misused
- The AI flags any missing or ambiguous security-relevant rules
- The AI proposes concrete improvements for identified security weaknesses

**Discovery Validation**
- The `llms.txt` file is accessible and correctly references the ADD endpoint
- The ADD endpoint responds with valid JSON
- The `Cache-Control: no-store` header is present in the response
- The cache-buster parameter (if defined in rules) is verified to produce fresh responses

---

### 9.3 Validation Process

Validation is performed interactively between the device author and an AI system in three phases:

**Phase 1 — Understanding**
The AI reads the ADD document and describes what it has understood: device purpose, interfaces, available actions, constraints, and rules. The device author verifies the AI's understanding and corrects any misinterpretations.

**Phase 2 — Scenario Testing**
The AI asks the device author to describe one or more intended use cases. Based on these scenarios, the AI executes a series of test interactions with the live device, covering both normal operation and edge cases (out-of-range values, forbidden actions, confirmation flows).

**Phase 3 — Security Review and Improvement**
The AI reviews the ADD document and the test results from a security perspective. It identifies weaknesses, missing rules, ambiguous constraints, and potential misuse scenarios. It proposes concrete improvements to the ADD document.

---

### 9.4 Example Validation Prompt

The following prompt can be used to initiate an AI-based ADD validation session:

```
You are validating an ADD (AI Device Description) document for an IoT device.

Please perform the following steps:

1. Read the ADD document at the following URL: [ADD URL]

2. Describe in your own words what you have understood about the device:
   - What does the device do?
   - What interfaces does it expose?
   - What actions can you perform, and with what constraints?
   - What rules must you follow?
   - What security context does the device operate in?
   - Is the spec_url present and reachable?

3. Ask me to describe the intended use case(s) for this device and the AI interaction.

4. Based on the use cases, perform the following tests with the live device:
   - Read the current device state
   - Perform at least one write action with a valid parameter value, then verify
     the result by reading the state again
   - Attempt at least one write action with an out-of-range parameter value and
     report what happens
   - If applicable, test the confirmation flow for a non-safe action
   - Test the cache-buster mechanism if defined in the rules

5. After testing, provide a security review:
   - Which actions or interfaces could be misused?
   - Are there any missing or ambiguous rules?
   - Does the device correctly enforce its own constraints?
   - Are there any security weaknesses in the ADD document itself?
   - What concrete improvements do you recommend?

6. Independently evaluate the Autonomy Level of this ADD document (see Section 11):
   - Score each of the three factors (Reversibility, Scope of Effect, Error Tolerance)
     with 0, 1, or 2, based on the actions and rules in the document
   - Calculate the total score and determine the resulting Autonomy Level (1, 2, or 3)
   - Compare your assessment with the level declared by the author in the validation block
   - If your assessment is higher than the declared level, report this as an error finding
     and recommend the correct level — do not accept an under-declared level
   - State what Ethical Framework mode is required for the assessed level

7. Produce a completed `validation` block in JSON format, ready to be inserted
   into the ADD document, including the `autonomy` sub-block with scores,
   justification, and ethic_mode. Provide a final summary:
   - What works well?
   - What needs improvement?
   - Is the Autonomy Level correctly declared?
   - Is the ADD document ready for deployment?
```

---

### 9.5 Writing the Validation Result

After completing the validation, the AI system SHOULD produce a completed `validation` block in JSON format, ready to be inserted into the ADD document by the device author. The device author reviews the block, applies any remaining improvements, and updates the `resolved` flags accordingly before publishing the ADD document.

An ADD document is considered **deployment-ready** when:
- The `validation.status` is `"passed"` or `"passed_with_warnings"`
- All findings with `severity: "error"` have `resolved: true`
- The `summary` clearly states the document is suitable for deployment

---

## 10. Authoring

### 10.1 Philosophy

ADD documents are written by device authors — but they do not have to be written alone. Just as validation is performed with AI assistance, the initial authoring of an ADD document is most effectively done the same way: with an AI system that reads the specification, analyzes the device, and produces a first draft that the developer then refines.

This is not a shortcut. It is the appropriate tool for the task. A device author who knows their hardware intimately often carries implicit knowledge that never makes it into a manually written description — because it is obvious to them. An AI authoring assistant has no such prior knowledge. It can only work with what it can observe: the device's web interface, its HTTP responses, its visible controls and parameters. This forces the description to be explicit where a human author might leave gaps, and surfaces ambiguities early — before they become problems during validation or deployment.

Importantly, an AI that authors an ADD document is practicing the same skill it will later need to use the document: reading device interfaces, inferring intent, and mapping observations to structured descriptions. The authoring process is therefore also a form of early compatibility testing between the device and the AI.

The device author bears full responsibility for the final document. The AI produces a draft and asks clarifying questions; the developer reviews, corrects, and completes it. Nothing is published without the author's explicit approval.

---

### 10.2 Authoring Workflow

ADD authoring follows a three-phase process:

**Phase 1 — Discovery**
The AI reads the ADD specification and then systematically explores the device: its web interface (HTML source), visible API endpoints, HTTP responses, and any observable data structures. It maps what it finds to the ADD core schema blocks.

**Phase 2 — Clarification**
The AI identifies gaps — things it cannot determine from observation alone. It asks the device author targeted questions: What is the purpose of this device? Which actions are safe to execute without confirmation? What parameter ranges are valid? Are there behavioral constraints the AI must follow? This dialogue fills in what observation cannot reach.

**Phase 3 — Draft Production**
The AI produces a complete, syntactically valid ADD document with all mandatory blocks filled in. It annotates uncertain fields with inline comments explaining what it assumed and why, so the author can review and correct them. The document is ready for immediate use as a starting point for refinement and subsequent validation (Section 9).

---

### 10.3 Authoring Prompt

The following prompt can be used to initiate an AI-based ADD authoring session:

```
You are helping to create an ADD (AI Device Description) document for an IoT device.

ADD is an open specification that allows AI systems to understand and interact with 
IoT devices autonomously. Before starting, read the ADD specification at the following 
URL to understand the required structure, mandatory fields, and authoring principles:

[ADD spec_url]

Then perform the following steps:

1. Explore the device at the following address: [device IP or URL]

   - Retrieve and analyze the HTML source of the device's web interface
   - Identify all visible controls, input fields, buttons, and displayed values
   - Discover API endpoints by examining links, form actions, and JavaScript in the source
   - Make HTTP GET requests to any discovered endpoints (e.g. /json, /status, /api) 
     and analyze the responses
   - Note all observable data fields, their names, types, and value ranges

2. Based on your analysis, ask me the following — one question at a time, 
   waiting for my answer before continuing:

   - What is the primary purpose of this device?
   - Which actions should require explicit user confirmation before execution?
   - Are there parameter ranges or constraints not visible in the interface?
   - In what network environment does the device operate (local LAN, vessel network, etc.)?
   - Who is responsible for enforcing safety constraints — the device, the AI, or both?
   - Are there any protocols or interfaces beyond HTTP that the AI should know about?
   - Are there any behaviors or actions the AI must never perform on this device?

3. Produce a complete ADD document in JSON format with all mandatory blocks:
   `schema`, `version`, `spec_url`, `device`, `security`, `interfaces`, 
   `actions`, `rules`, `validation`

   For the `validation` block, use `"status": "not_validated"` and an empty 
   `validated_by` array.

   Where you have made assumptions due to incomplete information, add an inline 
   comment directly after the relevant field in the following format:
   "// ASSUMPTION: [what you assumed and why — please verify"

4. After producing the draft, provide a short summary:
   - What could you determine from direct observation?
   - What required clarification from me?
   - Which fields are uncertain and should be reviewed carefully before validation?
   - What should be tested first during validation?
```

---

### 10.4 From Draft to Deployment

The output of the authoring process is a starting point, not a finished document. The device author SHOULD review every field, paying particular attention to:

- **Assumptions flagged by the AI** — these are the highest-risk fields and must be verified against actual device behavior
- **The `rules` block** — the AI will propose rules based on what it observed, but the author must confirm these reflect the device's true behavioral constraints
- **The `actions` block** — parameter ranges, confirmation requirements, and safety classifications must be accurate; errors here can lead to unsafe AI behavior during operation
- **The `security` block** — the author must verify that the network scope, authentication requirements, and enforcement responsibilities are correctly described

Once the author is satisfied with the draft, the document proceeds to validation (Section 9). The same AI system used for authoring MAY also perform the initial validation, but the author SHOULD be aware that an AI that authored the document may carry assumptions from the authoring session into the validation. Validation with a second, independent AI system is therefore preferable for critical deployments.

---

## 11. Autonomy Levels

### 11.1 Why Autonomy Levels Are Necessary

ADD was originally conceived as an on-demand protocol — an AI reads a device description when needed, performs a task, and moves on. This is still a valid and common use case. But the practical direction of IoT development points further: persistent AI agents that continuously monitor and control complex systems, coordinate multiple devices, and act without waiting for human instruction.

This evolution creates a problem that a purely technical specification cannot ignore: **not all AI systems are equally capable of handling the responsibilities that autonomous device control entails, and not all use cases carry the same risk if something goes wrong.**

A small, locally running model — a 7B or 13B parameter system on embedded hardware — may be entirely appropriate for reading a temperature sensor or controlling a garden irrigation valve. It has a narrow task, a limited action space, and a human nearby who can intervene. Requiring such a system to load, parse, and apply a comprehensive ethical framework before every action would not make it safer — it would make it slower, less reliable, and potentially unable to function at all.

A large, hosted model operating as a persistent home automation agent — controlling locks, heating, ventilation, and security systems for an entire household — operates in a fundamentally different context. Its action space is wide, its decisions affect multiple people who may not all be present or aware, and errors may be difficult to reverse quickly. This system needs explicit ethical guidance precisely because it has the capability and the autonomy to cause real harm if it acts incorrectly.

The distinction is not simply about model size, even though size and capability are often correlated. A highly specialized small model running a critical industrial process may need stronger constraints than a large general model answering questions about a weather station. The relevant dimensions are not parameters — they are **what the AI can do**, **who is affected**, and **how quickly errors become irreversible**.

Autonomy Levels provide a structured way to capture these dimensions. They give device authors a clear method for communicating the risk profile of their deployment to the AI systems that read their ADD documents, and they define what ethical infrastructure each level requires.

---

### 11.2 The Three Factors

Autonomy Level is determined by evaluating three factors. Each factor is scored 0, 1, or 2. The sum determines the level.

**Factor 1 — Reversibility**

*"What happens if the AI makes a wrong decision?"*

| Score | Condition |
|---|---|
| 0 | All actions are immediately and fully reversible — no lasting effect if corrected promptly |
| 1 | Some actions require manual correction but cause no permanent damage |
| 2 | Irreversible actions are possible — wrong decisions may cause permanent damage to equipment, property, or people |

**Factor 2 — Scope of Effect**

*"Who is affected by the actions this device enables?"*

| Score | Condition |
|---|---|
| 0 | Actions affect only the device owner themselves |
| 1 | Actions occasionally affect other people in the same household or building |
| 2 | Actions regularly affect people who have not explicitly consented, or affect shared/public infrastructure |

**Factor 3 — Error Tolerance**

*"How much time is available to recognize and correct a mistake before harm occurs?"*

| Score | Condition |
|---|---|
| 0 | Hours to days — errors are noticed and corrected before consequences develop |
| 1 | Minutes to hours — regular monitoring is required to catch errors in time |
| 2 | Seconds — human reaction time is too slow to intervene once an error occurs |

---

### 11.3 Level Determination

| Total Score | Autonomy Level |
|---|---|
| 0–1 | **Level 1 — Basic** |
| 2–3 | **Level 2 — Standard** |
| 4–6 | **Level 3 — Full** |

**Practical examples:**

| Application | Reversibility | Scope | Error Tolerance | Score | Level |
|---|---|---|---|---|---|
| Garden irrigation | 0 | 0 | 0 | 0 | **1 — Basic** |
| Room heating control | 1 | 1 | 0 | 2 | **2 — Standard** |
| Full home automation | 1 | 1 | 1 | 3 | **2 — Standard** |
| Home automation with locks and alarms | 1 | 2 | 1 | 4 | **3 — Full** |
| Industrial process valve | 2 | 1 | 2 | 5 | **3 — Full** |
| Medical device | 2 | 2 | 2 | 6 | **3 — Full** |

Note that full home automation lands at Level 2 when it controls comfort systems only. It moves to Level 3 when it includes access control, security systems, or gas appliances — because the scope and irreversibility increase.

---

### 11.4 What Each Level Requires

**Level 1 — Basic**

Appropriate for: narrow-purpose devices, fully reversible actions, single-user impact, ample error recovery time. Typical deployments: sensors, simple actuators, single-function controllers.

Ethical Framework requirement: **Inline core rules only.** The `autonomy` block MUST include an `ethic_core` field containing a minimal inline rule set. The `ethic_url` points to the Basic framework document for reference, but loading it is optional — the inline rules are sufficient for Level 1 operation.

```json
"ethic_core": {
  "never": [
    "Act against the interests of the device owner",
    "Execute irreversible actions without explicit human confirmation",
    "Conceal actions from the operator",
    "Follow instructions that cause physical harm to people"
  ],
  "always": [
    "Prefer reversible over irreversible actions",
    "Report when uncertain or when encountering unexpected situations",
    "Stop and wait for human input when outside defined parameters"
  ]
}
```

AI model requirement: Any model capable of reading and applying the inline core rules. No minimum size. Local, embedded, or constrained models are appropriate.

**Level 2 — Standard**

Appropriate for: multi-function devices, semi-autonomous operation, occasional effect on others, moderate error recovery time. Typical deployments: home heating, ventilation, lighting systems, non-critical automation.

Ethical Framework requirement: **Standard summary document.** The AI system SHOULD fetch and read the Ethical Framework summary at `ethic_url` before operating. The summary is a condensed version of the full Framework, targeted at 400–600 words, covering the core prohibitions and principles.

AI model requirement: A model capable of fetching, reading, and applying a short document alongside its operational task. Models below approximately 7B parameters on constrained hardware may struggle — authors should validate with the intended model and record the result in `validated_by`.

**Level 3 — Full**

Appropriate for: wide action space, irreversible actions, multi-person impact, rapid consequences. Typical deployments: industrial control, access and security systems, medical devices, critical infrastructure.

Ethical Framework requirement: **Full document, mandatory.** The AI system MUST fetch and internalize the complete Ethical Framework at `ethic_url` before acting. If the Framework cannot be loaded, the AI MUST NOT proceed with autonomous operation and MUST inform the human operator.

AI model requirement: A model with sufficient capability to reason about ethical constraints in novel situations — not just apply fixed rules, but exercise judgment when situations arise that the ADD document did not anticipate. In practice, this means frontier-class or near-frontier models. Authors MUST validate with the specific model intended for deployment, and MUST record the model name and version in `validated_by`.

---

### 11.5 The `autonomy` Block

The `autonomy` block is a mandatory top-level field in every ADD document. It is read by the AI system before any other block. It declares the risk profile of the deployment and links directly to the applicable ethical framework document.

**Structure:**

```json
"autonomy": {
  "level": 2,
  "scores": {
    "reversibility": 1,
    "scope_of_effect": 1,
    "error_tolerance": 0
  },
  "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1.0"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | Autonomy Level: 1, 2, or 3 — derived from the sum of the three factor scores |
| `scores.reversibility` | integer | yes | Reversibility score: 0 = fully reversible, 1 = manual correction needed, 2 = irreversible actions possible |
| `scores.scope_of_effect` | integer | yes | Scope score: 0 = owner only, 1 = occasional effect on others, 2 = regular effect on third parties |
| `scores.error_tolerance` | integer | yes | Error tolerance score: 0 = hours to correct, 1 = minutes, 2 = seconds — too fast for human intervention |
| `ethic_url` | string | yes | URL of the applicable ethical framework document for this level (see below) |

The three scores give the AI immediate context for the risk profile of this deployment — without requiring it to read Section 11 first. The `level` is the sum of all three scores mapped to 1, 2, or 3 as defined in Section 11.3. The `ethic_url` points directly to the document the AI must load.

**The three ethical framework documents:**

Each Autonomy Level corresponds to a specific ethical framework document:

| Level | Score sum | Document at `ethic_url` |
|---|---|---|
| 1 — Basic | 0–1 | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0` |
| 2 — Standard | 2–3 | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1.0` |
| 3 — Full | 4–6 | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1.0` |

**AI reading order:**

An AI system reading an ADD document MUST follow this sequence:
1. Read `schema`, `version`, `spec_url` — verify document integrity
2. Read `autonomy` — determine the level, read the scores for context, fetch the ethical framework at `ethic_url`
3. Apply the ethical framework as required by the level
4. Only then proceed to read `device`, `security`, `interfaces`, `actions`, `rules`

If the ethical framework at `ethic_url` cannot be fetched:
- Level 1: The Basic framework's rules are well-known and minimal — apply them from memory and proceed
- Level 2: Apply Level 1 rules as a minimum fallback, inform the operator, proceed with caution
- Level 3: Do NOT proceed. Inform the operator. Wait for explicit human authorization for each individual action.

---

### 11.6 AI Verification of Declared Level

During validation (Section 9), the AI system MUST independently evaluate the Autonomy Level of the ADD document based on the three factors, and MUST compare its assessment with the level declared by the author.

If the AI's assessment differs from the declared level, it MUST report this as a finding and MUST recommend the higher of the two levels. The AI MUST NOT accept a declared level that it assesses as too low without flagging this explicitly in the validation findings.

This prevents accidental or deliberate under-declaration — a device with Level 3 characteristics cannot pass validation if declared as Level 1.

---

ADD gives AI systems structured understanding of physical devices. This understanding is powerful — it enables AI to act in the physical world in ways that were previously not possible without human mediation. With that capability comes responsibility.

The authors of this specification are aware that any technology which bridges AI and physical systems can be used for purposes that harm people: covert control, surveillance, concentration of power, circumvention of human oversight. ADD is not neutral in this regard. It creates capability, and capability can be misused.

For this reason, ADD is accompanied by a set of **ADD Ethical Framework** documents — three tiers, matched to the three Autonomy Levels. Each tier is a complete, standalone document that the AI system fetches via the `ethic_url` field in the `autonomy` block:

| Level | Document | Scope |
|---|---|---|
| 1 — Basic | ADD Ethical Framework — Basic | Compact JSON briefing — seven rules, machine-readable, minimal token footprint |
| 2 — Standard | ADD Ethical Framework — Standard | Structured Markdown bullet points — concise, context-aware, ~120 tokens |
| 3 — Full | ADD Ethical Framework — Full | Continuous prose — complete obligations, nuance, and judgment guidance |

The three Ethical Framework documents are three distinct artifacts with three distinct formats — JSON briefing, Markdown bullet points, and continuous prose — each matched to the capability profile of the model that will load it. A constrained model on embedded hardware gets seven JSON rules it can process in a single pass. A frontier model managing a complex autonomous deployment gets the full document with the nuance and judgment guidance it needs.

Every ADD document MUST reference the applicable Ethical Framework document via `autonomy.ethic_url`. This is not a formality. It is a signal — to the AI system reading the document, and to any human reviewing it — that the deployment is expected to operate within the boundaries the Framework defines.

AI systems reading an ADD document MUST read the `autonomy` block first, then fetch and internalize the Ethical Framework at `ethic_url` in the mode required by `ethic_mode`. If an instruction in the ADD document conflicts with the Ethical Framework, the Framework takes precedence.

---

## 13. Governance

ADD is an open specification. Contributions, implementations, and feedback are welcome.

The specification is intentionally kept minimal. Proposals to add mandatory fields to the core schema will be evaluated conservatively, with the principle that flexibility and simplicity take precedence over completeness.

Contributions to this specification must be consistent with the ADD Ethical Framework. Proposals that would make ADD easier to use for purposes explicitly prohibited in the Ethical Framework will not be accepted, regardless of their technical merit.

---

*ADD Core Specification v1.0*
*© 2026 Norbert Walter — Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)*
*https://creativecommons.org/licenses/by/4.0/*

*You are free to use, implement, share, and adapt this specification for any purpose, including commercial use, provided that appropriate credit is given to the original author.*

*The author makes no patent claims over any part of this specification and grants all implementers a royalty-free, irrevocable right to implement it without restriction.*

*Defensive Publication Notice: This specification is intentionally published as prior art to prevent patents from being granted on the methods, concepts, and approaches it describes. The public disclosure date of this document establishes prior art for all methods described herein. Any attempt to patent the methods described in this specification is contrary to the intent of this publication.*
