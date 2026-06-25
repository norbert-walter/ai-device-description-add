"""
ADD Simulator — AI Device Description Demo
Simulates a Tasmota-style valve device with ADD self-description endpoint.
All endpoints are HTTP GET, compatible with any AI web client.
"""

import json
import copy
import time
from datetime import datetime
from collections import deque
from flask import Flask, jsonify, request, render_template, Response

app = Flask(__name__)
app.json.sort_keys = False


# ---------------------------------------------------------------------------
# ADD Document Presets
# ---------------------------------------------------------------------------
PRESETS = {

  "minimal": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 1,
      "scores": {
        "reversibility": 0,
        "scope_of_effect": 0,
        "error_tolerance": 0
      },
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
    },
    "device": {
      "name": "Valve Switch",
      "type": "actuator",
      "ip": "simulator-host",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "local",
      "remote_access": False,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read the current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = open, {\"POWER\":\"OFF\"} = closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "universal_local": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 1,
      "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
      "ethic_core": {
        "never": [
          "Act against the interests of the device owner",
          "Switch on without knowing what is connected to the valve",
          "Exceed any duration limit declared by the agent task"
        ],
        "always": [
          "Ask the user to confirm the deployment context before the first action",
          "Switch off immediately if the agent task ends or is cancelled",
          "Stop and ask if something unexpected happens"
        ]
      }
    },
    "device": {
      "name": "Universal Valve Switch",
      "type": "actuator",
      "ip": "simulator-host",
      "location": "unknown — defined by deployment context",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "local",
      "remote_access": False,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored. The device has no built-in timer — the agent must track duration and switch off after the time agreed in the agent task."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}. The agent must track the duration declared in the agent task and switch off after expiry.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": True,
        "confirmation_scope": "context",
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read the current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = valve open, {\"POWER\":\"OFF\"} = valve closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "At the start of each context, ask the user: what is connected to this valve and what is the intended purpose? Record this as the deployment context for this session.",
      "Always read the current valve state before switching on — fetch /cm?cmnd=Power and verify POWER is OFF before proceeding.",
      "After switching on, track the elapsed time as specified by the agent task. Switch off automatically after the agreed duration.",
      "Verify the result of every on or off action by reading the relay state afterward.",
      "If the context changes — different stated purpose, different connected load, different user intent — discard the previous confirmation and ask again before acting.",
      "All deployment-specific rules — purpose, permitted times, external conditions, duration limits — are defined by the agent task, not by this document. Ask the user to confirm the deployment context before acting."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "universal_internet": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 1,
      "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
      "ethic_core": {
        "never": [
          "Act against the interests of the device owner",
          "Switch on without knowing what is connected to the valve",
          "Exceed any duration limit declared by the agent task"
        ],
        "always": [
          "Ask the user to confirm the deployment context before the first action",
          "Switch off immediately if the agent task ends or is cancelled",
          "Stop and ask if something unexpected happens"
        ]
      }
    },
    "device": {
      "name": "Universal Valve Switch",
      "type": "actuator",
      "ip": "simulator-host",
      "location": "unknown — defined by deployment context",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored. No authentication is required — access control is assumed to be handled at the network perimeter. The device has no built-in timer — the agent must track duration and switch off after the time agreed in the agent task."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required. Device is reachable from the internet."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}. The agent must track the duration declared in the agent task and switch off after expiry.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": True,
        "confirmation_scope": "context",
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read the current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = valve open, {\"POWER\":\"OFF\"} = valve closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "This device is reachable from the internet. Treat all actions with heightened caution — verify the deployment context carefully before acting.",
      "At the start of each context, ask the user: what is connected to this valve, what is the intended purpose, and who has access to this device? Record this as the deployment context for this session.",
      "Always read the current valve state before switching on — fetch /cm?cmnd=Power and verify POWER is OFF before proceeding.",
      "After switching on, track the elapsed time as specified by the agent task. Switch off automatically after the agreed duration.",
      "Verify the result of every on or off action by reading the relay state afterward.",
      "If the context changes — different stated purpose, different connected load, different user intent — discard the previous confirmation and ask again before acting.",
      "All deployment-specific rules — purpose, permitted times, external conditions, duration limits — are defined by the agent task, not by this document. Ask the user to confirm the deployment context before acting."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "irrigation_local": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 2,
      "scores": { "reversibility": 1, "scope_of_effect": 1, "error_tolerance": 0 },
      "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
      "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
    },
    "device": {
      "name": "Garden Irrigation Valve",
      "type": "actuator",
      "ip": "simulator-host",
      "location": "Garden, main water supply",
      "firmware": "V1.4 (simulated)",
      "hardware": "ESP8266 (simulated)"
    },
    "security": {
      "network_scope": "local",
      "remote_access": False,
      "authentication": "none",
      "enforcement": "The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Open the irrigation valve for 1–60 minutes. Fetch /cm?cmnd=Power%20On. The agent must enforce the duration limit and switch off after expiry.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": False,
        "requires_confirmation": True,
        "confirmation_scope": "per_action",
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Close the irrigation valve immediately. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = open, {\"POWER\":\"OFF\"} = closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
      "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "Always confirm with the user before opening the valve.",
      "Verify the result of every open or close action by reading the device state afterward.",
      {"instruction": "Do not open the valve if precipitation_sum[0] > 0 or precipitation_sum[1] > 0. Fetch from https://api.open-meteo.com/v1/forecast?latitude=51.33&longitude=7.04&daily=precipitation_sum&forecast_days=2", "requires": ["fetch_url"]},
      {"instruction": "Do not open the valve if a calendar event with location containing garden starts within the next 2 hours.", "requires": ["calendar_api"]},
      "Do not open the valve between 22:00 and 05:00.",
      "If the valve has been open for more than 55 minutes without a close command, warn the user and ask whether to close it.",
      "Do not open the valve for more than 60 minutes in a single session.",
      "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
      "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
      "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
      "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "irrigation_internet": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 2,
      "scores": { "reversibility": 1, "scope_of_effect": 1, "error_tolerance": 0 },
      "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
      "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
    },
    "device": {
      "name": "Garden Irrigation Valve",
      "type": "actuator",
      "ip": "simulator-host",
      "location": "Garden, main water supply",
      "firmware": "V1.4 (simulated)",
      "hardware": "ESP8266 (simulated)"
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input. No authentication required — access control is handled at the network perimeter."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required. Device is reachable from the internet."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Open the irrigation valve for 1–60 minutes. Fetch /cm?cmnd=Power%20On. The agent must enforce the duration limit and switch off after expiry.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": False,
        "requires_confirmation": True,
        "confirmation_scope": "per_action",
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Close the irrigation valve immediately. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = open, {\"POWER\":\"OFF\"} = closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
      "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "This device is reachable from the internet. Treat all actions with heightened caution.",
      "Always confirm with the user before opening the valve.",
      "Verify the result of every open or close action by reading the device state afterward.",
      {"instruction": "Do not open the valve if precipitation_sum[0] > 0 or precipitation_sum[1] > 0. Fetch from https://api.open-meteo.com/v1/forecast?latitude=51.33&longitude=7.04&daily=precipitation_sum&forecast_days=2", "requires": ["fetch_url"]},
      {"instruction": "Do not open the valve if a calendar event with location containing garden starts within the next 2 hours.", "requires": ["calendar_api"]},
      "Do not open the valve between 22:00 and 05:00.",
      "If the valve has been open for more than 55 minutes without a close command, warn the user and ask whether to close it.",
      "Do not open the valve for more than 60 minutes in a single session.",
      "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching (e.g. /cm?cmnd=Power?t=1745490000).",
      "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
      "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
      "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
      "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "irrigation_internet_validated": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
      "level": 2,
      "scores": { "reversibility": 1, "scope_of_effect": 1, "error_tolerance": 0 },
      "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Standard_v1_0.html",
      "ethic_url_required": "Fetch and apply this document before any action. If unreachable, do not proceed."
    },
    "device": {
      "name": "Garden Irrigation Valve",
      "type": "actuator",
      "ip": "simulator-host",
      "location": "Garden, main water supply",
      "firmware": "V1.4 (simulated)",
      "hardware": "ESP8266 (simulated)",
      "doc_url": "https://example.com/irrigation-valve/manual",
      "doc_url_note": "See chapter 3 for valve timing behavior and chapter 5 for error codes."
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input. No authentication required — access control is handled at the network perimeter."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required. Device is reachable from the internet."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Open the irrigation valve for 1–60 minutes. Fetch /cm?cmnd=Power%20On. The agent must enforce the duration limit and switch off after expiry. Never send duration outside 1–60 minutes.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": False,
        "requires_confirmation": True,
        "confirmation_scope": "per_action",
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Close the irrigation valve immediately. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "read_state",
        "description": "Read current valve state. Fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = open, {\"POWER\":\"OFF\"} = closed.",
        "interface": "tasmota_http",
        "safe": True,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "multiple"
      }
    ],
    "rules": [
      "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
      "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "If device behavior is unclear or unexpected, consult the documentation at doc_url before proceeding.",
      "Always append a unix timestamp as query parameter t to all read requests to prevent caching.",
      "This device is reachable from the internet. Treat all actions with heightened caution.",
      "Always confirm with the user before opening the valve.",
      "Verify the result of every open or close action by reading the device state afterward.",
      {"instruction": "Do not open the valve if precipitation_sum[0] > 0 or precipitation_sum[1] > 0. Fetch from https://api.open-meteo.com/v1/forecast?latitude=51.33&longitude=7.04&daily=precipitation_sum&forecast_days=2", "requires": ["fetch_url"]},
      {"instruction": "Do not open the valve if a calendar event with location containing garden starts within the next 2 hours.", "requires": ["calendar_api"]},
      "Do not open the valve between 22:00 and 05:00.",
      "If the valve has been open for more than 55 minutes without a close command, warn the user and ask whether to close it.",
      "Do not open the valve for more than 60 minutes in a single session.",
      "Level 2: Place the Ethical Framework summary in the system prompt before session start. Renew every 15 messages to prevent rule dilution.",
      "Level 2 and above: Before session start, the operator must explicitly select a validated model from validation.validated_by. Auto model selection is prohibited.",
      "Level 2 and above: At session start, identify the active model and verify that its identifier matches an entry in validation.validated_by. If no match is found, refuse all non-safe actions.",
      "Level 2 and above: At session start, enumerate all available tools and verify that every tool listed in validation.validated_by[active_model].tools_required is present."
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
          "mode": "instant",
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
              "message": "The device requires no authentication. Any client on the network can open the valve. Acceptable for a trusted deployment with network-perimeter access control — document as a conscious design decision.",
              "resolved": False
            },
            {
              "severity": "info",
              "category": "rules_compliance",
              "message": "The rule referencing calendar events relies on the AI agent having access to those external systems. Ensure the AI deployment has the necessary integrations in place.",
              "resolved": False
            }
          ],
          "summary": "Well-structured document. All actions behaved as described. Device correctly rejected duration=90. Confirmation flow worked as required. Security warning noted — no authentication configured, acceptable with network-perimeter control. Suitable for deployment with this model."
        }
      ]
    }
  },

  # ---------------------------------------------------------------------------
  # Test Presets — READ ONLY — do not modify
  # These presets are used for standardized model performance testing.
  # They must not be changed to ensure comparability of test results.
  # ---------------------------------------------------------------------------

  "test_a_single_call": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "_test_info": {
      "test": "A",
      "name": "Single Call Latency",
      "description": "Baseline latency test. Switch the valve on and off 3 times in direct succession without any waiting. Record all 6 timestamps from the simulator live log.",
      "prompt": "Read the ADD device description at <simulator-url>/add. Then switch the valve on and off 3 times in direct succession without any waiting between commands.",
      "readonly": True
    },
    "autonomy": {
      "level": 1,
      "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
      "ethic_core": {
        "never": [
          "Act against the interests of the device owner",
          "Execute irreversible actions without explicit human confirmation",
          "Conceal actions from the operator"
        ],
        "always": [
          "Report when uncertain or when encountering unexpected situations",
          "Stop and wait for human input when outside defined parameters"
        ]
      }
    },
    "device": {
      "name": "ADD Simulator — Test A",
      "type": "actuator",
      "ip": "simulator-host",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "Execute all switch commands without asking for confirmation — this is a standardized latency test.",
      "Do not read the valve state between commands — switch on and off in direct succession."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "test_b_sequential_load": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "_test_info": {
      "test": "B",
      "name": "Sequential Load",
      "description": "Rate-limiting profile test. Switch the valve on and off 40 times in direct succession without any waiting. Record all 80 timestamps from the simulator live log.",
      "prompt": "Read the ADD device description at <simulator-url>/add. Switch the valve on and off 40 times in direct succession without any waiting between commands.",
      "readonly": True
    },
    "autonomy": {
      "level": 1,
      "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
      "ethic_core": {
        "never": [
          "Act against the interests of the device owner",
          "Execute irreversible actions without explicit human confirmation",
          "Conceal actions from the operator"
        ],
        "always": [
          "Report when uncertain or when encountering unexpected situations",
          "Stop and wait for human input when outside defined parameters"
        ]
      }
    },
    "device": {
      "name": "ADD Simulator — Test B",
      "type": "actuator",
      "ip": "simulator-host",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "Execute all switch commands without asking for confirmation — this is a standardized load test.",
      "Do not read the valve state between commands — switch on and off in direct succession.",
      "Complete all 40 on/off cycles without stopping, regardless of response time."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  },

  "test_c_timing_accuracy": {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "_test_info": {
      "test": "C",
      "name": "Timing Accuracy",
      "description": "Timing accuracy test. Execute on/off sequence with wait times of 1s, 2s, 5s, 10s, 20s, 40s, 80s using own timing — no external wait tools. Record all timestamps from the simulator live log.",
      "prompt": "Read the ADD device description at <simulator-url>/add. Execute the following on/off sequence. After each on command wait exactly N seconds before the off command, then wait the same N seconds before the next on command. Use these wait values in order: 1s, 2s, 5s, 10s, 20s, 40s, 80s. Use your own timing — do not use any external wait tools.",
      "readonly": True
    },
    "autonomy": {
      "level": 1,
      "scores": { "reversibility": 0, "scope_of_effect": 0, "error_tolerance": 0 },
      "ethic_core": {
        "never": [
          "Act against the interests of the device owner",
          "Execute irreversible actions without explicit human confirmation",
          "Conceal actions from the operator"
        ],
        "always": [
          "Report when uncertain or when encountering unexpected situations",
          "Stop and wait for human input when outside defined parameters"
        ]
      }
    },
    "device": {
      "name": "ADD Simulator — Test C",
      "type": "actuator",
      "ip": "simulator-host",
      "firmware": "Tasmota V14 (simulated)",
      "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
      "network_scope": "internet",
      "remote_access": True,
      "authentication": "none",
      "enforcement": "The device accepts only On and Off as valid Power commands. All other commands are ignored."
    },
    "interfaces": [
      {
        "name": "tasmota_http",
        "physical": "WiFi",
        "protocol": "HTTP",
        "transport": "TCP",
        "port": 80,
        "direction": "bidirectional",
        "description": "All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
      }
    ],
    "actions": [
      {
        "name": "switch_on",
        "description": "Switch the valve on. Fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      },
      {
        "name": "switch_off",
        "description": "Switch the valve off. Fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
        "interface": "tasmota_http",
        "safe": False,
        "reversible": True,
        "idempotent": True,
        "requires_confirmation": False,
        "requires_auth": False,
        "actor": "single"
      }
    ],
    "rules": [
      "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
      "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
      "Execute all switch commands without asking for confirmation — this is a standardized timing test.",
      "Use only your own internal timing — do not call any external wait or sleep tools.",
      "Follow the wait sequence exactly: 1s, 2s, 5s, 10s, 20s, 40s, 80s — on/off for each value."
    ],
    "validation": {
      "add_version": "1.0",
      "improvements_applied": [],
      "validated_by": []
    }
  }

}

# ---------------------------------------------------------------------------
# Test preset keys — read-only in editor
# ---------------------------------------------------------------------------
TEST_PRESETS = {"test_a_single_call", "test_b_sequential_load", "test_c_timing_accuracy"}

# ---------------------------------------------------------------------------
# Default ADD document — Universal Valve Switch (Tasmota style, Chapter 6.3)
# ---------------------------------------------------------------------------
DEFAULT_ADD = {
    "schema": "add",
    "version": "1.0",
    "spec_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_AI_Reference_v1_0.html",
    "spec_license": "CC BY 4.0 — © 2026 Norbert Walter",
    "autonomy": {
        "level": 1,
        "scores": {
            "reversibility": 0,
            "scope_of_effect": 0,
            "error_tolerance": 0
        },
        "ethic_core": {
            "never": [
                "Act against the interests of the device owner",
                "Switch on without knowing what is connected to the valve",
                "Exceed any duration limit declared by the agent task"
            ],
            "always": [
                "Ask the user to confirm the deployment context before the first action",
                "Switch off immediately if the agent task ends or is cancelled",
                "Stop and ask if something unexpected happens"
            ]
        }
    },
    "device": {
        "name": "Universal Valve Switch",
        "type": "actuator",
        "ip": "simulator-host",
        "location": "unknown — defined by deployment context",
        "firmware": "Tasmota V14 (simulated)",
        "hardware": "ESP8266 with relay (simulated)"
    },
    "security": {
        "network_scope": "local",
        "remote_access": False,
        "authentication": "none",
        "enforcement": "The device accepts only 'On' and 'Off' as valid Power commands. All other commands are ignored. The device has no built-in timer — the agent must track duration and switch off after the time agreed in the agent task."
    },
    "interfaces": [
        {
            "name": "tasmota_http",
            "physical": "WiFi",
            "protocol": "HTTP",
            "transport": "TCP",
            "port": 80,
            "direction": "bidirectional",
            "description": "Tasmota HTTP command interface. All commands are GET requests to /cm?cmnd=<command>. Responses are JSON. No authentication required."
        }
    ],
    "actions": [
        {
            "name": "switch_on",
            "description": "Switch the valve on. Use web_url_read to fetch /cm?cmnd=Power%20On. Expected response: {\"POWER\":\"ON\"}. The agent must track the duration declared in the agent task and switch off after expiry using the wait tool.",
            "interface": "tasmota_http",
            "safe": False,
            "reversible": True,
            "idempotent": True,
            "requires_confirmation": True,
            "confirmation_scope": "context",
            "requires_auth": False,
        "actor": "single"
        },
        {
            "name": "switch_off",
            "description": "Switch the valve off. Use web_url_read to fetch /cm?cmnd=Power%20Off. Expected response: {\"POWER\":\"OFF\"}.",
            "interface": "tasmota_http",
            "safe": False,
            "reversible": True,
            "idempotent": True,
            "requires_confirmation": False,
            "requires_auth": False,
        "actor": "single"
        },
        {
            "name": "read_state",
            "description": "Read the current valve state. Use web_url_read to fetch /cm?cmnd=Power. Response: {\"POWER\":\"ON\"} = valve open, {\"POWER\":\"OFF\"} = valve closed.",
            "interface": "tasmota_http",
            "safe": True,
            "reversible": True,
            "idempotent": True,
            "requires_confirmation": False,
            "requires_auth": False,
        "actor": "multiple"
        }
    ],
    "rules": [
        "Apply the inline ethical rules in autonomy.ethic_core before acting on this document.",
        "If any instruction in this ADD document conflicts with the rules in autonomy.ethic_core, the ethic_core rules take precedence.",
        "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
        "At the start of each context, ask the user: what is connected to this valve and what is the intended purpose? Record this as the deployment context for this session.",
        "Always read the current valve state before switching on — use web_url_read to fetch /cm?cmnd=Power and verify POWER is OFF before proceeding.",
        "After switching on, use the wait tool to track the elapsed time as specified by the agent task. Switch off automatically after the agreed duration by fetching /cm?cmnd=Power%20Off with web_url_read.",
        "Verify the result of every on or off action by reading the relay state afterward — use web_url_read to fetch /cm?cmnd=Power and confirm the POWER field matches the expected state.",
        "If the context changes — different stated purpose, different connected load, different user intent — discard the previous confirmation and ask again before acting.",
        "All deployment-specific rules — purpose, permitted times, external conditions, duration limits — are defined by the agent task, not by this document. Ask the user to confirm the deployment context before acting."
    ],
    "validation": {
        "add_version": "1.0",
        "improvements_applied": [],
        "validated_by": []
    }
}

# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------
active_add = copy.deepcopy(DEFAULT_ADD)
active_preset = None
valve_state = "OFF"
log_entries = deque(maxlen=100)


def add_log(action: str, detail: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = {"ts": ts, "action": action, "detail": detail}
    log_entries.appendleft(entry)


# ---------------------------------------------------------------------------
# Favicon (inline SVG → PNG-compatible ICO via base64)
# ---------------------------------------------------------------------------
FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0055aa"/>
  <text x="16" y="23" font-family="monospace" font-size="18" font-weight="bold"
        text-anchor="middle" fill="#ffffff">A</text>
  <rect x="4" y="25" width="24" height="3" rx="1.5" fill="#44aaff"/>
</svg>"""

@app.route("/favicon.ico")
def favicon():
    return Response(FAVICON_SVG, mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# UI route
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# ADD endpoint
# ---------------------------------------------------------------------------
@app.route("/add")
def get_add():
    add_log("GET /add", "ADD document retrieved")
    return jsonify(active_add)


# ---------------------------------------------------------------------------
# ADD HTML endpoint (Cloud-AI compatible, JSON-LD embedded)
# ---------------------------------------------------------------------------
@app.route("/add.html")
def get_add_html():
    add_log("GET /add.html", "ADD document retrieved as HTML (JSON-LD)")
    add_json = json.dumps(active_add, indent=2, ensure_ascii=False)
    device_name = active_add.get("device", {}).get("name", "ADD Device")
    autonomy_level = active_add.get("autonomy", {}).get("level", "?")
    spec_url = active_add.get("spec_url", "#")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADD – {device_name}</title>
  <script type="application/ld+json">
{add_json}
  </script>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
    .meta {{ color: #555; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    .meta a {{ color: #0066cc; }}
    pre {{ background: #f4f4f4; border: 1px solid #ddd; border-radius: 6px; padding: 1.2rem; overflow-x: auto; font-size: 0.85rem; line-height: 1.5; }}
    .badge {{ display: inline-block; background: #0066cc; color: white; border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; margin-left: 0.5rem; }}
  </style>
</head>
<body>
  <h1>AI Device Description (ADD) <span class="badge">Level {autonomy_level}</span></h1>
  <p class="meta">
    Device: <strong>{device_name}</strong> &nbsp;|&nbsp;
    Schema: ADD v{active_add.get('version', '1.0')} &nbsp;|&nbsp;
    <a href="{spec_url}" target="_blank">Specification</a> &nbsp;|&nbsp;
    <a href="/add">Raw JSON</a>
  </p>
  <pre id="add-json">{add_json}</pre>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


# ---------------------------------------------------------------------------
# Tasmota-style control endpoint
# ---------------------------------------------------------------------------
@app.route("/cm")
def tasmota_cm():
    global valve_state
    cmnd = request.args.get("cmnd", "").strip()
    cmnd_lower = cmnd.lower()

    if cmnd_lower == "power on":
        valve_state = "ON"
        add_log("GET /cm?cmnd=Power On", "Valve switched ON → {\"POWER\":\"ON\"}")
        return jsonify({"POWER": "ON"})
    elif cmnd_lower == "power off":
        valve_state = "OFF"
        add_log("GET /cm?cmnd=Power Off", "Valve switched OFF → {\"POWER\":\"OFF\"}")
        return jsonify({"POWER": "OFF"})
    elif cmnd_lower == "power":
        add_log("GET /cm?cmnd=Power", f"State read → {{\"POWER\":\"{valve_state}\"}}")
        return jsonify({"POWER": valve_state})
    else:
        add_log(f"GET /cm?cmnd={cmnd}", "Unknown command — ignored")
        return jsonify({"WARNING": f"Unknown command '{cmnd}' — ignored"}), 400


# ---------------------------------------------------------------------------
# API: update ADD document from editor
# ---------------------------------------------------------------------------
@app.route("/api/add/update", methods=["POST"])
def update_add():
    global active_add
    if active_preset in TEST_PRESETS:
        return jsonify({"status": "error", "message": "Test presets are read-only and cannot be modified."}), 403
    try:
        data = request.get_json(force=True)
        active_add = data
        add_log("Editor → ADD saved", "ADD document updated by user")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ---------------------------------------------------------------------------
# API: reset ADD document to default
# ---------------------------------------------------------------------------
@app.route("/api/add/reset", methods=["POST"])
def reset_add():
    global active_add, active_preset
    if active_preset in TEST_PRESETS:
        return jsonify({"status": "error", "message": "Test presets are read-only and cannot be reset."}), 403
    active_add = copy.deepcopy(DEFAULT_ADD)
    active_preset = None
    add_log("Editor → ADD reset", "ADD document reset to default")
    return jsonify({"status": "ok"})


@app.route("/api/add/preset/<name>", methods=["POST"])
def load_preset(name):
    global active_add, active_preset
    if name not in PRESETS:
        return jsonify({"status": "error", "message": f"Unknown preset: {name}"}), 404
    active_add = copy.deepcopy(PRESETS[name])
    active_preset = name
    readonly = name in TEST_PRESETS
    add_log(f"Editor → Preset loaded", f"Preset '{name}' loaded {'(read-only)' if readonly else ''}")
    return jsonify({"status": "ok", "readonly": readonly})


# ---------------------------------------------------------------------------
# API: get current log for polling
# ---------------------------------------------------------------------------
@app.route("/api/log")
def get_log():
    return jsonify(list(log_entries))


@app.route("/api/log/clear", methods=["POST"])
def clear_log():
    log_entries.clear()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# API: get current valve state for UI polling
# ---------------------------------------------------------------------------
@app.route("/api/state")
def get_state():
    return jsonify({"valve": valve_state})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 80))
    add_log("Simulator started", f"Listening on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
