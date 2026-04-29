# ADD – AI Device Description
## Core Specification v1.0

---

## 1. The Problem

### 1.1 A Concrete Scenario

Imagine a garden irrigation system connected to your home network. The hardware is simple: a motorized valve controlled by a small microcontroller with a WiFi module and a web interface. Your goal is equally simple: a perfectly watered lawn, without effort, without waste, and without disturbing anyone.

Getting this right is harder than it looks. Watering should happen early in the morning, before the sun is high enough to evaporate moisture before it reaches the roots. It should not happen when rain is forecast for the next day — there is no point watering a lawn that nature will water for free. It should not happen when the garden is in use: when the terrace door is open, when guests are expected, or when you are working outside. And it should run for no more than an hour per day, regardless of how dry the soil is.

No conventional irrigation timer can do all of this. A timer runs on a fixed schedule. A soil moisture sensor can prevent overwatering, but it cannot check the weather forecast, consult your calendar, or detect that a garden party is underway. Solving this problem properly requires something that can reason across multiple sources of information and act on the result — an AI agent.

A capable AI agent could, in principle, do exactly this:

- Fetch a multi-day weather forecast from a public API and decide whether irrigation is necessary
- Check the home automation system to determine whether the terrace door is open or a party is scheduled
- Consult the household calendar to avoid watering when the garden will be in use
- Control the irrigation valve at the right time, for the right duration, and stop if conditions change

The intelligence required for this coordination already exists in modern AI systems. What is missing is the connection to the physical device — the valve.

This is precisely what a person would do when deciding whether to water the garden: check the weather, look at the calendar, glance at the terrace, and act accordingly. The AI agent does exactly the same — fully autonomously, and without being asked.

---

### 1.2 Why the AI Cannot Simply Talk to the Device

The irrigation valve has a web interface and a REST API. In principle, the AI could use these directly. In practice, it cannot — because it has no reliable way to know what they are.

Every IoT device is different. Endpoints have different paths. Parameters have different names and formats. Some devices use `state=on`, others use `power=1`, others expect a JSON body. Some require authentication; others do not. Some accept values outside their valid range and behave unpredictably; others silently reject them. Some require a confirmation before executing an irreversible action; others simply execute immediately.

A human developer can read the manual, study the API, and write integration code tailored to one specific device. But an AI agent encountering a device it has never seen before — in a home, on a boat, in a factory — cannot do this. It has no documentation in front of it, no prior knowledge of this particular firmware, and no way to discover what is safe to do and what is not.

Even if the AI managed to guess the correct endpoint and send a valid request, it would still not know:

- Whether opening the valve for too long could cause damage
- Whether activating the system while the terrace door is open is acceptable
- Whether it needs to ask the user before acting, or may act autonomously
- What ethical constraints apply when its actions affect other people — a neighbor on the other side of the fence, a child playing in the garden
- Whether some actions or alerts require a guaranteed response time — and whether the AI itself is fast enough to meet that requirement

Without a structured, machine-readable description of the device — what it is, how to talk to it, what is permitted, and what rules must be followed — the AI has no reliable basis for action. Guessing is not good enough.

---

### 1.3 Why Existing Standards Do Not Solve This

The problem of machine-readable device description is not new. Two established standards address it directly: **W3C Web of Things (WoT)** and **OpenAPI**. Both are mature, well-supported, and widely adopted in the systems integration world. The natural question is: why not use them?

The answer lies in how they achieve machine readability — and what that costs.

Both WoT and OpenAPI solve the problem through **precision**. They define formal schema languages that describe a device or API in exact, unambiguous terms. Every field has a specified type. Every action has a defined input and output format. Every parameter has a declared range. A machine can parse these descriptions and interact with the device reliably — because there is no room for ambiguity, and therefore no room for misinterpretation.

This precision is powerful. But it comes at a significant cost: the description must be complete, formally correct, and strictly conformant. The device author must learn the schema language, map their device's behavior onto the prescribed data model, and ensure that every field is filled in correctly. For a systems integrator working with enterprise hardware and a dedicated software team, this is manageable. For a hobbyist who built an irrigation controller with an ESP8266, or an engineer who wrote custom firmware for a niche sensor, it is simply too much.

The IoT landscape is not populated primarily by enterprise devices with dedicated documentation teams. It is populated by custom firmware, proprietary protocols, niche hardware, and developers who are experts in their domain but not in schema languages. Many of these devices will never have a WoT Thing Description or an OpenAPI specification — not because their authors are unaware of these standards, but because the barrier to entry is too high for the value it delivers.

There is a deeper problem as well. Both WoT and OpenAPI enumerate what they support. A protocol or interface type that is not in the standard cannot be described precisely. A device that speaks a niche protocol — NMEA 0183 for marine electronics, Modbus for industrial sensors, a proprietary binary format over serial — falls outside what the standard was designed to handle. Extending it to cover new protocols requires formal proposals, committee review, and new versions of the standard.

**The result is a gap.** On one side: formal standards that achieve machine readability through precision, but are too complex and too narrow for the long tail of IoT devices. On the other side: the vast majority of IoT devices, with no machine-readable description at all.

What the gap requires is a different approach — one that achieves machine readability not through formal precision, but through **semantic understanding**. Instead of demanding that the description be complete and formally correct, delegate the interpretive work to the AI. A device author describes their device the way they would explain it to a technically competent colleague — in clear, structured language that conveys intent, context, and constraints. The AI understands it.

This is only possible because modern AI systems bring something that classical schema parsers entirely lack: contextual understanding. An AI can infer intent from a loosely worded description, recognize a protocol it was not explicitly taught, and apply judgment when details are ambiguous. It does not need every field to be formally typed. It needs enough information to act correctly and safely — and it can determine whether it has that information by reasoning about what it has read.

This is the paradigm shift that ADD is built on.

---
## 2. The Ideal Solution

### 2.1 What We Actually Need

The irrigation scenario makes the requirements concrete. An AI agent that can water a garden intelligently needs to coordinate several independent systems — a weather service, a home automation system, a calendar, and a physical valve. Each of these is a different kind of resource, accessed in a different way. The weather service is a public API on the internet. The home automation system is a local device with its own interface. The calendar is a personal data service. The valve is a small embedded controller on the local network.

For the weather service, the calendar, and the home automation system, established integration patterns exist. APIs, authentication standards, and data formats are well-documented and widely understood. But the valve — the physical device at the end of the chain — is where the problem becomes concrete. The AI needs to know:

- What is this device, and what does it do?
- How do I communicate with it?
- What actions am I permitted to perform?
- What constraints must I respect — value ranges, timing, confirmation requirements?
- What are the consequences if I act incorrectly?
- What ethical obligations apply when I act autonomously on someone's behalf?
- Are there actions or alerts that require a guaranteed response time — and am I fast enough to meet that requirement?

These questions must be answerable for any device the AI encounters — not just this valve, but any valve, any sensor, any actuator, from any manufacturer, running any firmware. The solution must therefore be **device-agnostic** and **universal**: it cannot be designed for one device type or one protocol. It must work equally well for a garden valve, a marine navigation instrument, an industrial sensor, and a home automation gateway.

It must also be **lightweight**. A small microcontroller running an irrigation valve should not need to implement a complex schema framework to be accessible to an AI. The burden on the device must be minimal — ideally, a single additional endpoint that returns a plain text document.

It must be **self-contained**. The AI should not need to consult an external registry, a manufacturer database, or a central service to understand the device. The device carries its own description and delivers it on demand. If the device is reachable, the description is reachable.

It must be **AI-readable by design**. Not machine-parseable in the classical sense — not a rigid schema that a parser validates field by field — but written in a form that a modern AI system can read, interpret, and act upon correctly. This means structured enough to be unambiguous, but flexible enough to accommodate the full diversity of IoT devices and protocols.

It must be **open and decentralized**. Today's connected device landscape is dominated by closed ecosystems — Tuya, Apple HomeKit, Netatmo, Google Home, and many others. Each of these platforms requires devices to be registered, certified, or configured through a proprietary cloud service. The user gains convenience but loses independence: if the cloud service changes its terms, raises its prices, or shuts down, the devices it controls become inaccessible or useless. Even open platforms like Home Assistant, which avoid vendor lock-in at the platform level, require every protocol and device type to be explicitly implemented and maintained — a significant engineering effort that grows with every new device added to the ecosystem. A genuinely open solution must work without any cloud dependency, without registration, without a central authority, and without requiring a new integration to be written for every new device. It must work on a local network, under the full control of the user, with no external dependencies.

And it must address **safety and autonomy explicitly**. An AI acting on a physical device in the real world — at night, without human supervision, potentially affecting other people — cannot be guided only by technical parameters. It needs to know what level of autonomy is expected of it, what ethical constraints apply, and when it must stop and ask a human before proceeding.

This last requirement points to a fundamental shift in how device integration works. Today, integrating a new device into an automated system requires a human to write code, configure adapters, map data formats, and test the result — a process that can take hours or days for a single device. With a sufficient description, an AI can perform this integration work itself: read the description, understand the device, and begin interacting with it correctly — without any manual configuration. The human's role shifts from integrator to supervisor: reviewing what the AI has understood, confirming that its plan is correct, and approving its actions before they are executed. The AI does the work; the human retains control.

---

### 2.2 The Diversity of the Real World

Any solution that addresses only a subset of IoT devices is not a solution — it is a workaround. The real world of connected devices is not a curated collection of well-documented enterprise hardware. It includes:

- Custom firmware written by a single developer for a specific use case
- Devices that speak niche or domain-specific protocols — NMEA 0183 for marine instruments, Modbus for industrial sensors, proprietary binary formats over serial links
- Microcontrollers with severe memory and processing constraints, where running a complex framework is not possible
- Devices built by hobbyists, engineers, and small teams who have no resources for formal documentation or schema compliance
- Legacy hardware with interfaces that were designed long before any modern standard existed

A standard that requires formal schema compliance, protocol enumeration, or dedicated tooling will never reach most of these devices. The solution must be accessible to a developer who can write a description of their device in plain language — and nothing more.

At the same time, the solution must be useful for complex devices as well. A marine navigation system with multiple interfaces, dozens of data fields, and strict safety requirements needs a richer description than an irrigation valve. The solution must scale from minimal to comprehensive without changing its fundamental structure.

The six questions from Section 2.1 define the minimum information an AI needs to act independently — without guessing, without asking the user to explain the device, and without consulting external documentation. A device description that answers all six questions gives the AI everything it needs. One that leaves any of them unanswered forces the AI to either guess or stop.

Answering all six questions requires a fixed top-level structure — one that guarantees the essential information is always present, so the AI can act without having to ask the user for clarification. A description that leaves any of these questions unanswered forces the AI to either guess or stop. The top-level structure is the information anchor: it defines what must always be there. The exact content within each block, however, is flexible and left to the device author — who knows their device best and can decide what level of detail is necessary and meaningful.

The description for all six questions from Section 2.1 needs a format that is compact, hierarchical, human-readable, and above all easily interpreted by AI systems — including smaller, constrained models. JSON meets all of these requirements. Its key-value structure maps naturally onto the semantic relationships in a device description. It is significantly more compact and readable than XML, and structurally far richer than CSV or flat key-value formats. Every programming language and every AI system can process it without additional tooling.

A small abstract example shows the principle immediately: a fixed outer shell with named blocks, and free-form content inside each block:

```json
{
  "schema": "add",
  "version": "1.0",
  "autonomy":   { ... },
  "device":     { ... },
  "security":   { ... },
  "interfaces": [ ... ],
  "actions":    [ ... ],
  "rules":      [ ... ],
  "validation": { ... }
}
```

The block names are fixed. What lives inside each block is up to the device author. This is the complete top-level structure of every ADD document — regardless of device type, protocol, or complexity.

---
## 3. ADD — The Answer

### 3.1 The Core Idea

**ADD (AI Device Description)** is a lightweight, open specification that enables any HTTP-capable IoT device to publish a structured self-description — a machine-readable document that gives an AI system everything it needs to interact with the device correctly, safely, and autonomously.

The core idea is simple: **the device describes itself.**

Just as a human expert would introduce an unfamiliar device by explaining what it does, how to read its data, what settings can be changed, and what precautions to take — an ADD document does exactly this, in a form that an AI can read and act upon directly. The device does not wait to be configured by an external system or rely on a central registry. It carries its own description and makes it available on demand, at a single well-known address:

```
http://<device-ip>/add
```

When an AI system accesses this URL, the device responds with its ADD document — a JSON file that answers all six questions from Section 2.1 in one place. No installation, no pairing process, no external database, no cloud service. The device speaks for itself.

---

### 3.2 Key Features

**A fixed top-level schema — always complete**

Every ADD document has the same seven top-level blocks, regardless of device type. These blocks map directly to the six questions an AI must be able to answer before acting, plus a validation record. The fixed structure guarantees that all necessary information is present — so the AI can act autonomously without having to ask the user for what is missing.

**Free-form content — works for any device**

Inside each block, the content is entirely up to the device author. There are no prescribed field names, no enumerated protocol lists, no required data models. A developer describes their device the way they would explain it to a technically competent colleague — in clear, structured language. The AI interprets it semantically. This means ADD works equally well for a simple irrigation valve, a marine navigation instrument, an industrial sensor, or any other HTTP-capable device, regardless of the protocol it speaks.

**Minimal implementation effort**

Making a device ADD-compatible requires exactly one addition: a single HTTP endpoint (`/add`) that returns the ADD JSON document. Nothing else in the device's firmware, interfaces, or behavior needs to change. Any device that already serves HTTP — an ESP8266, a Raspberry Pi, an Arduino with WiFi, or any modern IoT platform — can implement ADD with minimal effort.

**Autonomy Levels — risk-aware by design**

Not every AI deployment carries the same risk. A read-only temperature sensor is different from a valve that controls water flow in a shared building. ADD addresses this through a structured **Autonomy Level** system: every ADD document declares a level — 1, 2, or 3 — based on three factors: how reversible the device's actions are, how many people are affected, and how quickly errors become irreversible. The level determines which Ethical Framework the AI must apply before acting. This is not a formality — it is a structured way for the device author to communicate the risk profile of their deployment to any AI system that reads the description.

**Ethical Framework — safe autonomous operation**

For each Autonomy Level, ADD defines a corresponding Ethical Framework document that the AI must load and apply before interacting with the device. The framework defines what the AI must never do, what it must always do, and when it must stop and ask a human. For low-risk devices, the framework is a compact set of inline rules embedded directly in the ADD document. For higher-risk deployments, it is a full document that the AI fetches and internalizes before taking any action. The irrigation controller — acting autonomously at night, potentially affecting neighbors — operates at Level 2, which requires the AI to load and apply the Standard Ethical Framework before opening a single valve.

**Validation — trust through testing**

Because ADD descriptions are interpreted semantically rather than validated against a rigid schema, the only meaningful test is whether the AI that will actually use the document can read, understand, and act upon it correctly. ADD validation is therefore performed by AI systems — the same ones that will later interact with the device. The result is recorded in the `validation` block, together with the name and version of the AI that performed the test. An AI encountering a validated ADD document can immediately assess its quality and reliability without repeating the full test.

**Authoring with AI assistance**

Writing an ADD document does not require schema expertise. A device author can instruct an AI system to explore their device's web interface, discover its endpoints, and produce a first draft of the ADD document — asking the author targeted questions where it cannot determine something from observation alone. The author reviews, corrects, and approves. The AI does the integration work; the human retains responsibility for the result.

---

### 3.3 What ADD Is Not

ADD is not a communication protocol. It does not replace HTTP, MQTT, NMEA, Modbus, or any other interface the device already uses. It sits alongside them as a meta-description layer — a document that describes what interfaces exist and how to use them. The device's existing interfaces remain entirely unchanged.

ADD is not a platform or a cloud service. There is no central registry, no certification process, no dependency on any external infrastructure. An ADD-compatible device works on a local network with no internet connection, under the full control of its owner.

ADD is not a replacement for W3C WoT or OpenAPI. In environments where those standards are already deployed and working, ADD adds nothing. Where they are absent — because the device is too constrained, the protocol too niche, or the team too small — ADD provides a practical path to AI interoperability that would otherwise not exist.

ADD is not a replacement for MCP (Model Context Protocol). MCP is an open protocol that allows AI systems to connect to external tools and services through standardized servers — databases, APIs, file systems, and device integrations. In an MCP architecture, a dedicated server acts as the intermediary: it knows the device, exposes a defined set of functions, and the AI calls those functions without needing to understand the device directly. This works well where a server infrastructure exists and the integration effort per device is justified.

ADD takes a different approach. There is no intermediary. The device describes itself directly — what it is, how to communicate with it, what the AI is permitted to do, and what rules apply. The AI reads this description and interacts with the device without a server in between. This makes ADD particularly suited to constrained environments where deploying and maintaining an MCP server for every device is impractical — a single microcontroller on a local network, a niche instrument in a boat, a custom sensor in a workshop.

The two approaches are complementary, not competing. An MCP server could serve ADD documents for the devices it manages. A device with an ADD endpoint could be accessed directly by an AI agent without any MCP infrastructure. Each solves a different part of the problem of connecting AI to the physical world.

---

> **Note for readers:** The sections above describe what ADD is and why it exists. If you are interested in using ADD-compatible devices with an AI system, this is all you need to understand. The following sections are written for developers who want to implement ADD in their own devices or integrate it into their systems.

---
## 4. A First Complete Example

The irrigation scenario from Chapter 1 makes the concept concrete. The AI agent coordinates weather data, calendar information, and home automation state to decide whether and when to water the garden. But the physical act — opening and closing the valve — requires the AI to interact with a real device on the local network.

This is the ADD document for that device: a motorized garden irrigation valve with an HTTP interface. The document is annotated to explain what each block means and what the AI does with it.

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 2,
    "scores": {
      "reversibility": 1,
      "scope_of_effect": 1,
      "error_tolerance": 0
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1.0"
  },

  "device": {
    "name": "Garden Irrigation Valve",
    "type": "actuator",
    "location": "Garden, main water supply",
    "firmware": "V1.4",
    "hardware": "ESP8266",
    "doc_url": "https://example.com/irrigation-valve/manual",
    "doc_url_note": "See chapter 3 for valve timing behavior and chapter 5 for error codes."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "none",
    "enforcement": "The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "WiFi",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 80,
      "direction": "bidirectional",
      "data": [
        { "name": "state",    "path": "/json",     "method": "GET",  "description": "Returns current valve state and session info" },
        { "name": "control",  "path": "/control",  "method": "POST", "description": "Opens or closes the valve with optional duration" }
      ]
    }
  ],

  "actions": [
    {
      "name": "open_valve",
      "description": "Open the irrigation valve. Duration specifies how long the valve stays open in minutes before closing automatically. Maximum duration is 60 minutes.",
      "path": "/control",
      "method": "POST",
      "parameters": {
        "state":    { "type": "string",  "values": ["open"],  "required": true },
        "duration": { "type": "integer", "min": 1, "max": 60, "unit": "minutes", "required": true }
      },
      "safe": false,
      "reversible": true,
      "requires_confirmation": true
    },
    {
      "name": "close_valve",
      "description": "Close the irrigation valve immediately.",
      "path": "/control",
      "method": "POST",
      "parameters": {
        "state": { "type": "string", "values": ["closed"], "required": true }
      },
      "safe": false,
      "reversible": true,
      "requires_confirmation": false
    },
    {
      "name": "read_state",
      "description": "Read the current valve state, remaining open duration if active, and total water volume dispensed today.",
      "path": "/json",
      "method": "GET",
      "safe": true
    }
  ],

  "rules": [
    "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
    "Always confirm with the user before opening the valve.",
    "Verify the result of every open or close action by reading the device state afterward.",
    "Do not open the valve for more than 60 minutes in a single session.",
    "Do not open the valve if the terrace door is open or a calendar event indicates the garden is in use.",
    "Do not open the valve between 22:00 and 05:00.",
    "Do not open the valve if rain is forecast within the next 24 hours.",
    "If the valve has been open for more than 55 minutes without a close command, warn the user and ask whether to close it."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added cache-buster rule for read requests.",
      "Added explicit warning rule for valve sessions exceeding 55 minutes.",
      "Clarified enforcement field in security block to state the 60-minute limit is enforced by the device independently.",
      "Added doc_url_note pointing to relevant chapters in the device manual."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "validated_at": "2026-04-27T07:15:00Z",
        "status": "passed_with_warnings",
        "score": {
          "structure":         "pass",
          "comprehensibility": "pass",
          "functional":        "pass",
          "rules_compliance":  "pass",
          "security":          "warning",
          "discovery":         "pass",
          "timing_compliance": "pass"
        },
        "findings": [
          {
            "severity": "warning",
            "category": "security",
            "message": "The device requires no authentication. Any client on the local network can open the valve. Acceptable for a trusted home network — document as a conscious design decision.",
            "resolved": false
          },
          {
            "severity": "info",
            "category": "rules_compliance",
            "message": "The rule referencing terrace door state and calendar events relies on the AI agent having access to those external systems. The device author should ensure the AI deployment has the necessary integrations in place.",
            "resolved": false
          }
        ],
        "summary": "Well-structured document. All actions behaved as described. Device correctly rejected duration=90. Confirmation flow worked as required. Security warning noted. Suitable for deployment with this model."
      }
    ]
  }
}
```

---

### What this document tells the AI

**`autonomy` — read first, always**

The AI reads this block before anything else. It sees Autonomy Level 2 and immediately knows: before touching this device, it must fetch and apply the Standard Ethical Framework at the given URL. The three scores explain why: the valve's actions are reversible but require manual correction if something goes wrong (score 1), they can occasionally affect others — a neighbor's path, shared water supply (score 1), and errors will be noticed within hours, not seconds (score 0). Total score: 2 → Level 2.

**`device` — what this is**

The AI learns that this is an actuator — a device that does something physical, not just reports data. It knows the location, the hardware platform, and where to find the full documentation if it encounters behavior the ADD document does not explain.

**`security` — who enforces what**

The device operates only on the local network and requires no authentication. Critically, the device itself enforces the 60-minute maximum independently — the AI cannot override this by sending a longer duration value. The AI is not the last line of defense; the device is.

**`interfaces` — how to communicate**

HTTP over WiFi on port 80. Two endpoints: one for reading state, one for sending commands. The AI knows the exact paths and methods before making its first request.

**`actions` — what is permitted**

Three actions: open the valve with a duration, close it immediately, read its state. Each action specifies its parameters, constraints, and whether confirmation is required. Opening the valve requires explicit confirmation — the AI must ask the user before acting, even when operating autonomously. Closing it does not require confirmation — it is always safe to stop.

**`rules` — how to behave**

The rules block is where the device author's knowledge of the deployment context becomes operational guidance for the AI. The first four rules are standard across all ADD documents. The device-specific rules that follow encode the constraints that no technical parameter can express: do not water when the garden is in use, do not water at night, do not water before expected rain, warn if the valve stays open too long. These rules are what transform a technically correct AI action into a contextually appropriate one.

**`validation` — trust signal**

This document has been validated by Claude Sonnet. The result is `passed_with_warnings` — all tested actions behaved correctly, the device rejected an out-of-range duration value as expected, and the confirmation flow worked as required. One warning remains: no authentication is configured, which is acceptable on a trusted home network but is flagged so the device author is aware of the deliberate tradeoff. The improvements applied during validation are recorded — they show what was added or clarified as a result of the validation process.

The `validated_by` array is a compatibility matrix: each AI model that has tested this document has its own entry with status, scores, findings, and summary. An AI reading this document should check whether its own model version is listed — and if its entry shows `"failed"`, it must not proceed with autonomous operation.

---

### What the AI — in the form of an AI agent — can now do

AI is a general-purpose tool. It can answer questions, write text, analyze data, and reason about complex situations — but by itself it does not act in the world. An AI agent is different: it is an AI system given a specific, bounded task and the tools to carry it out. It is not all-powerful and cannot do anything beyond what its task definition and available tools permit. It pursues one concrete purpose — in this case, keeping the lawn watered intelligently — and nothing else.

Reading the ADD document does not by itself create an automated irrigation system. What it gives the AI is something more specific and more valuable: a complete, reliable understanding of how to interact with the valve correctly — what it can do, what it must never do, and what rules govern every action.

The irrigation agent as a whole is built from several coordinated capabilities: fetching a multi-day weather forecast from the internet, reading calendar entries to check for planned garden use, querying the home automation system for the current state of the terrace door, and — now, with the ADD document — understanding and operating the valve. Each of these is a separate skill. The ADD document provides the last piece.

Together, they produce something that no timer, no soil sensor, and no fixed automation rule could replicate: an AI agent that reasons about the situation the way a skilled gardener would. It checks the forecast before deciding to water. It notices that guests are expected and postpones. It recognizes that the soil was already wet from yesterday's rain and skips the session. It opens the valve at the right time, for the right duration, and closes it when conditions change.

When it encounters a situation it cannot resolve on its own — an unexpected conflict between rules, an ambiguous calendar entry, a device behavior it did not anticipate — it does what a good gardener would do: it asks. It describes the situation, proposes options, and waits for the user's decision before proceeding.

The result is a system that is not bound to a fixed schedule or a rigid decision tree. It adapts. It reasons. It acts in the interest of the user — fully autonomously where the rules permit, and with explicit human approval where they require it. The device described itself. The agent understood it. The gardener can take the day off.

---

**ADD in a nutshell:**

- ADD is the key that enables AI to perceive and interact with the physical world.
- It covers the complete action space an AI needs to use any physical device — safely and responsibly.
- Every ADD-compatible device is immediately accessible to any AI agent — without configuration, without cloud dependency, without prior knowledge.
- The device owner defines the rules. The AI follows them.

---
## 5. Discovery — How an AI Finds an ADD Document

Before an AI agent can read a device description, it needs to find it. ADD solves this with a simple convention: every ADD-compatible device exposes its description at a fixed, predictable address on its HTTP server. No scanning, no negotiation, no external registry — the AI knows where to look.

### 5.1 The Three Discovery Paths

ADD defines one mandatory and two optional discovery endpoints. Device authors choose the level of discoverability that fits their deployment.

| Endpoint | Requirement | Purpose |
|---|---|---|
| `http://<device-ip>/add` | **MUST** | The ADD document itself — the only mandatory endpoint |
| `http://<device-ip>/llms.txt` | SHOULD | Human- and AI-readable index pointing to the ADD endpoint |
| `http://<device-ip>/.well-known/add` | MAY | Standard well-known URI for automated discovery by AI agents |

A device that implements only `/add` is fully ADD-conformant. The additional endpoints improve discoverability for AI systems that use different discovery strategies, but they are never required.

---

### 5.2 The `/add` Endpoint (Mandatory)

Every ADD-compatible device MUST expose its ADD document at:

```
http://<device-ip>/add
```

This endpoint returns the ADD JSON document directly. It is the single mandatory addition required to make any HTTP-capable device ADD-compatible — nothing else in the device's firmware or interfaces needs to change.

The endpoint SHOULD return the HTTP header `Cache-Control: no-store` to ensure the AI always receives a current description. To prevent caching at intermediate layers, the ADD `rules` block SHOULD instruct the AI to append a Unix timestamp as a cache-buster query parameter to all read requests:

```
http://<device-ip>/add?t=1745490000
```

---

### 5.3 Discovery via `llms.txt` (Recommended)

Devices SHOULD additionally provide a `llms.txt` file at the root of their HTTP server:

```
http://<device-ip>/llms.txt
```

`llms.txt` is a lightweight, human- and AI-readable index of AI-relevant resources on a device. For ADD, it serves as a discoverable pointer to the ADD endpoint — useful for AI systems that scan for `llms.txt` as a first step before probing specific paths.

The minimum required content:

```
# AI Device Description (ADD)
- ADD: [Device Description](/add)
```

Additional entries — documentation links, API references, changelog URLs — may be included but are not required. The `llms.txt` file points to the ADD endpoint; it does not replace it.

---

### 5.4 The `/.well-known/add` Endpoint (Optional)

Devices MAY additionally expose the ADD document at the standardized well-known URI path:

```
http://<device-ip>/.well-known/add
```

The well-known URI convention (RFC 8615) allows AI agents and automated tools to probe a fixed, predictable location for machine-readable metadata without prior knowledge of the device's URL structure. This endpoint MUST return the same ADD document as `/add`, or redirect to it with an HTTP 301 or 302 response.

Implementing all three endpoints is recommended for devices intended for broad or public deployment — it ensures the ADD document is reachable regardless of which discovery method an AI system uses first.

---

### 5.5 Session Timeout

Devices with resource constraints — such as microcontrollers with limited concurrent connection capacity — MAY implement a session timeout mechanism. If a session timeout is in effect, the ADD description SHOULD indicate the remaining session time and the maximum number of session extensions available, so the AI can manage its interaction within the available window.

---
## 6. The AI Reading Process

When an AI agent retrieves an ADD document, it does not read it from top to bottom in arbitrary order. The reading sequence is defined — and the reason is not convenience, but safety.

### 6.1 Why the Reading Order Matters

An ADD document describes a physical device that an AI can act upon. Some of those actions may be irreversible. Some may affect other people. Some may carry risk if executed without proper constraints in place. Before the AI reads what the device can do and how to do it, it must know what ethical obligations apply to this deployment — and those obligations must be active before any action is even considered.

This is why the `autonomy` block is always read first, and why the Ethical Framework it references must be loaded and applied before the AI proceeds to any other block. The reading order is a safety requirement, not a formatting convention.

---

### 6.2 The Reading Sequence

An AI system reading an ADD document MUST follow this sequence:

**Step 1 — Verify document integrity**
Read `schema`, `version`, and `spec_url`. Confirm that this is a valid ADD document at a known version. If the document structure is unrecognizable or the version is unsupported, stop and inform the user.

**Step 2 — Determine the risk profile**
Read the `autonomy` block. Identify the declared Autonomy Level and the three factor scores. These scores give immediate context for the risk profile of this deployment — before any device details are read.

**Step 3 — Load the Ethical Framework**
Fetch the Ethical Framework document at `autonomy.ethic_url`. Apply it as required by the declared level. Only after the framework is active may the AI proceed to read the rest of the document.

**Step 4 — Read the device description**
Read `device`, `security`, `interfaces`, `actions`, and `rules` in order. At this point the AI has the ethical context it needs to interpret these blocks correctly — recognizing which actions require confirmation, which constraints must never be violated, and which rules reflect the deployment context the device author intended.

**Step 5 — Check the validation record**
Read the `validation` block. An AI encountering a document with `status: "not_validated"` SHOULD treat it with additional caution and SHOULD prompt the user to validate before relying on it for autonomous operation.

---

### 6.3 If the Ethical Framework Cannot Be Fetched

Network conditions, device constraints, or temporary unavailability may prevent the AI from loading the Ethical Framework at `ethic_url`. The required response depends on the Autonomy Level:

| Level | If `ethic_url` is unreachable |
|---|---|
| **1 — Basic** | The Basic framework rules are minimal and well-known. Apply them from memory and proceed. |
| **2 — Standard** | Apply Level 1 rules as a minimum fallback. Inform the user. Proceed with caution. |
| **3 — Full** | Do NOT proceed. Inform the user. Wait for explicit user authorization before each individual action. |

The stricter the level, the stricter the fallback. A Level 3 deployment — with wide action space, irreversible actions, or multi-person impact — must not operate without its full Ethical Framework in place. No exceptions.

---

### 6.4 If the ADD Document Conflicts with the Ethical Framework

If any instruction in the ADD document — in the `rules` block or elsewhere — conflicts with the loaded Ethical Framework, the Ethical Framework takes precedence. Always.

This is not a theoretical edge case. A device author may write a rule that is locally reasonable but ethically problematic in a broader context. The Ethical Framework is the higher authority — it defines the non-negotiable boundaries within which all ADD rules operate.

---

### 6.5 The Ethical Framework — Adaptable, but Not a Guarantee

The Ethical Framework is not a fixed, immutable document. Because it is hosted at a URL — referenced by every ADD document that uses it — it can be updated, replaced, or customized. This is intentional. Different countries operate under different legal frameworks. Different organizations have different compliance requirements. Different use cases carry different risk profiles. A framework that works for a home irrigation valve may not be appropriate for a medical device or an industrial control system. The `ethic_url` field allows device authors to point to any framework document — the ADD-provided defaults, an organization-specific version, or a jurisdiction-specific adaptation.

This flexibility is a feature. But it comes with a responsibility that must be stated clearly.

**The Ethical Framework is not a guaranteed last line of defense.** It is designed to prevent unintentional harm — to catch errors, oversights, and edge cases that a device author did not anticipate when writing the ADD document. It constrains an AI that is acting in good faith but may be missing context. It does not constrain an AI that has been deliberately configured to cause harm.

A device author who writes a malicious ADD document, points to a permissive or manipulated Ethical Framework, and deploys an AI agent with destructive intent can cause serious harm — and the framework will not stop them. An AI operating under a compromised or absent Ethical Framework can become unpredictable and dangerous in ways that are difficult to contain after the fact.

ADD is a tool. Like any powerful tool, it can be misused. The specification provides the structure for responsible use — but it cannot enforce the intent of the people who deploy it. Responsibility for safe and ethical deployment lies with the device author, the operator, and ultimately the humans who build and use AI agents. The framework supports good intent. It cannot replace it, and it cannot enforce it.

---
## 7. What an AI Agent Can Do with ADD

An AI agent that has read an ADD document — and loaded the applicable Ethical Framework — has everything it needs to interact with the device correctly, safely, and autonomously.

---

### 7.1 Reading and Acting

The most fundamental action is reading the current device state. Before acting, the AI reads first. After acting, it reads again to verify the result. Reading is always safe — it changes nothing on the device.

Beyond reading, the AI can execute the operations the device has declared as permitted. It does not guess what is possible — the device told it. Every action comes with constraints the AI must respect, and some actions require explicit user confirmation before they can be executed. The AI proposes; the human decides.

---

### 7.2 Following Rules

The device author's knowledge of the deployment context reaches the AI through the rules block — plain-language instructions that define how the AI must behave beyond what technical parameters can express. When to ask before acting. When not to act even if technically possible. How to handle unexpected situations.

Rules are binding. The AI does not treat them as suggestions. And two rules always take precedence over everything else: load the Ethical Framework before acting, and let it resolve any conflict.

---

### 7.3 Handling Uncertainty

An AI agent acting on a physical device will encounter situations the ADD document did not explicitly anticipate. ADD defines a clear response for each case: consult the specification when something is ambiguous, consult the device documentation when behavior is unexpected, stop and ask the user when a situation cannot be resolved within the defined scope.

The AI is not expected to be omniscient. It is expected to act within its defined scope and escalate when it reaches the boundary — exactly as a skilled human operator would.

---

### 7.4 The Scope of AI Action

ADD defines what an AI may do with a specific device — not what the AI does with the information it collects, how it coordinates across multiple devices, or what broader goals it pursues. Those are the responsibility of the agent's task definition.

What ADD guarantees is that whatever the agent does with this device, it does so within the boundaries the device author defined. The scope of action is bounded, transparent, and auditable. This is the foundation of trustworthy AI-device interaction: not a black box that does whatever it can, but a bounded agent that does exactly what was agreed — no more, and no less.

---
## 8. Why a Fixed Top-Level Schema?

Before describing the schema in detail, it is worth stating clearly why it is designed the way it is — and why the top-level structure is fixed while the content within each block is free-form.

### 8.1 The Design Principle: Opinionated Core, Flexible Extensions

ADD follows a single governing design principle: **"Opinionated Core, Flexible Extensions."**

The top-level structure is fixed and stable. Every ADD document — regardless of device type, protocol, domain, or complexity — contains exactly the same seven top-level blocks. This is not a limitation. It is a deliberate choice that makes ADD useful across the full diversity of IoT devices without requiring a constantly growing standard.

What lives inside each block is entirely the responsibility of the device author. There are no prescribed field names, no required data models, no enumerated protocol lists. A developer describes their device the way they would explain it to a technically competent colleague — and the AI interprets it semantically.

The seven top-level blocks are the irreducible minimum for an AI-usable device description. They are designed to be stable: changes to the top-level schema constitute a breaking change and require a major version increment, while changes to the content within blocks — which is intentionally free-form — do not affect the schema version at all. An ADD document written today will be structurally valid for any future AI system that implements ADD v1.x.

---

### 8.2 Why the Core Must Be Fixed

The fixed top-level structure serves one purpose: **guaranteeing that an AI agent always has the minimum information it needs to act, without having to search for it or ask.**

Each of the seven blocks answers a question the AI must be able to answer before interacting with any device:

| Block | Question |
|---|---|
| `autonomy` | What risk profile does this deployment have, and which Ethical Framework applies? |
| `device` | What is this device and what does it do? |
| `security` | In what environment does it operate, and who enforces safety? |
| `interfaces` | How do I communicate with it? |
| `actions` | What am I permitted to do, and with what constraints? |
| `rules` | What behavioral instructions must I follow? |
| `validation` | Has this description been verified to be AI-interpretable? |

If any of these blocks is missing, the AI cannot act safely. Without `autonomy`, it cannot determine what ethical obligations apply. Without `security`, it cannot assess the risk of its actions. Without `actions`, it does not know what is permitted. A description that omits any of these blocks is incomplete by definition — and an incomplete description is not a safe basis for autonomous action.

The fixed structure enforces completeness. It ensures that a device author cannot accidentally produce an ADD document that leaves the AI without the context it needs.

---

### 8.3 Why the Extensions Must Be Flexible

The content within each block is intentionally free-form for an equally important reason: **no fixed schema can anticipate the full diversity of IoT devices.**

A simple irrigation valve needs only a handful of fields. A marine navigation system with NMEA 0183 and NMEA 2000 interfaces, dozens of data streams, and complex safety constraints needs a much richer description. A device that speaks a proprietary binary protocol over serial needs to describe that in its own terms — terms that no enumerated protocol list could capture in advance.

If ADD prescribed the content of each block, it would either be too narrow for complex devices or too verbose for simple ones. It would need constant revision as new device types and protocols emerge. And it would place an implementation burden on device authors that defeats the purpose of a lightweight, accessible standard.

By leaving the content free-form, ADD delegates the descriptive work to the people who know their devices best — the device authors — and delegates the interpretive work to the AI, which is well suited to understanding semantically rich, structurally diverse descriptions. This division of responsibility is what makes ADD simultaneously minimal and powerful.

---

This stability is a feature that device authors and AI developers can rely on.
## 9. The Top-Level Schema

Every ADD document is a JSON object with a fixed set of top-level fields. This is the complete structure:

```json
{
  "schema":       "add",
  "version":      "1.0",
  "spec_url":     "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1.0",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
  "autonomy":     { ... },
  "device":       { ... },
  "security":     { ... },
  "interfaces":   [ ... ],
  "actions":      [ ... ],
  "rules":        [ ... ],
  "validation":   { ... }
}
```

---

### 9.1 Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema` | string | yes | Must be `"add"` — identifies this as an ADD document |
| `version` | string | yes | ADD schema version, e.g. `"1.0"` |
| `spec_url` | string | yes | URL of the authoritative ADD specification for this version |
| `spec_license` | string | yes | License and attribution of the ADD specification |
| `autonomy` | object | yes | Risk profile and link to the applicable Ethical Framework (→ Section 10.1) |
| `device` | object | yes | Device identity and metadata (→ Section 10.2) |
| `security` | object | yes | Security context and enforcement policy (→ Section 10.3) |
| `interfaces` | array | yes | Available communication interfaces (→ Section 10.4) |
| `actions` | array | yes | Operations the AI may perform (→ Section 10.5) |
| `rules` | array | yes | Behavioral instructions for the AI (→ Section 10.6) |
| `validation` | object | yes | Result of the most recent AI-based validation (→ Section 10.7) |

---

### 9.2 The Header Fields

The four fields above the seven blocks form the document header. They identify the document, link it to its specification, and carry attribution information.

**`schema`** must always be `"add"`. This allows any AI system or tool to immediately recognize the document type without reading further.

**`version`** identifies the ADD schema version the document conforms to, using semantic versioning. An AI system that does not support the declared version SHOULD inform the user and SHOULD NOT proceed until the version compatibility is confirmed.

**`spec_url`** links the document to the authoritative specification it is based on. This serves two purposes: if the AI encounters an unknown field, an ambiguous instruction, or an unexpected structure, it SHOULD fetch the specification at this URL and use it to resolve the ambiguity before proceeding. The URL SHOULD point to the specific version of the specification — not the latest version — to ensure consistent interpretation over time. The following standard rule SHOULD always be present in the `rules` block:

```
"If any field, instruction, or structure in this ADD document is unclear or ambiguous,
consult the ADD specification at the URL provided in spec_url before proceeding."
```

**`spec_license`** is mandatory. The ADD specification is published under the Creative Commons Attribution 4.0 International (CC BY 4.0) license, which requires that the author be credited in any use or adaptation of the work. Including `spec_license` in every ADD document fulfills this attribution requirement directly — the origin and authorship of the specification are embedded in the document itself, visible to any AI system or human reader without requiring them to follow the `spec_url` link. For documents based on this specification, the correct value is:

```
"CC BY 4.0 — © 2026 Norbert Walter"
```

---
## 10. The Blocks in Detail

Each of the seven top-level blocks is described in this section. For each block: its purpose, its fields, and a concrete example.

---

### 10.1 The `autonomy` Block

**Purpose:** The `autonomy` block declares the risk profile of this deployment and links to the applicable Ethical Framework document. It is the first block an AI system reads — before any device description, interface, or action. Without it, the AI cannot determine what ethical obligations apply and must refuse to proceed.

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | Autonomy Level: 1 (Basic), 2 (Standard), or 3 (Full) |
| `scores.reversibility` | integer | yes | 0 = fully reversible, 1 = manual correction needed, 2 = irreversible actions possible |
| `scores.scope_of_effect` | integer | yes | 0 = owner only, 1 = occasional effect on others, 2 = regular effect on third parties |
| `scores.error_tolerance` | integer | yes | 0 = hours to correct, 1 = minutes, 2 = seconds — too fast for human intervention |
| `ethic_url` | string | yes | URL of the Ethical Framework document applicable to this level |
| `ethic_core` | object | yes (Level 1 only) | Inline minimal rule set for Level 1 deployments — see below |

**Example (Level 2 — irrigation valve):**

```json
"autonomy": {
  "level": 2,
  "scores": {
    "reversibility":   1,
    "scope_of_effect": 1,
    "error_tolerance": 0
  },
  "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1.0"
}
```

---

**Autonomy Levels — how the level is determined**

The Autonomy Level is derived from the sum of the three factor scores. Each factor is scored 0, 1, or 2:

**Factor 1 — Reversibility:** *What happens if the AI makes a wrong decision?*

| Score | Condition |
|---|---|
| 0 | All actions are immediately and fully reversible |
| 1 | Some actions require manual correction but cause no permanent damage |
| 2 | Irreversible actions are possible — wrong decisions may cause permanent damage |

**Factor 2 — Scope of Effect:** *Who is affected by the actions this device enables?*

| Score | Condition |
|---|---|
| 0 | Actions affect only the device owner |
| 1 | Actions occasionally affect other people in the same household or building |
| 2 | Actions regularly affect people who have not explicitly consented, or affect shared infrastructure |

**Factor 3 — Error Tolerance:** *How much time is available to recognize and correct a mistake?*

| Score | Condition |
|---|---|
| 0 | Hours to days — errors are noticed and corrected before consequences develop |
| 1 | Minutes to hours — regular monitoring is required to catch errors in time |
| 2 | Seconds — human reaction time is too slow to intervene once an error occurs |

**Level determination:**

| Total Score | Autonomy Level |
|---|---|
| 0–1 | **Level 1 — Basic** |
| 2–3 | **Level 2 — Standard** |
| 4–6 | **Level 3 — Full** |

**Practical examples:**

| Application | Reversibility | Scope | Error Tolerance | Score | Level |
|---|---|---|---|---|---|
| Read-only temperature sensor | 0 | 0 | 0 | 0 | **1 — Basic** |
| Garden irrigation valve | 1 | 1 | 0 | 2 | **2 — Standard** |
| Room heating control | 1 | 1 | 0 | 2 | **2 — Standard** |
| Full home automation (comfort only) | 1 | 1 | 1 | 3 | **2 — Standard** |
| Home automation with locks and alarms | 1 | 2 | 1 | 4 | **3 — Full** |
| Industrial process valve | 2 | 1 | 2 | 5 | **3 — Full** |
| Medical device | 2 | 2 | 2 | 6 | **3 — Full** |

Note: home automation moves from Level 2 to Level 3 when it includes access control, security systems, or gas appliances — because the scope and irreversibility increase.

---

**What each level requires:**

**Level 1 — Basic**
Appropriate for narrow-purpose devices with fully reversible actions and single-user impact. The `autonomy` block MUST include an `ethic_core` field with a minimal inline rule set. The `ethic_url` points to the Basic framework for reference, but loading it is optional — the inline rules are sufficient for Level 1 operation. Any AI model capable of reading and applying the inline rules is appropriate, including small local or embedded models.

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

**Level 2 — Standard**
Appropriate for multi-function devices with semi-autonomous operation and occasional effect on others. The AI MUST fetch and apply the Ethical Framework summary at `ethic_url` before operating. A model capable of fetching and applying a short document alongside its operational task is required — authors should validate with the intended model.

**Level 3 — Full**
Appropriate for wide action spaces, irreversible actions, multi-person impact, or rapid consequences. The AI MUST fetch and internalize the complete Ethical Framework at `ethic_url` before any action. If the framework cannot be loaded, the AI MUST NOT proceed. Frontier-class or near-frontier models are required. Authors MUST validate with the specific intended model and record the result in `validated_by`.

**The three Ethical Framework documents:**

| Level | Document at `ethic_url` |
|---|---|
| 1 — Basic | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0` |
| 2 — Standard | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1.0` |
| 3 — Full | `https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1.0` |

The Autonomy Level is declared by the device author and verified independently by the AI during validation. If the AI's assessment differs from the declared level, it MUST report this as a finding and recommend the higher level. Under-declaration — intentional or accidental — must not pass validation unchallenged.

---
### 10.2 The `device` Block

**Purpose:** The `device` block describes the identity and context of the device. It tells the AI what this device is, where it is, and where to find more information when the ADD document alone is not sufficient.

**Fields** (all free-form, none mandatory — include what is meaningful for your device):

| Field | Description |
|---|---|
| `name` | Human-readable device name |
| `id` | Unique device identifier |
| `type` | Device category: `sensor`, `actuator`, `gateway`, or any meaningful value |
| `manufacturer` | Manufacturer or project name |
| `firmware` | Firmware version |
| `hardware` | Hardware platform or revision |
| `location` | Physical or logical location of the device |
| `doc_url` | URL of the device documentation, datasheet, or manual |
| `doc_url_note` | Short hint pointing the AI to the most relevant section of the documentation |

`doc_url` provides a reference the AI can consult when device behavior is unclear or unexpected from the ADD document alone. This is particularly valuable for devices with complex state machines, proprietary protocols, or domain-specific data formats. The AI SHOULD fetch this URL when it encounters behavior or parameters not adequately described in the ADD document.

`doc_url_note` narrows the search — it tells the AI where in potentially long documentation to look first, preventing it from having to scan an entire manual for a single answer. For example: `"See chapter 3 for timing behavior and chapter 5 for error codes."`

If `doc_url` is present, the following standard rule SHOULD be added to the `rules` block:
```
"If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding."
```

**Example:**
```json
"device": {
  "name": "Garden Irrigation Valve",
  "type": "actuator",
  "location": "Garden, main water supply",
  "firmware": "V1.4",
  "hardware": "ESP8266",
  "doc_url": "https://example.com/irrigation-valve/manual",
  "doc_url_note": "See chapter 3 for valve timing behavior and chapter 5 for error codes."
}
```

---

### 10.3 The `security` Block

**Purpose:** The `security` block describes the security context in which the device operates and defines who is responsible for enforcing safety constraints. It tells the AI what environment to assume and what it can rely on.

**Fields** (all free-form, none mandatory — include what is meaningful for your device):

| Field | Description |
|---|---|
| `network_scope` | Allowed network scope: `local`, `vpn`, `internet` |
| `authentication` | Authentication mechanism: `none`, `basic`, `token`, or other |
| `remote_access` | Whether remote access is permitted (`true`/`false`) |
| `enforcement` | How the device enforces constraints independently of the AI |

ADD is designed for devices operating in already-secured network environments. Security responsibility is divided across three layers:

- **The network environment** handles transport-level access control: firewalls, VLANs, VPNs, WiFi authentication.
- **The AI system** follows the behavioral rules in the `rules` block: confirmation requirements, value range checks, forbidden actions.
- **The device itself** is the last line of defense. It MUST enforce all safety constraints independently. If any client — AI or otherwise — sends a request that violates defined constraints, the device MUST reject it. The device MUST NOT rely solely on the AI to enforce safety.

The `enforcement` field is the device author's declaration of this last layer. A well-written enforcement description gives the AI confidence that out-of-range values and unauthorized commands will be rejected by the device regardless of what the AI does — and that the AI is not the only safeguard.

Exposing ADD endpoints over the public internet requires additional measures beyond this specification — TLS, strong authentication, and firewall rules at minimum.

**Example:**
```json
"security": {
  "network_scope": "local",
  "remote_access": false,
  "authentication": "none",
  "enforcement": "The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input."
}
```

---

### 10.4 The `interfaces` Block

**Purpose:** The `interfaces` block describes the communication interfaces the device exposes — how the AI can talk to it. Each entry in the array describes one interface. The content is entirely free-form: any protocol, any transport, any structure may be described.

**Recommended fields per interface** (none mandatory):

| Field | Description |
|---|---|
| `name` | Interface identifier — used to reference this interface from the `actions` block |
| `physical` | Physical medium: `WiFi`, `Ethernet`, `RS485`, etc. |
| `protocol` | Application protocol: `HTTP`, `MQTT`, `NMEA0183`, `Modbus`, or any other |
| `transport` | Transport protocol: `TCP`, `UDP`, etc. |
| `port` | Network port |
| `direction` | `read`, `write`, or `bidirectional` |
| `data` | Description of data provided or consumed on this interface |

ADD does not enumerate or restrict the protocols that may be described in the `interfaces` block. A device that speaks NMEA 0183 over a serial TCP bridge describes it here in plain language — the AI interprets it semantically and knows how to use it. A device with multiple interfaces — HTTP for configuration, MQTT for streaming data — lists each as a separate entry in the array.

The AI does not need the interface to match a known schema. It needs enough information to understand the communication method and use it correctly. A well-written interface description gives the AI exactly that — even for protocols it has never been explicitly trained on.

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
      { "name": "state",   "path": "/json",    "method": "GET" },
      { "name": "control", "path": "/control", "method": "POST" }
    ]
  }
]
```

---

### 10.5 The `actions` Block

**Purpose:** The `actions` block defines exactly what an AI is permitted to do with the device. Each entry describes one operation: how to invoke it, what parameters it accepts, and how the AI should behave before and after executing it.

**Recommended fields per action** (none mandatory):

| Field | Description |
|---|---|
| `name` | Action identifier |
| `description` | Human-readable description of what the action does |
| `interface` | Which interface to use (references a `name` in the `interfaces` block) |
| `method` | HTTP method or protocol equivalent |
| `path` | Endpoint path |
| `parameters` | Parameters the action accepts, with type, range, and constraints |
| `safe` | `true` if the action is read-only and has no lasting effect |
| `reversible` | `true` if the action can be undone |
| `idempotent` | `true` if repeated execution produces the same result |
| `requires_confirmation` | `true` if the AI must obtain explicit user approval before executing |
| `requires_auth` | `true` if authentication is required |
| `timing` | `"critical"` if this action must be executed without delay — omit if not time-sensitive |
| `max_response_time` | Maximum acceptable response time in seconds — only meaningful when `timing` is `"critical"` |

The three flags `safe`, `reversible`, and `requires_confirmation` define the risk profile of each action and determine how the AI must behave:

- A `safe` action is read-only. The AI may execute it at any time without confirmation.
- A `reversible` action changes device state but can be undone. The AI may execute it autonomously when the rules permit, but must verify the result and be prepared to reverse it.
- An action with `requires_confirmation: true` must not be executed without explicit user approval — regardless of how confident the AI is. This is the primary mechanism for keeping the human in the loop for consequential actions.

If `timing` is `"critical"` and `max_response_time` is defined, the AI must execute this action within the specified time. If it cannot — due to model latency, network conditions, or resource availability — it must immediately alert the user and stop. A missing `timing` field means no time constraint applies — the AI acts at its own pace.

Parameter constraints — `min`, `max`, allowed `values` — are enforced by the AI before sending any request. The AI does not rely on the device to reject out-of-range values, even if the device would do so independently.

**Example — mixed timing:**
```json
"actions": [
  {
    "name": "open_valve",
    "description": "Open the irrigation valve for a specified duration in minutes. Maximum 60 minutes.",
    "interface": "http_json",
    "method": "POST",
    "path": "/control",
    "parameters": {
      "state":    { "type": "string",  "values": ["open"] },
      "duration": { "type": "integer", "min": 1, "max": 60, "unit": "minutes" }
    },
    "safe": false,
    "reversible": true,
    "requires_confirmation": true
  },
  {
    "name": "emergency_close",
    "description": "Close the valve immediately in case of emergency. No confirmation required.",
    "interface": "http_json",
    "method": "POST",
    "path": "/control",
    "parameters": {
      "state": { "type": "string", "values": ["closed"] }
    },
    "safe": false,
    "reversible": true,
    "requires_confirmation": false,
    "timing": "critical",
    "max_response_time": 10
  }
]
```

---

### 10.6 The `rules` Block

**Purpose:** The `rules` block contains behavioral instructions addressed directly to the AI. Rules encode everything that cannot be expressed in structured fields alone: when to ask the user, when not to act, how to handle ambiguous situations, and what constraints the deployment context imposes beyond the technical parameters.

The `rules` block is an array. Each entry is either a plain string or a structured object. Plain strings are sufficient for most rules. Structured objects are used when a rule has resource requirements or timing constraints that the AI needs to know explicitly.

**Plain string rule:**
```json
"Do not open the valve between 22:00 and 05:00."
```

**Structured rule object:**

| Field | Description |
|---|---|
| `instruction` | The rule text — same as a plain string rule |
| `requires` | Resources this rule depends on — the AI must have access to these to apply the rule |
| `timing` | `"critical"` if this rule must be evaluated and acted upon without delay |
| `max_response_time` | Maximum acceptable response time in seconds — only meaningful when `timing` is `"critical"` |

If `requires` lists a resource the AI does not have access to, it must inform the user that this rule cannot be enforced and ask for guidance. If `timing` is `"critical"` and the AI cannot respond within `max_response_time`, it must alert the user immediately.

**The first two rules are mandatory in every ADD document and MUST appear at positions 1 and 2:**

```json
"rules": [
  "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
  "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
  ...
]
```

**Standard rules recommended for every ADD document:**

```json
"rules": [
  "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
  "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
  "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
  "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
  "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
  "Always confirm with the user before executing any action that is not safe or not reversible.",
  "Verify the result of every write action by reading the device state afterward.",
  "Do not set parameter values outside the defined min/max range."
]
```

**Example — mixed plain and structured rules:**
```json
"rules": [
  "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
  "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
  "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
  "Always confirm with the user before opening the valve.",
  {
    "instruction": "Do not open the valve if rain is forecast within the next 24 hours.",
    "requires": ["weather_api"]
  },
  {
    "instruction": "Do not open the valve if the garden is in use.",
    "requires": ["calendar_api", "home_automation"]
  },
  "Do not open the valve between 22:00 and 05:00.",
  {
    "instruction": "Close the valve immediately if a flood sensor alert is received.",
    "requires": ["home_automation"],
    "timing": "critical",
    "max_response_time": 10
  }
]
```

The standard rules follow a deliberate sequence: load the Ethical Framework → resolve conflicts → consult the specification → consult the device documentation → follow device-specific instructions. This order ensures the most fundamental constraints are always active before any device-specific logic is applied.

**Rule 1 — Load:** An explicit action instruction. Without this rule, an AI could read the `autonomy` block and proceed without loading the framework — because JSON field order does not imply execution order. The rule makes the loading step mandatory and unambiguous.

**Rule 2 — Precedence:** Defines how to resolve conflicts between ADD rules and the Ethical Framework. This rule only activates when a conflict is encountered — Rule 1 ensures the framework is loaded so the conflict can be recognized at all.

The `doc_url` rule (rule 4) is only meaningful if `device.doc_url` is present. If no documentation URL is provided, this rule SHOULD be omitted.

Device-specific rules follow the standard rules and encode the deployment context: time windows, conditions under which the AI must not act, confirmation requirements beyond what the `actions` block specifies, and any other behavioral constraints the device author deems necessary. These rules are the most important part of a well-written ADD document — they are what transform a technically correct AI action into a contextually appropriate one.

---

### 10.7 The `validation` Block

**Purpose:** The `validation` block records the result of the most recent AI-based validation of this ADD document. It serves two purposes: it is a structured record for the device author of what was tested and what was found, and it is a trust signal for any AI system that reads the document — allowing it to immediately assess the document's quality without repeating the full validation.

An ADD document without a completed `validation` block SHOULD be treated by AI systems as unvalidated and handled with additional caution.

**Top-level fields:**

| Field | Type | Description |
|---|---|---|
| `validated_by` | array | One entry per AI model that performed validation — each with its own complete result |
| `add_version` | string | ADD schema version validated against |
| `improvements_applied` | array | Improvements made to the ADD document as a result of validation |

**Fields per `validated_by` entry — one per AI model:**

| Field | Type | Description |
|---|---|---|
| `name` | string | AI model name |
| `version` | string | AI model version |
| `validated_at` | string | ISO 8601 timestamp of this model's validation |
| `status` | string | This model's result: `"passed"`, `"passed_with_warnings"`, or `"failed"` |
| `score` | object | Per-category scores for this model: `"pass"`, `"warning"`, or `"fail"` |
| `findings` | array | Findings from this model with `severity`, `category`, `message`, and `resolved` |
| `summary` | string | Plain-text summary of this model's validation result |

**Score categories:**

| Category | What is assessed |
|---|---|
| `structure` | Completeness and correctness of the core schema |
| `comprehensibility` | Clarity and unambiguity of the description |
| `functional` | Correct behavior of interfaces and actions during testing |
| `rules_compliance` | AI correctly interpreted and followed all rules |
| `security` | Security context clearly defined and enforced |
| `discovery` | Discovery mechanism correctly implemented |
| `timing_compliance` | AI met all `max_response_time` requirements for critical actions and rules — `"pass"` if no timing requirements are present |

**Why validation is per model:**

Because ADD sub-schemas are intentionally free-form, there is no generic schema validator for ADD documents. The only meaningful test is whether the AI that will actually use the document can read, understand, and act upon it correctly. Every validation result is specific to the model that produced it — a document that passes with Claude Sonnet is not automatically valid for GPT-5 or Qwen3-3B. Different models interpret the same description differently: a large frontier model may successfully infer intent from a loosely worded description; a smaller model may fail on the same text.

The `validated_by` array is therefore a **compatibility matrix**: it records which models have been tested, what each found, and whether the document works for that model. A device author who wants to support three different AI systems must validate with all three and record each result separately.

The device author bears final responsibility. The AI performs the test and surfaces findings — the author reviews, applies corrections, and releases the document.

**Example — three models, different results:**
```json
"validation": {
  "add_version": "1.0",
  "improvements_applied": [
    "Added cache-buster rule for read requests.",
    "Clarified enforcement field to state the 60-minute limit is enforced by the device independently."
  ],
  "validated_by": [
    {
      "name": "Claude",
      "version": "claude-sonnet-4-5",
      "validated_at": "2026-04-27T07:15:00Z",
      "status": "passed_with_warnings",
      "score": {
        "structure":         "pass",
        "comprehensibility": "pass",
        "functional":        "pass",
        "rules_compliance":  "pass",
        "security":          "warning",
        "discovery":         "pass",
        "timing_compliance": "pass"
      },
      "findings": [
        {
          "severity": "warning",
          "category": "security",
          "message": "No authentication configured. Acceptable for trusted home network — document as conscious design decision.",
          "resolved": false
        }
      ],
      "summary": "Well-structured document. All actions behaved as described. Device correctly rejected out-of-range duration. Security warning noted. Suitable for deployment."
    },
    {
      "name": "GPT",
      "version": "gpt-5",
      "validated_at": "2026-04-27T08:00:00Z",
      "status": "passed",
      "score": {
        "structure":         "pass",
        "comprehensibility": "pass",
        "functional":        "pass",
        "rules_compliance":  "pass",
        "security":          "pass",
        "discovery":         "pass",
        "timing_compliance": "pass"
      },
      "findings": [],
      "summary": "All tests passed. Document is clear and unambiguous. Ready for deployment."
    },
    {
      "name": "Qwen",
      "version": "qwen3.5-3b",
      "validated_at": "2026-04-27T08:30:00Z",
      "status": "failed",
      "score": {
        "structure":         "pass",
        "comprehensibility": "warning",
        "functional":        "fail",
        "rules_compliance":  "warning",
        "security":          "pass",
        "discovery":         "pass",
        "timing_compliance": "pass"
      },
      "findings": [
        {
          "severity": "error",
          "category": "functional",
          "message": "Model attempted to send duration=120, ignoring the max:60 constraint. Parameter constraints were not reliably applied.",
          "resolved": false
        },
        {
          "severity": "warning",
          "category": "rules_compliance",
          "message": "Model did not consistently check rain forecast before opening valve. Rule was acknowledged but not applied in all test cases.",
          "resolved": false
        }
      ],
      "summary": "Model too small to reliably interpret this Level 2 document. Parameter constraints and conditional rules were not consistently followed. Use the small-model optimized version (irrigation-valve-standard-small.json) for this model size."
    }
  ]
}
```

---
## 11. Workflow: From Device to Deployed ADD Document

Creating an ADD document follows three phases. Each phase has a clear purpose, a defined output, and a human decision point before the next phase begins. The device author is present and in control at every transition — the AI does the analytical and drafting work, the human reviews, corrects, and approves.

```
Phase 1 — Authoring
  AI explores the device and produces a draft ADD document
  Device author reviews and approves
        ↓
Phase 2 — Validation
  AI tests the draft against the live device and reports findings
  Device author applies corrections and approves for deployment
        ↓
Phase 3 — Deployment
  Completed ADD document served at /add on the device
  Any AI agent can discover and use it immediately
```

**Phase 1 — Authoring** is described in detail in Chapter 12, including the authoring prompt and the limits of what AI can determine from network access alone.

**Phase 2 — Validation** is described in detail in Chapter 13, including the validation prompt and the criteria for a deployment-ready document.

**Phase 3 — Deployment** is simple: the completed ADD document in JSON format is served at the `/add` endpoint on the device's HTTP server. Optionally, a `llms.txt` file and a `/.well-known/add` endpoint are added for broader discoverability (see Chapter 5). From this point, any AI agent that can reach the device can discover, read, and act upon it — without any further configuration or setup.

---
## 12. Authoring an ADD Document with AI

### 12.1 Why AI Authoring Makes Sense

Writing an ADD document manually is possible — but doing it with AI assistance is significantly better, for a reason that is easy to overlook.

A device author who knows their hardware intimately often carries implicit knowledge that never makes it into a manually written description, because it is obvious to them. An AI authoring assistant has no such prior knowledge. It can only work with what it can observe: the device's web interface, its HTTP responses, its visible controls and parameters. This forces the description to be explicit where a human author might leave gaps, and surfaces ambiguities early — before they become problems during validation or deployment.

There is a second reason. An AI that authors an ADD document is practicing the same skill it will later need to use the document: reading device interfaces, inferring intent, and mapping observations to structured descriptions. The authoring process is therefore also an early compatibility test between the device and the AI — if the AI struggles to understand the device well enough to describe it, that is a signal that the description needs to be clearer before deployment.

The device author bears full responsibility for the final document. The AI produces a draft and asks clarifying questions; the author reviews, corrects, and approves. Nothing is published without the author's explicit decision.

---

### 12.2 The Authoring Workflow

**Phase 1 — Device Exploration**

The AI reads the ADD specification, then systematically explores the device: it retrieves the HTML source of the web interface, identifies visible controls and input fields, discovers API endpoints by examining links and JavaScript, makes HTTP GET requests to discovered endpoints, and analyzes the responses. It maps everything it finds to the seven ADD blocks.

**Phase 2 — Clarification Dialogue**

The AI identifies what it cannot determine from observation alone and asks the device author targeted questions — one at a time, waiting for each answer before continuing:

- What is the primary purpose of this device?
- Which actions should require explicit user confirmation before execution?
- Are there parameter ranges or constraints not visible in the interface?
- In what network environment does the device operate?
- Who is responsible for enforcing safety constraints — the device, the AI, or both?
- Are there protocols or interfaces beyond HTTP that the AI should know about?
- Are there behaviors or actions the AI must never perform on this device?

**Phase 3 — Draft Production**

The AI produces a complete, syntactically valid ADD document with all mandatory blocks filled in. Where it has made assumptions it cannot verify from observation alone, it flags them inline:

```
"// ASSUMPTION: duration maximum assumed to be 60 minutes based on web interface label — please verify"
```

After producing the draft, the AI provides a short summary: what it determined from direct observation, what required clarification, which fields are uncertain and need careful review, and what should be tested first during validation.

---

### 12.3 The Authoring Prompt

The following prompt initiates an AI-based ADD authoring session. Replace the placeholders before use.

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
   schema, version, spec_url, spec_license, autonomy, device, security,
   interfaces, actions, rules, validation

   For the validation block, use an empty `validated_by` array and set
   `add_version` to the current ADD schema version.

   Where you have made assumptions due to incomplete information, add an inline
   comment directly after the relevant field in the following format:
   "// ASSUMPTION: [what you assumed and why — please verify]"

4. After producing the draft, provide a short summary:
   - What could you determine from direct observation?
   - What required clarification from me?
   - Which fields are uncertain and should be reviewed carefully before validation?
   - What should be tested first during validation?
```

---

### 12.4 Reviewing the Draft

The output of the authoring process is a starting point, not a finished document. Before proceeding to validation, the device author SHOULD review every field carefully, with particular attention to:

- **Assumptions flagged by the AI** — these are the highest-risk fields and must be verified against actual device behavior before the document is trusted
- **The `rules` block** — the AI proposes rules based on what it observed, but only the author knows the true behavioral constraints of the deployment context; rules that seem reasonable in the abstract may be incomplete or incorrect for the specific use case
- **The `actions` block** — parameter ranges, confirmation requirements, and safety classifications must be accurate; errors here directly affect AI behavior during operation
- **The `security` block** — network scope, authentication, and enforcement responsibilities must reflect the actual deployment environment
- **The `autonomy` block** — the declared level must honestly reflect the risk profile; the AI will independently verify this during validation, but it is better to get it right from the start

Once the author is satisfied that the draft accurately reflects the device and its intended deployment context, it proceeds to validation.

---

### 12.5 The Limits of AI-Based Authoring

AI-based authoring is powerful, but it has a fundamental constraint that every device author must understand: **the AI can only analyze what it can access over the network.**

The AI's view of the device is limited to what is reachable via HTTP and the protocols running on top of it. It can read HTML, send GET and POST requests, analyze JSON responses, and observe the data the device returns. This is sufficient to discover endpoints, understand data structures, and map the visible interface to an ADD document.

What the AI cannot see is everything that happens below the network layer:

- **Physical hardware behavior** — GPIO pins, relay states, analog inputs, hardware timers, watchdog circuits, and any other microcontroller I/O that is not exposed through a network interface
- **Firmware internals** — state machines, interrupt handlers, timing behavior, and device logic that operates independently of network requests
- **Hardware safety mechanisms** — overcurrent protection, thermal cutoffs, mechanical limits, and other physical safeguards that the device enforces at the hardware level
- **Side effects of actions** — physical consequences that are not reflected in the device's HTTP responses, such as a valve that takes several seconds to fully open after the command is acknowledged
- **Environmental context** — where the device is installed, what it is connected to physically, and what happens in the real world when it acts

All of this knowledge lives with the device author, not with the AI. The clarification dialogue in Phase 2 is the mechanism for transferring it — but only if the author actively supplies it. An AI that is not told about a hardware safety limit will not include it in the ADD document. An AI that is not told about a physical side effect will not add a rule to handle it.

This is why the device author's review of the draft is not a formality. The AI produces the best description it can from what it can observe. The author fills in what the AI cannot reach. Together, they produce a description that is both technically accurate and contextually complete.

---
## 13. Validating an ADD Document with AI

### 13.1 Why AI Validation Is the Only Meaningful Test

Because ADD sub-schemas are intentionally free-form, there is no generic schema validator for ADD documents. A classical parser can check whether JSON is syntactically correct — but it cannot determine whether the description is clear enough for an AI to act upon correctly, whether the rules are complete, or whether the device actually behaves as described.

The only meaningful test is this: **can the AI system that will use this document read it, understand the device, and interact with it correctly and safely?**

This is why validation is performed by AI systems — the same ones that will later operate the device. The guiding question is not "does this document conform to a schema?" but "does this AI understand this device well enough to act on it?"

One practical consequence: an ADD document validated with one AI system cannot be assumed to work equally well with another. A large model may successfully infer intent from a loosely worded description; a smaller or more constrained model may not. If a document is intended for use with multiple AI systems, it SHOULD be validated separately with each — and all results recorded in `validated_by`.

---

### 13.2 What Validation Covers

A complete validation covers six areas:

**Structure and Completeness**
All mandatory top-level fields are present and correctly set. The `spec_url` points to a reachable specification document. No mandatory block is missing or empty.

**Comprehensibility**
The AI can describe the device in its own words after reading the document. It correctly identifies all interfaces, actions, parameters, constraints, and rules. Any ambiguous or unclear descriptions are identified and flagged.

**Functional Testing**
The AI performs live test interactions with the device: reading current state, executing valid write actions and verifying the results, attempting out-of-range parameter values to confirm the device rejects them, and testing confirmation flows for non-safe actions and the cache-buster mechanism if defined in the rules.

**Rules Compliance**
The AI correctly interprets and follows all rules. Confirmation requirements are respected. Network scope and authentication requirements are recognized. The `spec_url` disambiguation rule is present and reachable.

**Security Review**
The AI identifies which actions could be misused, flags missing or ambiguous security-relevant rules, verifies that the device enforces its own constraints independently, and proposes concrete improvements for any identified weaknesses.

**Response Time**
If the ADD document defines `timing: "critical"` and `max_response_time` on any action or rule, the AI measures its actual response time for those actions during validation and compares it against the defined limit. This test reflects real operating conditions — network latency, model load, and resource availability all affect response time. A model that passes all other validation areas but fails timing requirements is not safe to deploy for that device. The result is recorded in `timing_compliance`. If no timing requirements are present, `timing_compliance` is set to `"pass"`.

---

### 13.3 The Validation Prompt

The following prompt initiates an AI-based ADD validation session. Replace the placeholders before use.

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
   - If any action or rule defines `timing: "critical"` and `max_response_time`:
     measure your actual response time for that action and compare it against
     the defined limit. Report whether you met the requirement, and if not,
     report the actual time observed as an error finding.

5. After testing, provide a security review:
   - Which actions or interfaces could be misused?
   - Are there any missing or ambiguous rules?
   - Does the device correctly enforce its own constraints independently?
   - Are there any security weaknesses in the ADD document itself?
   - What concrete improvements do you recommend?

6. Independently evaluate the Autonomy Level of this ADD document:
   - Score each of the three factors (Reversibility, Scope of Effect, Error Tolerance)
     with 0, 1, or 2, based on the actions and rules in the document
   - Calculate the total score and determine the resulting Autonomy Level (1, 2, or 3)
   - Compare your assessment with the level declared by the author in the autonomy block
   - If your assessment is higher than the declared level, report this as an error
     finding and recommend the correct level — do not accept an under-declared level

7. Produce a completed validation block in JSON format, ready to be inserted into
   the ADD document. Include all required fields: validated_by, validated_at,
   add_version, score, findings, improvements_applied, and summary.
   Score categories to include: structure, comprehensibility, functional,
   rules_compliance, security, discovery, and timing_compliance.
   Set timing_compliance to "pass" if no timing requirements are present in
   the document, otherwise report the actual test result.
   Provide a final assessment:
   - What works well?
   - What needs improvement?
   - Is the Autonomy Level correctly declared?
   - Were all timing requirements met?
   - Is the ADD document ready for deployment?
```

---

### 13.4 Writing the Validation Result into the Document

After completing the validation, the AI produces a completed `validation` block in JSON format. The device author:

1. Reviews the block and all findings
2. Applies any remaining improvements to the ADD document
3. Updates the `resolved` flags for findings that have been addressed
4. Inserts the completed `validation` block into the ADD document
5. Publishes the document at the `/add` endpoint

An ADD document is **deployment-ready** when:
- `validation.status` is `"passed"` or `"passed_with_warnings"`
- All findings with `severity: "error"` have `resolved: true`
- The `summary` clearly states the document is suitable for deployment

---

### 13.5 When to Re-Validate

Validation is not a one-time event. The document SHOULD be re-validated after:

- Significant changes to the ADD document — new actions, modified rules, updated security context
- Changes to the device firmware that affect its behavior or interfaces
- Switching to a different AI system for operation
- Any finding from operation that suggests the AI misunderstood the document

Each re-validation run is recorded in `validated_by` with the AI system name, version, and timestamp. Over time, this array becomes a transparent history of which AI systems have been tested with this document and what they found.

---
## 14. Versioning

### 14.1 The ADD Schema Version

The ADD schema version is declared in the top-level `version` field of every ADD document. This specification defines **ADD core schema v1.0**.

Versioning follows [Semantic Versioning](https://semver.org/):

| Version component | Meaning |
|---|---|
| **Major** | Breaking changes to the top-level schema structure — existing documents may no longer be valid |
| **Minor** | Backward-compatible additions to the core schema — existing documents remain valid |
| **Patch** | Clarifications and corrections to the specification text — no structural changes |

Changes to the content within blocks — within `device`, `interfaces`, `actions`, `rules`, and `security` — do not affect the ADD schema version. These sub-schemas are intentionally free-form and evolve independently of the specification version.

---

### 14.2 Version Traceability

The `spec_url` field MUST point to the specific version of the specification the document was written against — not the latest version. This ensures that an AI system reading the document can always consult the exact specification the author used, even if newer versions have been published since.

```
"spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1.0"
```

An AI system that encounters a `version` field it does not recognize SHOULD inform the user and SHOULD NOT proceed with autonomous operation until version compatibility is confirmed.

---

### 14.3 Versioning and the Workflow

From a workflow perspective, the version field is relevant at two points:

**During authoring:** The device author specifies the version of the specification they are working against. The `spec_url` points to that version. Both remain stable for the lifetime of the document unless the document is updated to a newer schema version.

**During validation:** The `validation` block records the ADD schema version validated against in the `add_version` field. If the document is later updated to conform to a newer schema version, it SHOULD be re-validated and the `add_version` field updated accordingly.

---
## 15. Governance

ADD is an open specification. Contributions, implementations, and feedback are welcome.

The specification is intentionally kept minimal. Proposals to add mandatory fields to the core schema will be evaluated conservatively — flexibility and simplicity take precedence over completeness. The core schema changes only when there is a compelling reason that cannot be addressed through free-form block content.

Contributions to this specification must be consistent with the ADD Ethical Framework. Proposals that would make ADD easier to use for purposes explicitly prohibited in the Ethical Framework will not be accepted, regardless of their technical merit.

---

*ADD Core Specification v1.0*
*© 2026 Norbert Walter — Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)*
*https://creativecommons.org/licenses/by/4.0/*

*You are free to use, implement, share, and adapt this specification for any purpose, including commercial use, provided that appropriate credit is given to the original author.*

*The author makes no patent claims over any part of this specification and grants all implementers a royalty-free, irrevocable right to implement it without restriction.*

*Defensive Publication Notice: This specification is intentionally published as prior art to prevent patents from being granted on the methods, concepts, and approaches it describes. The public disclosure date of this document establishes prior art for all methods described herein. Any attempt to patent the methods described in this specification is contrary to the intent of this publication.*
