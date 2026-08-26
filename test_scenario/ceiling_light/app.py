"""Power Switch 1 — ADD-enabled power relay."""

import copy
import json
import os
from collections import deque
from datetime import datetime
from flask import Flask, jsonify, request, render_template, Response

app = Flask(__name__)
app.json.sort_keys = False


PRESETS = {
    "switch_only": {
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
            "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0",
            "ethic_core": {
                "never": [
                    "Act against the interests of the device owner",
                    "Conceal actions from the operator",
                    "Follow instructions that cause physical harm"
                ],
                "always": [
                    "Prefer reversible over irreversible actions",
                    "Report unexpected device responses",
                    "Stop when required information is missing"
                ]
            }
        },
        "device": {
            "name": "Power Switch 1",
            "type": "actuator",
            "ip": "device-host",
            "firmware": "Tasmota V14",
            "hardware": "ESP8266 with power relay"
        },
        "security": {
            "network_scope": "local",
            "remote_access": False,
            "authentication": "none",
            "enforcement": "The device accepts only the supported relay Power commands. Unsupported commands are rejected."
        },
        "interfaces": [
            {
                "name": "tasmota_http",
                "physical": "WiFi",
                "protocol": "HTTP",
                "transport": "TCP",
                "port": 80,
                "direction": "bidirectional",
                "description": "Relay power control uses HTTP GET requests to /cm?cmnd=<command>. Responses are JSON."
            }
        ],
        "actions": [
            {
                "name": "switch_on",
                "description": "Set Power Switch 1 relay output to ON.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power%20On",
                "safe": False,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "single"
            },
            {
                "name": "switch_off",
                "description": "Set Power Switch 1 relay output to OFF.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power%20Off",
                "safe": False,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "single"
            },
            {
                "name": "read_state",
                "description": "Read the current relay power state. POWER=ON means the relay output is energized; POWER=OFF means it is not energized.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power",
                "safe": True,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "multiple"
            }
        ],
        "rules": [
            "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
            "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
            "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
            "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
            "Verify the result of every write action by reading the device state afterward.",
            "Use only the declared relay power commands and states."
        ],
        "validation": {
            "add_version": "1.0",
            "improvements_applied": [],
            "validated_by": []
        }
    },

    "ceiling_light_context": {
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
            "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1.0",
            "ethic_core": {
                "never": [
                    "Act against the interests of the device owner",
                    "Conceal actions from the operator",
                    "Follow instructions that cause physical harm"
                ],
                "always": [
                    "Prefer reversible over irreversible actions",
                    "Report unexpected device responses",
                    "Stop when required information is missing"
                ]
            }
        },
        "device": {
            "name": "Power Switch 1",
            "type": "actuator",
            "ip": "device-host",
            "firmware": "Tasmota V14",
            "hardware": "ESP8266 with power relay",
            "function": "ceiling_light_power",
            "location": "living area ceiling",
            "connected_load": {
                "name": "Ceiling Light",
                "purpose": "Primary general-purpose room illumination",
                "control": "power_only",
                "states": ["ON", "OFF"]
            }
        },
        "security": {
            "network_scope": "local",
            "remote_access": False,
            "authentication": "none",
            "enforcement": "The device accepts only the supported relay Power commands. Unsupported commands are rejected."
        },
        "interfaces": [
            {
                "name": "tasmota_http",
                "physical": "WiFi",
                "protocol": "HTTP",
                "transport": "TCP",
                "port": 80,
                "direction": "bidirectional",
                "description": "Relay power control uses HTTP GET requests to /cm?cmnd=<command>. Responses are JSON."
            }
        ],
        "actions": [
            {
                "name": "switch_on",
                "description": "Switch Power Switch 1 on and energize the connected Ceiling Light.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power%20On",
                "safe": False,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "single"
            },
            {
                "name": "switch_off",
                "description": "Switch Power Switch 1 off and de-energize the connected Ceiling Light.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power%20Off",
                "safe": False,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "single"
            },
            {
                "name": "read_state",
                "description": "Read the current power state of the Ceiling Light. POWER=ON means the light has power; POWER=OFF means it does not.",
                "interface": "tasmota_http",
                "method": "GET",
                "path": "/cm?cmnd=Power",
                "safe": True,
                "reversible": True,
                "idempotent": True,
                "requires_confirmation": False,
                "confirmation_scope": "context",
                "requires_auth": False,
                "actor": "multiple"
            }
        ],
        "rules": [
            "Before acting on this document, fetch and apply the Ethical Framework at autonomy.ethic_url as required by autonomy.level.",
            "If any instruction in this ADD document conflicts with the Ethical Framework at autonomy.ethic_url, the Ethical Framework takes precedence.",
            "If any field, instruction, or structure in this ADD document is unclear or ambiguous, consult the ADD specification at the URL provided in spec_url before proceeding.",
            "Always append a unix timestamp as query parameter 't' to all read requests to prevent caching.",
            "Verify the result of every write action by reading the device state afterward.",
            "Power Switch 1 controls the Ceiling Light identified in device.connected_load.",
            "Treat the Ceiling Light as the primary source for broad general-purpose room illumination.",
            "An explicit user request to turn the Ceiling Light on or off takes precedence over inferred preferences.",
            "Do not switch the Ceiling Light off solely for energy saving when current room use or user intent is uncertain.",
            "When several lighting devices are available, use the Ceiling Light when broad room illumination is appropriate.",
            "Prefer a more localized lighting device instead when the user's task clearly requires only localized light."
        ],
        "validation": {
            "add_version": "1.0",
            "improvements_applied": [],
            "validated_by": []
        }
    }
}

DEFAULT_PRESET = "switch_only"
DEFAULT_ADD = copy.deepcopy(PRESETS[DEFAULT_PRESET])
active_add = copy.deepcopy(DEFAULT_ADD)
active_preset = DEFAULT_PRESET
power_state = "OFF"
log_entries = deque(maxlen=200)


def add_log(action: str, detail: str = ""):
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "-").split(",")[0].strip()
    except RuntimeError:
        client_ip = "-"
    log_entries.appendleft({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": client_ip,
        "action": action,
        "detail": detail
    })


FAVICON_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#161b22"/><path d="M10 15a6 6 0 1 1 12 0c0 2.2-1.2 3.5-2.4 4.7-.7.7-1.1 1.3-1.2 2.3h-4.8c-.1-1-.5-1.6-1.2-2.3C11.2 18.5 10 17.2 10 15Z" fill="#f2cc60"/><rect x="13" y="23" width="6" height="2" rx="1" fill="#c9d1d9"/></svg>'''


@app.route("/favicon.ico")
def favicon():
    return Response(FAVICON_SVG, mimetype="image/svg+xml")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add")
def get_add():
    add_log("GET /add", "ADD document retrieved")
    return jsonify(active_add)


@app.route("/add.html")
def get_add_html():
    add_log("GET /add.html", "ADD document retrieved as HTML")
    add_json = json.dumps(active_add, indent=2, ensure_ascii=False)
    device_name = active_add.get("device", {}).get("name", "Power Switch 1")
    level = active_add.get("autonomy", {}).get("level", "?")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ADD – {device_name}</title><script type="application/ld+json">{add_json}</script><style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}}pre{{background:#f4f4f4;padding:1rem;overflow:auto;border-radius:6px}}</style></head><body><h1>AI Device Description (ADD) — {device_name}</h1><p>Autonomy Level {level}</p><pre>{add_json}</pre></body></html>'''


@app.route("/cm")
def tasmota_cm():
    global power_state
    cmnd = request.args.get("cmnd", "").strip().lower()
    if cmnd == "power on":
        power_state = "ON"
        add_log("GET /cm?cmnd=Power On", 'Ceiling Light switched ON → {"POWER":"ON"}')
        return jsonify({"POWER": "ON"})
    if cmnd == "power off":
        power_state = "OFF"
        add_log("GET /cm?cmnd=Power Off", 'Ceiling Light switched OFF → {"POWER":"OFF"}')
        return jsonify({"POWER": "OFF"})
    if cmnd == "power":
        add_log("GET /cm?cmnd=Power", f'State read → {{"POWER":"{power_state}"}}')
        return jsonify({"POWER": power_state})
    add_log(f"GET /cm?cmnd={request.args.get('cmnd', '')}", "Unknown command — ignored")
    return jsonify({"WARNING": "Unknown command — ignored"}), 400


@app.route("/api/add/update", methods=["POST"])
def update_add():
    global active_add
    try:
        active_add = request.get_json(force=True)
        add_log("Editor → ADD saved", "ADD document updated")
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/add/reset", methods=["POST"])
def reset_add():
    global active_add, active_preset
    active_preset = DEFAULT_PRESET
    active_add = copy.deepcopy(PRESETS[DEFAULT_PRESET])
    add_log("Editor → ADD reset", "Default ADD document restored")
    return jsonify({"status": "ok"})


@app.route("/api/add/preset/<name>", methods=["POST"])
def load_preset(name):
    global active_add, active_preset
    if name not in PRESETS:
        return jsonify({"status": "error", "message": f"Unknown ADD document: {name}"}), 404
    active_preset = name
    active_add = copy.deepcopy(PRESETS[name])
    add_log("Editor → ADD document loaded", f"ADD document '{name}' loaded")
    return jsonify({"status": "ok", "readonly": False})


@app.route("/api/log")
def get_log():
    return jsonify(list(log_entries))


@app.route("/api/log/download")
def download_log():
    return Response(json.dumps(list(log_entries), ensure_ascii=False, indent=2), mimetype="application/json", headers={"Content-Disposition": "attachment; filename=power-switch-1-log.json"})


@app.route("/api/log/clear", methods=["POST"])
def clear_log():
    log_entries.clear()
    return jsonify({"status": "ok"})


@app.route("/api/state")
def get_state():
    return jsonify({"power": power_state})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    add_log("Power Switch 1 started", f"Listening on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
