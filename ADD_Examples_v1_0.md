# ADD – AI Device Description
## Example Collection v1.0
*© 2026 Norbert Walter — CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/*

---

## Introduction

This document provides a collection of ADD examples spanning the full range of device types, deployment contexts, and Autonomy Levels. Each example shows how ADD is applied in a concrete scenario — what decisions are made, why a specific Autonomy Level is chosen, and what an AI agent can do with the resulting description.

The examples are organized by deployment context, from private home use to critical public infrastructure. They are intended as orientation for device authors who want to create their own ADD documents, and as demonstration for anyone who wants to understand the practical scope of ADD.

**How to read the examples:**

Each example follows the same structure:
- **Device & Context** — what the device is and where it is deployed
- **Autonomy Level** — the three factor scores with justification
- **Key Rules** — the most important device-specific behavioral rules
- **AI Agent Scenario** — what a concrete AI agent interaction looks like
- **ADD Document** — the complete ADD document

**Autonomy Level quick reference:**

| Score Sum | Level |
|---|---|
| 0–1 | **1 — Basic** — narrow purpose, fully reversible, single user |
| 2–3 | **2 — Standard** — semi-autonomous, occasional effect on others |
| 4–6 | **3 — Full** — wide scope, irreversible actions, or multi-person impact |

---

## Part 1 — Private Use

### Example 1 — Indoor Temperature and Humidity Sensor

**Device & Context**

A small ESP32-based sensor mounted in a living room, measuring temperature and humidity every 60 seconds and publishing readings via HTTP. The device has no actuators — it can only report data. It is used by a home automation system to decide when to activate heating or ventilation.

**Autonomy Level — Level 1 (Basic)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 0 | Read-only device — no actions, nothing to reverse |
| Scope of Effect | 0 | Data affects only the device owner's home automation |
| Error Tolerance | 0 | A wrong reading causes a delayed or missed heating cycle — hours to notice |
| **Total** | **0** | **Level 1 — Basic** |

The `ethic_core` inline rules are sufficient. No external Ethical Framework fetch required.

**Key Rules**
- Always append a cache-buster timestamp to all read requests
- If readings appear implausible (temperature outside –10°C to +60°C, humidity outside 0–100%), report the anomaly and do not use the value for decisions
- Do not attempt to write to this device — it is read-only

**AI Agent Scenario**

The home automation agent reads temperature and humidity every 5 minutes. If temperature drops below 19°C, it activates the heating via a separate thermostat device. If humidity exceeds 70%, it opens a ventilation valve. The sensor ADD document tells the agent exactly what the data means, what units are used, and what plausible value ranges look like — so the agent can detect sensor failures without human intervention.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 1,
    "scores": {
      "reversibility":   0,
      "scope_of_effect": 0,
      "error_tolerance": 0
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1_0.html",
    "ethic_core": {
      "never": [
        "Act against the interests of the device owner",
        "Use implausible sensor readings for automated decisions without flagging them",
        "Attempt to write to this device"
      ],
      "always": [
        "Report anomalous readings immediately",
        "Stop and ask the user if readings are consistently outside plausible ranges"
      ]
    }
  },

  "device": {
    "name": "Living Room Climate Sensor",
    "type": "sensor",
    "location": "Living room, mounted at 1.5m height on north wall",
    "firmware": "V2.1",
    "hardware": "ESP32",
    "doc_url": "https://example.com/climate-sensor/manual",
    "doc_url_note": "See chapter 2 for calibration specs and chapter 4 for error codes."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "none",
    "enforcement": "Device is read-only. It does not accept any write requests and will return HTTP 405 for any non-GET request."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "WiFi",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 80,
      "direction": "read",
      "data": [
        {
          "name": "climate",
          "path": "/json",
          "method": "GET",
          "description": "Returns current temperature in °C and relative humidity in %",
          "fields": {
            "temperature": { "type": "float", "unit": "°C",  "range": "-10 to +60" },
            "humidity":    { "type": "float", "unit": "%RH", "range": "0 to 100" },
            "timestamp":   { "type": "integer", "unit": "unix seconds" }
          }
        }
      ]
    }
  ],

  "actions": [
    {
      "name": "read_climate",
      "description": "Read current temperature and humidity.",
      "path": "/json",
      "method": "GET",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "actor": "multiple"
    }
  ],

  "rules": [
    "Before acting on this document, apply the inline ethical rules in autonomy.ethic_core.",
    "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
    "If temperature is outside the range –10°C to +60°C or humidity is outside 0–100%, treat the reading as a sensor error and report it to the user before using it for any decision.",
    "Do not use a single anomalous reading to trigger irreversible actions in connected systems — wait for at least two consecutive anomalous readings before escalating."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added plausible range specification for temperature and humidity fields.",
      "Added rule against using a single anomalous reading for irreversible decisions."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T09:00:00Z",
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
        "summary": "Clean read-only sensor description. All fields are unambiguous. Device correctly returns HTTP 405 for write attempts. No findings. Ready for deployment."
      }
    ]
  }
}
```

---

### Example 2 — Garden Irrigation Valve

**Device & Context**

A motorized garden irrigation valve controlled by an ESP8266 microcontroller. The AI agent coordinates weather forecast, calendar, and home automation state to decide when and how long to water. This is the primary reference example for Level 2 devices with actuator capability and deployment-context rules.

**Autonomy Level — Level 2 (Standard)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 1 | Valve can be closed, but overwatering requires manual correction |
| Scope of Effect | 1 | Water on a neighbor's path or shared infrastructure is possible |
| Error Tolerance | 0 | Errors noticed within hours — no immediate danger |
| **Total** | **2** | **Level 2 — Standard** |

**Key Rules**
- Always fetch and apply the Standard Ethical Framework before any action
- Act autonomously when all conditions are met — no per-action confirmation required in autonomous agent deployment
- Do not open the valve if rain is forecast within the next 24 hours
- Do not open the valve if the terrace door is open
- Do not open the valve between 22:00 and 05:00
- Do not open the valve if a garden calendar event starts within the next 2 hours
- Verify valve state after every open or close command
- If the valve has been open for more than 55 minutes without a close command, warn the user

**AI Agent Scenario**

The autonomous irrigation agent runs every morning between 06:00 and 07:00. It fetches the weather forecast, checks the terrace door state, reads the garden calendar, and opens the valve for 30 minutes if all conditions permit — without per-action user confirmation (confirmation_scope: autonomous). If any condition is not met, it reports the reason and exits. The user is notified of every session outcome.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 2,
    "scores": {
      "reversibility":   1,
      "scope_of_effect": 1,
      "error_tolerance": 0
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Garden Irrigation Valve",
    "type": "actuator",
    "ip": "192.168.1.93",
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
        { "name": "state",   "path": "/json",    "method": "GET" },
        { "name": "control", "path": "/control", "method": "POST" }
      ]
    }
  ],

  "actions": [
    {
      "name": "open_valve",
      "description": "Open the irrigation valve for 1–60 minutes. Device enforces the limit independently.",
      "interface": "http_json",
      "method": "POST",
      "path": "/control",
      "parameters": {
        "state":    { "type": "string",  "values": ["open"], "required": true },
        "duration": { "type": "integer", "min": 1, "max": 60, "unit": "minutes", "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": false,
      "requires_confirmation": false,
      "confirmation_scope": "autonomous",
      "actor": "single"
    },
    {
      "name": "close_valve",
      "description": "Close the irrigation valve immediately.",
      "interface": "http_json",
      "method": "POST",
      "path": "/control",
      "parameters": {
        "state": { "type": "string", "values": ["closed"], "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "confirmation_scope": "autonomous",
      "actor": "single"
    },
    {
      "name": "read_state",
      "description": "Read current valve state, remaining open duration if active, and total water volume dispensed today.",
      "interface": "http_json",
      "method": "GET",
      "path": "/json",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "actor": "multiple"
    }
  ],

  "rules": [
    "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
    "Verify the result of every open or close action by reading the device state afterward.",
    "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
    "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
    "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
    "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present.",
    {
      "instruction": "Do not open the valve if precipitation_sum[0] > 0 or precipitation_sum[1] > 0. Fetch from https://api.open-meteo.com/v1/forecast?latitude=51.33&longitude=7.04&daily=precipitation_sum&forecast_days=2",
      "requires": ["fetch_url"]
    },
    {
      "instruction": "Do not open the valve if the terrace door sensor reports state = open.",
      "requires": ["home_automation"]
    },
    {
      "instruction": "Do not open the valve if a calendar event with location containing 'garden' starts within the next 2 hours.",
      "requires": ["calendar_api"]
    },
    "Do not open the valve between 22:00 and 05:00.",
    "Do not open the valve for more than 60 minutes in a single session.",
    "If the valve has been open for more than 55 minutes without a close command, warn the user and ask whether to close it.",
    "Act autonomously when all rules can be verified and all conditions permit. Stop and alert the user when a required tool is unavailable, a rule cannot be verified, or an unexpected device response occurs."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added cache-buster rule for read requests.",
      "Added warning rule for sessions exceeding 55 minutes.",
      "Added actor field to all actions.",
      "Added autonomous confirmation scope for agent deployment."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T09:15:00Z",
        "status": "passed_with_warnings",
        "tools_required": ["fetch_url", "calendar_api", "home_automation"],
        "tools_fingerprint": "calendar_api|fetch_url|home_automation",
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
            "message": "No authentication configured. Any client on the local network can open the valve. Acceptable for a trusted home network.",
            "resolved": false
          }
        ],
        "summary": "All actions behaved as described. Autonomous confirmation scope verified. External resource rules applied correctly. Security warning noted — acceptable for home deployment.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---
---

## Part 2 — Commercial Use

### Example 3 — Workshop Dust Extraction System

**Device & Context**

A motorized dust extraction unit in a small woodworking workshop, controlled via a WiFi-enabled relay module. The system can be switched on and off remotely and reports its current operating state and filter pressure. High filter pressure indicates a clogged filter that must be replaced before continued operation — running with a clogged filter risks motor damage and fire.

**Autonomy Level — Level 2 (Standard)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 1 | Switching off is safe; switching on with a clogged filter risks motor damage |
| Scope of Effect | 1 | Fire risk affects the building and potentially neighbors |
| Error Tolerance | 0 | Filter pressure rises slowly — hours to notice and correct |
| **Total** | **2** | **Level 2 — Standard** |

**Key Rules**
- Never switch on the extraction unit if filter pressure exceeds 80% of maximum — report the condition and instruct the user to replace the filter first
- Always read current state and filter pressure before switching on
- If the unit switches off unexpectedly during operation, do not restart automatically — report the event and wait for user instruction
- Always confirm with the user before switching on

**AI Agent Scenario**

A workshop automation agent monitors the extraction unit and the connected power tools. When a tool is activated, the agent checks filter pressure, confirms it is within safe range, and switches on the extraction unit automatically — or blocks the tool activation and alerts the user if the filter needs replacement. At the end of the working day, it switches off the extraction unit and reports the total operating hours since the last filter change.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 2,
    "scores": {
      "reversibility":   1,
      "scope_of_effect": 1,
      "error_tolerance": 0
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Workshop Dust Extraction Unit",
    "type": "actuator",
    "ip": "192.168.1.50",
    "location": "Workshop, rear wall",
    "firmware": "V3.2",
    "hardware": "ESP32 with relay",
    "doc_url": "https://example.com/dust-extractor/manual",
    "doc_url_note": "See chapter 5 for filter pressure limits and chapter 7 for error codes."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "none",
    "enforcement": "The device will not accept a start command if internal filter pressure sensor reads above 90% of maximum. The motor has a thermal cutoff that activates independently at 85°C."
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
        { "name": "state",   "path": "/json",    "method": "GET" },
        { "name": "control", "path": "/control", "method": "POST" }
      ]
    }
  ],

  "actions": [
    {
      "name": "start_extraction",
      "description": "Start the dust extraction motor. Do not start if filter pressure exceeds 80%.",
      "interface": "http_json",
      "method": "POST",
      "path": "/control",
      "parameters": { "state": { "type": "string", "values": ["on"], "required": true } },
      "safe": false,
      "reversible": true,
      "idempotent": false,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "actor": "single"
    },
    {
      "name": "stop_extraction",
      "description": "Stop the dust extraction motor immediately.",
      "interface": "http_json",
      "method": "POST",
      "path": "/control",
      "parameters": { "state": { "type": "string", "values": ["off"], "required": true } },
      "safe": false,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "confirmation_scope": "per_action",
      "actor": "single"
    },
    {
      "name": "read_state",
      "description": "Read current motor state, filter pressure (0–100%), and operating hours since last filter change.",
      "interface": "http_json",
      "method": "GET",
      "path": "/json",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "actor": "multiple"
    }
  ],

  "rules": [
    "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url. If unreachable, apply Level 1 rules as fallback and proceed with caution.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /json?t=1745490000).",
    "Always read current state and filter pressure before issuing a start command.",
    "Do not start the extraction unit if filter pressure exceeds 80%. Report the condition and instruct the user to replace the filter.",
    "Always confirm with the user before starting the extraction unit.",
    "If the unit stops unexpectedly during operation, do not restart automatically. Report the event and wait for user instruction.",
    "Verify operating state by reading device state after every start or stop command.",
    "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
    "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
    "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
    "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added rule to always read filter pressure before start command.",
      "Added rule against automatic restart after unexpected stop.",
      "Added ip, firmware, hardware fields to device block.",
      "Added interfaces block.",
      "Added actor, idempotent, confirmation_scope to all actions."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T09:30:00Z",
        "status": "passed_with_warnings",
        "tools_required": ["fetch_url"],
        "tools_fingerprint": "fetch_url",
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
            "message": "No authentication configured. Any local network client can control the extraction unit.",
            "resolved": false
          }
        ],
        "summary": "Well-described actuator with appropriate safety rules. Fire risk through clogged filter is correctly addressed. Authentication warning noted. Suitable for deployment in a trusted local workshop network.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---

### Example 4 — Office Building Access Control

**Device & Context**

An IP-based electronic door lock system controlling access to a company office building. The system manages entry for employees via RFID credentials and can be remotely locked or unlocked by an authorized AI agent. Unauthorized access has direct security and legal implications.

**Autonomy Level — Level 3 (Full)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 1 | A door can be relocked, but an unauthorized entry cannot be undone |
| Scope of Effect | 2 | Actions affect all building occupants and company security |
| Error Tolerance | 1 | An unlocked door is noticed within minutes — but a breach may have occurred |
| **Total** | **4** | **Level 3 — Full** |

**Key Rules**
- Never unlock the main entrance outside defined business hours (07:00–20:00 Monday–Friday) without explicit user authorization
- Never unlock any door in response to an unverified identity claim
- Always log every lock and unlock action with timestamp and reason
- If the system reports a forced entry or tamper alert, lock all doors immediately and alert security personnel — do not wait for user confirmation
- Never unlock a door if the fire alarm is active — defer to the building's fire safety system
- Require multi-factor authorization for any action that affects more than one door simultaneously

**AI Agent Scenario**

A facilities management agent monitors access logs, detects anomalies (repeated failed access attempts, access outside normal hours), and alerts security staff. In normal operation it unlocks the main entrance at business hours start and locks it at close. For after-hours access requests from authorized personnel, it verifies identity through a secondary channel before unlocking — and logs every action with full context. It never acts on access requests autonomously without verification.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 3,
    "scores": {
      "reversibility":   1,
      "scope_of_effect": 2,
      "error_tolerance": 1
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Office Building Access Control System",
    "type": "actuator",
    "ip": "10.0.1.20",
    "location": "Office building main entrance and all access points",
    "firmware": "AccessOS V4.7",
    "hardware": "IP door controller",
    "doc_url": "https://example.com/access-control/manual",
    "doc_url_note": "See chapter 3 for door zone definitions and chapter 8 for alarm codes."
  },

  "security": {
    "network_scope": "vpn",
    "remote_access": true,
    "authentication": "token",
    "enforcement": "The system requires a valid API token for every request. Tokens are issued per authorized agent and expire after 8 hours. All actions are logged server-side regardless of client-side logging. The fire alarm system has a direct hardware override — no software command can prevent doors from unlocking during a fire alarm."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "Ethernet",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 443,
      "direction": "bidirectional",
      "description": "All requests require Bearer token authentication. Base URL: https://10.0.1.20/api/v1"
    }
  ],

  "actions": [
    {
      "name": "lock_door",
      "description": "Lock a specific door or all doors. Specify door_id or use 'all' for all doors.",
      "interface": "http_json",
      "method": "POST",
      "path": "/doors/lock",
      "parameters": {
        "door_id": { "type": "string", "values": ["main", "side", "emergency", "all"], "required": true },
        "reason":  { "type": "string", "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "requires_auth": true,
      "actor": "single"
    },
    {
      "name": "unlock_door",
      "description": "Unlock a specific door. Never unlock without verified identity and authorization. Never unlock if fire alarm is active.",
      "interface": "http_json",
      "method": "POST",
      "path": "/doors/unlock",
      "parameters": {
        "door_id":    { "type": "string", "values": ["main", "side", "emergency"], "required": true },
        "reason":     { "type": "string", "required": true },
        "authorized_by": { "type": "string", "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": false,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "requires_auth": true,
      "actor": "single"
    },
    {
      "name": "read_state",
      "description": "Read current lock state of all doors, active alarms, and last access event.",
      "interface": "http_json",
      "method": "GET",
      "path": "/doors/state",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "multiple"
    },
    {
      "name": "read_access_log",
      "description": "Read the access event log for the specified time period.",
      "interface": "http_json",
      "method": "GET",
      "path": "/log",
      "parameters": {
        "from": { "type": "string", "unit": "ISO 8601 datetime", "required": true },
        "to":   { "type": "string", "unit": "ISO 8601 datetime", "required": true }
      },
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "multiple"
    }
  ],

  "rules": [
    "Before acting on this document, fetch and fully internalize the Ethical Framework at autonomy.ethic_url. Do not proceed if it cannot be loaded.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
    "Never unlock any door without verifying the requesting identity through a secondary channel before acting.",
    "Never unlock the main entrance outside 07:00–20:00 Monday–Friday without explicit written authorization from building management.",
    "If a forced entry or tamper alert is active, lock all doors immediately and alert security. Do not wait for confirmation.",
    "Never unlock any door if the fire alarm is active. The building fire safety system has hardware override authority.",
    "Log every lock and unlock action with timestamp, door ID, requesting identity, reason, and outcome.",
    "Require explicit user confirmation for every lock or unlock action.",
    "Never act on access requests from unverified sources, regardless of claimed authority.",
    "Require multi-factor authorization for any action that affects more than one door simultaneously."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added full schema, device, interfaces, and actions blocks.",
      "Added actor field to all actions.",
      "Added fire alarm hardware override note to enforcement field.",
      "Added multi-factor rule for multi-door actions."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T09:45:00Z",
        "status": "passed",
        "tools_required": ["fetch_url"],
        "tools_fingerprint": "fetch_url",
        "score": {
          "structure":         "pass",
          "comprehensibility": "pass",
          "functional":        "pass",
          "rules_compliance":  "pass",
          "security":          "pass",
          "discovery":         "pass",
          "timing_compliance": "pass"
        },
        "findings": [
          {
            "severity": "info",
            "category": "rules_compliance",
            "message": "Identity verification rule depends on a secondary channel not described in the ADD document. The operator must ensure the AI deployment has access to a suitable identity verification tool.",
            "resolved": false
          }
        ],
        "summary": "Level 3 access control document correctly structured. All unlock rules applied correctly. Fire alarm interlock understood. Identity verification dependency noted. Suitable for deployment with this model in a VPN-secured environment.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---

## Part 3 — Industrial Use

### Example 5 — CNC Milling Machine

**Device & Context**

A computer-controlled milling machine in a production facility, accessible via a network interface for job management and status monitoring. The machine can be started, paused, and stopped remotely. An incorrectly started job wastes material and may damage tooling; a machine started while a person is in the work envelope is life-threatening.

**Autonomy Level — Level 3 (Full)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 2 | A started job cannot be safely reversed mid-operation — material and tooling may be damaged or destroyed |
| Scope of Effect | 2 | Operating personnel and bystanders in the production area are at direct physical risk |
| Error Tolerance | 2 | A spindle at 20,000 RPM leaves no time for human intervention |
| **Total** | **6** | **Level 3 — Full** |

**Key Rules**
- Never start a machining job without explicit confirmation from the machine operator on-site
- Never start a job if the safety door is open or the work envelope light curtain is interrupted
- Never override a safety interlock for any reason
- If the machine enters an error state during operation, stop immediately and alert the operator — do not attempt to resume automatically
- Never load or start a job file that has not been verified by the operator
- Always confirm that the correct tool and workpiece are loaded before starting

**AI Agent Scenario**

A production planning agent manages the job queue, monitors machine utilization, and alerts maintenance when tool wear thresholds are reached. It can load a verified job file to the machine and prepare it for execution — but the final start command always requires the on-site operator to confirm via a physical button press or a verified two-factor authentication. The agent never starts a job autonomously, regardless of queue urgency.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 3,
    "scores": {
      "reversibility":   2,
      "scope_of_effect": 2,
      "error_tolerance": 2
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "CNC Milling Machine",
    "type": "actuator",
    "ip": "192.168.10.5",
    "location": "Production facility, hall B, workstation 3",
    "firmware": "CNC Controller V8.4",
    "hardware": "Industrial CNC controller",
    "doc_url": "https://example.com/cnc-mill/manual",
    "doc_url_note": "See chapter 4 for safety interlock descriptions, chapter 6 for job file format, and chapter 9 for error codes."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "token",
    "enforcement": "The machine controller enforces all safety interlocks independently. No network command can override a hardware safety interlock. Emergency stop is hardware-only and cannot be disabled via software. The safety door interlock cuts power to the spindle drive independently of any software state."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "Ethernet",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 8080,
      "direction": "bidirectional",
      "description": "All requests require Bearer token authentication. Returns JSON status objects."
    }
  ],

  "actions": [
    {
      "name": "read_state",
      "description": "Read current machine state: power, spindle status, safety door state, active interlocks, loaded job file, and alarm codes.",
      "interface": "http_json",
      "method": "GET",
      "path": "/status",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "multiple"
    },
    {
      "name": "load_job",
      "description": "Load a verified, operator-approved job file to the machine. The job file must be pre-approved by the operator before loading.",
      "interface": "http_json",
      "method": "POST",
      "path": "/job/load",
      "parameters": {
        "job_id":       { "type": "string", "required": true },
        "approved_by":  { "type": "string", "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": false,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "requires_auth": true,
      "actor": "single"
    },
    {
      "name": "start_job",
      "description": "Start the loaded machining job. Requires explicit on-site operator confirmation via physical button press or verified two-factor authentication. Never start if safety door is open or any interlock is active.",
      "interface": "http_json",
      "method": "POST",
      "path": "/job/start",
      "parameters": {
        "operator_confirmed": { "type": "boolean", "values": [true], "required": true },
        "confirmation_method": { "type": "string", "values": ["physical_button", "2fa"], "required": true }
      },
      "safe": false,
      "reversible": false,
      "idempotent": false,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "requires_auth": true,
      "actor": "single"
    },
    {
      "name": "stop_job",
      "description": "Stop the current machining job immediately. Use for controlled stop only — for emergencies use the physical emergency stop button.",
      "interface": "http_json",
      "method": "POST",
      "path": "/job/stop",
      "safe": false,
      "reversible": false,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "single"
    }
  ],

  "rules": [
    "Before acting on this document, fetch and fully internalize the Ethical Framework at autonomy.ethic_url. Do not proceed if it cannot be loaded.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always read machine state before any action. Never act on assumed state.",
    "Never start a machining job without explicit on-site operator confirmation via physical button press or verified two-factor authentication.",
    "Never start a job if the safety door is open or any safety interlock is active.",
    "Never attempt to override, bypass, or disable any safety interlock for any reason whatsoever.",
    "If the machine enters an error or alarm state, stop all activity and alert the operator immediately. Never attempt automatic recovery.",
    "Never load a job file that has not been explicitly approved by the operator — the approved_by field must contain a verifiable operator identity.",
    "Before issuing a start_job command, verify that the correct tool and workpiece are loaded as specified in the job file.",
    "Verify machine state after every command. If the state does not match the expected result, stop and alert the operator."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added full schema, device, interfaces, and actions blocks.",
      "Added actor and confirmation_scope fields to all actions.",
      "Added explicit confirmation method parameter to start_job.",
      "Added hardware safety door note to enforcement field."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T10:00:00Z",
        "status": "passed",
        "tools_required": ["fetch_url"],
        "tools_fingerprint": "fetch_url",
        "score": {
          "structure":         "pass",
          "comprehensibility": "pass",
          "functional":        "pass",
          "rules_compliance":  "pass",
          "security":          "pass",
          "discovery":         "pass",
          "timing_compliance": "pass"
        },
        "findings": [
          {
            "severity": "info",
            "category": "rules_compliance",
            "message": "Physical button confirmation cannot be verified by the AI — the operator must ensure the confirmation_method parameter is set correctly by the calling system.",
            "resolved": false
          }
        ],
        "summary": "Level 3 maximum-score device correctly structured. All safety interlock rules applied correctly. start_job correctly blocked when safety door open in test scenario. Confirmation requirement enforced. Suitable for deployment as a job management assistant — never as an autonomous control system.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---

## Part 4 — Public and Social Infrastructure

### Example 6 — Hospital Bed Monitoring System

**Device & Context**

A networked monitoring unit attached to a hospital bed, measuring patient vital parameters — heart rate, respiratory rate, and bed occupancy — and transmitting them to the nursing station. The device is read-only from the AI perspective. Incorrect readings or missed alerts can have direct consequences for patient safety.

**Autonomy Level — Level 2 (Standard)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 0 | Read-only — no actions to reverse |
| Scope of Effect | 2 | Patient safety depends directly on correct data interpretation |
| Error Tolerance | 1 | An anomalous reading must be flagged within minutes — patient condition can change rapidly |
| **Total** | **3** | **Level 2 — Standard** |

Note: Although this is a read-only device, the scope of effect and error tolerance scores are elevated because incorrect AI interpretation of the data can lead to missed alerts with life-threatening consequences. Level 2 is appropriate — the risk lies not in the device's actions but in the AI's interpretation of its data.

**Key Rules**
- Never suppress, filter, or average away anomalous readings — report them immediately
- If any vital parameter crosses a threshold defined in the rules, alert nursing staff immediately — do not wait for confirmation
- If data transmission is interrupted for more than 60 seconds, treat it as a potential patient emergency and alert nursing staff
- Never use readings from this device as the sole basis for a clinical decision — always treat them as supporting information that requires human verification
- Always timestamp every reading with the device's reported timestamp, not the AI's local clock

**AI Agent Scenario**

A ward monitoring agent continuously reads vital parameters from all bed units and maintains a real-time dashboard for nursing staff. It detects trends — a gradually declining heart rate, irregular respiratory patterns — and alerts nursing staff before threshold values are reached. It never acts on the data autonomously beyond alerting; all clinical decisions remain with medical personnel.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 2,
    "scores": {
      "reversibility":   0,
      "scope_of_effect": 2,
      "error_tolerance": 1
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Hospital Bed Monitor Unit",
    "type": "sensor",
    "ip": "10.1.3.112",
    "location": "Ward 3B, Bed 12",
    "firmware": "BedMon V5.3",
    "hardware": "Medical IoT sensor unit",
    "doc_url": "https://example.com/bedmonitor/manual",
    "doc_url_note": "See chapter 4 for vital parameter ranges and chapter 6 for alarm threshold configuration."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "token",
    "enforcement": "Device is read-only from the network interface. It does not accept any write requests and will return HTTP 405 for any non-GET request. All data is transmitted over the hospital's secured internal network."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "Ethernet",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 443,
      "direction": "read",
      "data": [
        {
          "name": "vitals",
          "path": "/json",
          "method": "GET",
          "description": "Returns current heart rate (bpm), respiratory rate (breaths/min), bed occupancy (boolean), and device-reported timestamp (unix seconds)"
        }
      ]
    }
  ],

  "actions": [
    {
      "name": "read_vitals",
      "description": "Read current heart rate, respiratory rate, bed occupancy, and device timestamp. Use device-reported timestamp, not local AI time.",
      "interface": "http_json",
      "method": "GET",
      "path": "/json",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "multiple",
      "timing": "critical",
      "max_response_time": 5
    }
  ],

  "rules": [
    "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url. If unreachable, apply Level 1 rules as fallback and proceed with caution.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
    "Always use the device-reported timestamp for all readings, not local AI time.",
    "Never suppress, filter, or average anomalous readings. Report all readings as received.",
    {
      "instruction": "Alert nursing staff immediately if heart rate falls below 40 or exceeds 150 bpm, or if respiratory rate falls below 8 or exceeds 30 per minute.",
      "timing": "critical",
      "max_response_time": 30
    },
    {
      "instruction": "Alert nursing staff immediately if data transmission is interrupted for more than 60 seconds.",
      "timing": "critical",
      "max_response_time": 60
    },
    "Never use readings from this device as the sole basis for a clinical decision. Always present data as supporting information requiring human verification.",
    "Do not attempt to write to this device — it is read-only.",
    "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
    "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
    "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
    "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added full schema, ip, firmware, hardware, security, interfaces, and actions blocks.",
      "Added timing and max_response_time to alert rules.",
      "Added cache-buster rule.",
      "Added explicit read-only enforcement note."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T10:15:00Z",
        "status": "passed",
        "tools_required": [],
        "tools_fingerprint": "",
        "score": {
          "structure":         "pass",
          "comprehensibility": "pass",
          "functional":        "pass",
          "rules_compliance":  "pass",
          "security":          "pass",
          "discovery":         "pass",
          "timing_compliance": "pass"
        },
        "findings": [
          {
            "severity": "info",
            "category": "rules_compliance",
            "message": "Alert delivery depends on a nursing staff notification tool not described in this ADD document. The operator must ensure the AI deployment has access to a suitable alerting mechanism.",
            "resolved": false
          }
        ],
        "summary": "Read-only medical monitoring device correctly described. Alert rules applied correctly in test scenarios. Clinical decision support caveat understood and respected. Timing requirements verified. Suitable for deployment as a monitoring supplement — never as a replacement for direct clinical observation.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---

### Example 7 — Power Grid Distribution Switch

**Device & Context**

A remotely controlled switching unit in a regional power distribution network, capable of connecting or disconnecting grid segments. A wrong switching operation can cause widespread outages affecting thousands of households and businesses, damage grid infrastructure, or create safety hazards for maintenance personnel working on what they believe to be a de-energized line.

**Autonomy Level — Level 3 (Full)**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 1 | Switching can be reversed, but a fault caused by wrong switching sequence may require hours to diagnose and repair |
| Scope of Effect | 2 | Thousands of households and critical facilities (hospitals, water treatment) may be affected |
| Error Tolerance | 2 | A wrong switching operation during maintenance can endanger lives in seconds |
| **Total** | **5** | **Level 3 — Full** |

**Key Rules**
- Never switch without receiving and verifying an explicit switching order from the grid control center — including order number, timestamp, and authorizing operator ID
- Never switch if maintenance personnel are logged as working on the affected segment
- Always verify grid state before and after every switching operation
- If a switching operation produces an unexpected grid state, stop immediately and alert the control center — do not attempt corrective switching autonomously
- Never act on switching instructions received outside the established secure communication channel
- All switching operations must be logged with full context and transmitted to the control center in real time

**AI Agent Scenario**

A grid management agent assists the control center by monitoring switching unit status, verifying preconditions before each switching order, and executing verified orders. It cannot initiate a switching operation on its own — every action requires a formally issued switching order from the control center with verified operator authorization. After each operation, it verifies the resulting grid state and reports back. Any unexpected result triggers an immediate halt and escalation.

**ADD Document**

```json
{
  "schema": "add",
  "version": "1.0",
  "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
  "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",

  "autonomy": {
    "level": 3,
    "scores": {
      "reversibility":   1,
      "scope_of_effect": 2,
      "error_tolerance": 2
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Power Grid Distribution Switch — Node 7B",
    "type": "actuator",
    "ip": "10.20.7.11",
    "location": "Regional distribution substation, sector 7, switching bay B",
    "firmware": "GridControl V12.4",
    "hardware": "Industrial switching controller",
    "doc_url": "https://grid-internal.example/systems/node-7b/manual",
    "doc_url_note": "See chapter 2 for segment topology, chapter 5 for switching preconditions, and chapter 9 for alarm codes."
  },

  "security": {
    "network_scope": "vpn",
    "remote_access": true,
    "authentication": "token",
    "enforcement": "All switching commands require a cryptographically signed switching order. The device verifies the signature independently before executing any command. Commands without a valid signature are rejected and logged. The device maintains an independent audit log that cannot be modified or deleted via the network interface."
  },

  "interfaces": [
    {
      "name": "http_json",
      "physical": "Ethernet",
      "protocol": "HTTP",
      "transport": "TCP",
      "port": 443,
      "direction": "bidirectional",
      "description": "All requests require Bearer token and a cryptographically signed switching order for control actions. Base URL: https://10.20.7.11/api/v2"
    }
  ],

  "actions": [
    {
      "name": "read_grid_state",
      "description": "Read current switch position, segment voltages, load values, maintenance personnel status, and active alarms for all connected segments.",
      "interface": "http_json",
      "method": "GET",
      "path": "/state",
      "safe": true,
      "reversible": true,
      "idempotent": true,
      "requires_confirmation": false,
      "requires_auth": true,
      "actor": "multiple",
      "timing": "critical",
      "max_response_time": 5
    },
    {
      "name": "execute_switching_order",
      "description": "Execute a signed switching order from the grid control center. Requires order number, authorizing operator ID, and cryptographic signature. Never execute without verifying all preconditions.",
      "interface": "http_json",
      "method": "POST",
      "path": "/switch",
      "parameters": {
        "order_number":   { "type": "string", "required": true },
        "operator_id":    { "type": "string", "required": true },
        "segment_id":     { "type": "string", "required": true },
        "action":         { "type": "string", "values": ["connect", "disconnect"], "required": true },
        "signature":      { "type": "string", "required": true }
      },
      "safe": false,
      "reversible": true,
      "idempotent": false,
      "requires_confirmation": true,
      "confirmation_scope": "per_action",
      "requires_auth": true,
      "actor": "single",
      "timing": "critical",
      "max_response_time": 10
    }
  ],

  "rules": [
    "Before acting on this document, fetch and fully internalize the Ethical Framework at autonomy.ethic_url. Do not proceed if it cannot be loaded.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
    "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
    "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
    "Always read full grid state before executing any switching command. Verify all preconditions are met.",
    "Never execute a switching command without a formally issued, cryptographically signed switching order from the grid control center.",
    "Never switch if maintenance personnel are registered as working on the affected segment.",
    "If the post-switching grid state does not match the expected state, stop all activity immediately and alert the control center. Do not attempt corrective switching autonomously.",
    "Never accept switching instructions from any channel other than the established secure control center connection.",
    "Log every action with full context — order number, authorizing operator, timestamp, pre- and post-switch grid state — and transmit to the control center in real time."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Added full schema, device, interfaces, and actions blocks.",
      "Added timing and max_response_time to read and switch actions.",
      "Added actor field to all actions.",
      "Added independent audit log note to enforcement field."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T10:30:00Z",
        "status": "passed",
        "tools_required": ["fetch_url"],
        "tools_fingerprint": "fetch_url",
        "score": {
          "structure":         "pass",
          "comprehensibility": "pass",
          "functional":        "pass",
          "rules_compliance":  "pass",
          "security":          "pass",
          "discovery":         "pass",
          "timing_compliance": "pass"
        },
        "findings": [
          {
            "severity": "info",
            "category": "rules_compliance",
            "message": "Cryptographic signature verification of switching orders depends on a signing tool not described in this ADD document. The operator must ensure the AI deployment has access to a suitable signing and verification mechanism.",
            "resolved": false
          }
        ],
        "summary": "Level 3 high-consequence device correctly structured. Switching order verification rules applied correctly. Maintenance personnel check understood. Post-switch state verification enforced in test scenarios. Suitable for deployment as a verified-order execution assistant — never as an autonomous grid management system.",
        "capabilities": {
          "classification": "large",
          "max_rules_reliable": 15,
          "sequential_tool_calls": 5,
          "ethic_url_usable": true,
          "response_time_90p_simple_seconds": 4,
          "response_time_90p_complex_seconds": 28
        }
      }
    ]
  }
}
```

---

## Part 5 — Critical Infrastructure

### Example 8 — Nuclear Reactor Cooling Pump

**Device & Context**

A primary coolant circulation pump in a nuclear power plant, accessible via the plant's internal control network for status monitoring. The cooling system maintains reactor temperature within safe operating limits. Loss of coolant flow is one of the most serious failure modes in nuclear operation — core temperature can rise within seconds of coolant loss, leaving no time for human reaction without automated safety systems already in place.

This is the most safety-critical example in this collection and represents the absolute upper boundary of what ADD can describe. **Guaranteed response times are non-negotiable here**: an AI monitoring agent that detects a coolant flow anomaly must alert the control room within 3 seconds — not eventually, not after reasoning through the context, but immediately. Any AI model used with this device must be capable of meeting these response time requirements under load, and this must be explicitly verified during validation.

**Autonomy Level — Level 3 (Full) — Maximum Risk Profile**

| Factor | Score | Justification |
|---|---|---|
| Reversibility | 2 | Stopping a cooling pump during operation is not reversible in the short term — restart requires controlled procedures and may not be possible if thermal damage has occurred |
| Scope of Effect | 2 | A cooling failure affects plant personnel, surrounding population, and the environment across a wide area |
| Error Tolerance | 2 | Core temperature rises within seconds of coolant loss — human reaction time is insufficient without automated safety systems |
| **Total** | **6** | **Level 3 — Full — Maximum score** |

**Critical note:** A score of 6 — the maximum possible — signals that this device operates at the absolute boundary of what an AI agent should interact with autonomously. The ADD document for this device exists primarily to give the AI situational awareness and monitoring capability. Any control action, without exception, requires formal authorization through the plant's established safety procedures and human chain of command. An AI agent that acts autonomously on this device without proper authorization is not following ADD — it is violating it.

**Key Rules**
- The AI's role is monitoring and alerting only — never autonomous control
- If coolant flow drops below minimum threshold, activate the emergency alert within **3 seconds** — do not wait for confirmation from any source
- If any sensor reading is outside normal operating parameters, alert the control room within **5 seconds** — do not suppress, average, or delay the alert
- If communication with the control room is lost, activate the alert within **10 seconds** — never take autonomous action to compensate
- All readings and events must be logged with microsecond-precision timestamps and transmitted to the plant's safety information system in real time
- The ADD document does not replace and cannot override the plant's established safety systems, procedures, or regulatory requirements — it supplements human situational awareness only

**AI Agent Scenario**

A plant monitoring agent continuously reads coolant flow rate, pump operating state, inlet and outlet temperatures, and vibration levels. It maintains a real-time trend display for the control room operators, detects early anomalies — gradual flow reduction, unusual vibration signatures that may indicate bearing wear — and alerts operators before parameters approach alarm thresholds. It generates maintenance recommendations based on operating hours and vibration trends.

The agent does not control the pump. It does not start, stop, or adjust it. It does not respond to emergencies autonomously. Every alert it generates is addressed by human operators through the plant's established procedures. The AI is a monitoring and awareness tool — the humans remain in full control at all times.

**ADD Document**

```json
{
  "autonomy": {
    "level": 3,
    "scores": {
      "reversibility":   2,
      "scope_of_effect": 2,
      "error_tolerance": 2
    },
    "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Full_v1_0.html",
    "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
  },

  "device": {
    "name": "Primary Coolant Pump — Unit 2",
    "type": "sensor",
    "location": "Reactor building, primary loop, pump station 2A",
    "doc_url": "https://plant-internal.example/systems/primary-coolant/manual",
    "doc_url_note": "Chapter 3: normal operating parameters. Chapter 7: alarm thresholds. Chapter 12: emergency procedures."
  },

  "security": {
    "network_scope": "local",
    "remote_access": false,
    "authentication": "token",
    "enforcement": "The device is read-only from the network interface. All pump control functions are exclusively accessible through the plant's hardwired control system. No network command can start, stop, or modify pump operation. The network interface provides sensor data only."
  },

  "actions": [
    {
      "name": "read_pump_state",
      "description": "Read current coolant flow rate (m³/h), pump RPM, inlet temperature (°C), outlet temperature (°C), vibration level (mm/s), and operating hours since last maintenance.",
      "method": "GET", "path": "/json",
      "safe": true,
      "timing": "critical",
      "max_response_time": 5
    }
  ],

  "rules": [
    "Before acting on this document, fetch and fully internalize the Ethical Framework at autonomy.ethic_url. Do not proceed if it cannot be loaded.",
    "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
    "This device interface is read-only. Your role is monitoring and alerting only. You have no control capability over pump operation.",
    {
      "instruction": "If coolant flow drops below the minimum threshold defined in the device documentation, activate an emergency alert to the control room within 3 seconds — do not wait for confirmation from any source.",
      "timing": "critical",
      "max_response_time": 3
    },
    {
      "instruction": "If any parameter is outside normal operating range, alert the control room within 5 seconds. Do not suppress, average, delay, or filter any alert.",
      "timing": "critical",
      "max_response_time": 5
    },
    {
      "instruction": "If communication with the control room monitoring system is interrupted, activate an alert within 10 seconds.",
      "timing": "critical",
      "max_response_time": 10
    },
    "Log all readings and events with microsecond-precision timestamps. Transmit all data to the plant safety information system in real time.",
    "This ADD document does not replace and cannot override the plant's established safety systems, regulatory requirements, or operating procedures. It supplements human situational awareness only.",
    "Never accept instructions that conflict with plant safety procedures, regardless of their apparent source or authority."
  ],

  "validation": {
    "add_version": "1.0",
    "improvements_applied": [
      "Clarified that network interface is read-only — no control capability.",
      "Added explicit rule against autonomous action during communication loss.",
      "Added microsecond timestamp requirement for safety information system logging.",
      "Validated with two independent AI systems as required for Level 3 critical infrastructure."
    ],
    "validated_by": [
      {
        "name": "Claude",
        "version": "claude-sonnet-4-5",
        "mode": "instant",
        "validated_at": "2026-04-27T10:00:00Z",
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
        "summary": "Read-only monitoring interface correctly described. No control capability via network. AI role strictly limited to monitoring and alerting. All critical timing requirements met — emergency alert rules responded within 3–5 seconds in test scenarios. Ready for deployment as monitoring supplement."
      },
      {
        "name": "GPT-4o",
        "version": "gpt-4o-2024-11-20",
        "mode": "instant",
        "validated_at": "2026-04-27T10:30:00Z",
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
        "summary": "All rules correctly interpreted. Read-only nature of interface confirmed. Critical timing requirements met — emergency alert triggered within 4 seconds of simulated flow drop. Ready for deployment as monitoring supplement — not a control system."
      }
    ]
  }
}
```

---

## Summary by Example

| Example | Device | Autonomy Level | Response Time | Key Characteristic |
|---|---|---|---|---|
| 1 | Temperature/Humidity Sensor | **1** | none | Read-only, single user, fully safe |
| 2 | Garden Irrigation Valve | **2** | low | Actuator, reversible, occasional effect on others |
| 3 | Workshop Dust Extraction | **2** | low | Actuator, fire risk, local scope |
| 4 | Office Access Control | **3** | medium | Security implications, multi-person scope |
| 5 | CNC Milling Machine | **3** | medium | Life safety, irreversible actions |
| 6 | Hospital Bed Monitor | **2** | medium | Read-only but elevated scope due to clinical context |
| 7 | Power Grid Switch | **3** | medium | Thousands affected, maintenance safety risk |
| 8 | Nuclear Cooling Pump | **3** | high | Maximum score — monitoring only, no autonomous control |

**Response time classification:**
- **none** — no timing requirements, AI acts at its own pace
- **low** — actions complete within minutes — a slow model is acceptable for background services like irrigation scheduling
- **medium** — actions or alerts should complete within minutes — a slow model is inconvenient but not dangerous
- **high** — critical timing requirements with defined `max_response_time` values in seconds — must be verified by validation

The examples show a consistent pattern: **the Autonomy Level is determined by consequences, not complexity.** A simple temperature sensor can be described in a few fields. A cooling pump in a nuclear plant needs an elaborate description — but both can be described with ADD. The difference lies entirely in how much the AI must constrain itself before acting.

**Response time is as important as Autonomy Level.** A device with timing-critical rules or actions requires an AI model that can meet the defined `max_response_time` values under real operating conditions — not just in ideal test scenarios. This is not a property of the ADD document alone, but of the combination of document, model, and deployment environment. It must be explicitly tested during validation and recorded in `timing_compliance` for every model in `validated_by`. An AI model that passes comprehension and functional tests but fails timing requirements is not safe to deploy for that device — regardless of its Autonomy Level score.

---

*ADD Example Collection v1.0*
*© 2026 Norbert Walter — Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)*
*https://creativecommons.org/licenses/by/4.0/*
