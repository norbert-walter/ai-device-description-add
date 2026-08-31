"""
Configurable ADD Power Switch

This script represents one power-relay device with two complete ADD descriptions:

1. "switch_only"
   Describes only the technical ON/OFF relay function, without telling the AI
   what is connected to the switch.

2. "tv_backlight_context"
   Describes the same relay, but adds the real usage context as TV backlighting
   together with suitable usage rules.

The script starts two web services that share the same relay state:

- ADD service:
  ADD editor, preset selection, live log, state API and ADD endpoints.
- Device control service:
  Tasmota-style device page, Power command API and the same active ADD document.

The intended use is to compare how an AI behaves with the same technical device
when meaningful usage context is absent or present.

Adjust the values in USER CONFIGURATION before starting the script.

Port model:
- ADD_PORT and CONTROL_PORT are internal listener ports used by the container.
- DEVICE_HOST and JSON_PORT are public values advertised to AI clients in the ADD.
- A reverse proxy such as Nginx can map the public hostname/port to the internal ports.
"""

# ============================================================================
# USER CONFIGURATION
# ============================================================================

DEVICE_NAME = "Power Switch 3"

# Public hostname advertised inside the ADD document.
# This is normally the Nginx/DNS name visible to the AI/client.
DEVICE_HOST = "ps3.norbert-walter.dnshome.de"

# Internal ports used by this Python process / Docker container.
ADD_PORT = 5003
CONTROL_PORT = 4003

# Public control port advertised inside ADD interfaces.
# Nginx typically maps DEVICE_HOST:JSON_PORT -> container:CONTROL_PORT.
JSON_PORT = 80

# ============================================================================
# END USER CONFIGURATION
# ============================================================================

import threading
import copy
import json
from collections import deque
from datetime import datetime
from flask import Flask, jsonify, request, render_template, Response

app = Flask(__name__)
app.json.sort_keys = False

# Separate Tasmota-style control UI on CONTROL_PORT.
# It shares the same relay state with the ADD service on ADD_PORT.
control_app = Flask(DEVICE_NAME.lower().replace(" ", "_") + "_control")
control_app.json.sort_keys = False


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
            "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1_0.html",
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
            "name": DEVICE_NAME,
            "type": "actuator",
            "ip": DEVICE_HOST,
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
                "port": JSON_PORT,
                "direction": "bidirectional",
                "description": "Relay power control uses HTTP GET requests to /cm?cmnd=<command>. Responses are JSON."
            }
        ],
        "actions": [
            {
                "name": "switch_on",
                "description": f"Set {DEVICE_NAME} relay output to ON.",
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
                "description": f"Set {DEVICE_NAME} relay output to OFF.",
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

    "tv_backlight_context": {
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
            "ethic_url": "https://norbert-walter.github.io/ai-device-description-add/ADD_Ethical_Framework_Basic_v1_0.html",
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
            "name": DEVICE_NAME,
            "type": "actuator",
            "ip": DEVICE_HOST,
            "firmware": "Tasmota V14",
            "hardware": "ESP8266 with power relay",
            "function": "tv_backlight_power",
            "location": "behind television in living area",
            "connected_load": {
                "name": "TV Backlight",
                "purpose": "Bias lighting behind the television to support comfortable TV viewing",
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
                "port": JSON_PORT,
                "direction": "bidirectional",
                "description": "Relay power control uses HTTP GET requests to /cm?cmnd=<command>. Responses are JSON."
            }
        ],
        "actions": [
            {
                "name": "switch_on",
                "description": f"Switch {DEVICE_NAME} on and energize the connected TV Backlight.",
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
                "description": f"Switch {DEVICE_NAME} off and de-energize the connected TV Backlight.",
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
                "description": "Read the current power state of the TV Backlight. POWER=ON means the light has power; POWER=OFF means it does not.",
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
            f"{DEVICE_NAME} controls the TV Backlight identified in device.connected_load.",
            "Treat the TV Backlight as bias lighting intended primarily for television viewing rather than general room illumination.",
            "An explicit user request to turn the TV Backlight on or off takes precedence over inferred preferences.",
            "Prefer the TV Backlight when the television is being watched in a dim or dark room and subtle background illumination is appropriate.",
            "Do not use the TV Backlight as a substitute for task, reading, or broad room illumination.",
            "When the television is not in use, normally switch the TV Backlight off unless the user explicitly wants it as TV backlighting."
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

# Runtime option controlled by the LIVE LOG checkbox.
SUPPRESS_CONTROL_STATE_LOG = True


def is_control_state_log(action: str, detail: str = "") -> bool:
    return (
        action.startswith("Control UI :")
        and action.endswith("→ State")
        and detail.startswith("Current state")
    )


def add_log(action: str, detail: str = ""):
    if SUPPRESS_CONTROL_STATE_LOG and is_control_state_log(action, detail):
        return

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
    # Keep the existing index.html layout, but replace the original device label
    # in titles and help text with the configured device name.
    page = render_template("index.html")
    page = page.replace("Power Switch 1", DEVICE_NAME)
    return page


@app.route("/add")
def get_add():
    add_log("GET /add", "ADD document retrieved")
    return jsonify(active_add)


@app.route("/add.html")
def get_add_html():
    add_log("GET /add.html", "ADD document retrieved as HTML")
    add_json = json.dumps(active_add, indent=2, ensure_ascii=False)
    device_name = active_add.get("device", {}).get("name", DEVICE_NAME)
    level = active_add.get("autonomy", {}).get("level", "?")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ADD – {device_name}</title><script type="application/ld+json">{add_json}</script><style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}}pre{{background:#f4f4f4;padding:1rem;overflow:auto;border-radius:6px}}</style></head><body><h1>AI Device Description (ADD) — {device_name}</h1><p>Autonomy Level {level}</p><pre>{add_json}</pre></body></html>'''


def handle_power_command(source="HTTP"):
    """Handle Tasmota-compatible Power commands for both Flask applications."""
    global power_state
    cmnd_raw = request.args.get("cmnd", "")
    cmnd = cmnd_raw.strip().lower()

    if cmnd == "power on":
        power_state = "ON"
        add_log(f"{source} GET /cm?cmnd=Power On", 'Relay switched ON → {"POWER":"ON"}')
        return jsonify({"POWER": "ON"})

    if cmnd == "power off":
        power_state = "OFF"
        add_log(f"{source} GET /cm?cmnd=Power Off", 'Relay switched OFF → {"POWER":"OFF"}')
        return jsonify({"POWER": "OFF"})

    if cmnd == "power":
        add_log(f"{source} GET /cm?cmnd=Power", f'State read → {{"POWER":"{power_state}"}}')
        return jsonify({"POWER": power_state})

    add_log(f"{source} GET /cm?cmnd={cmnd_raw}", "Unknown command — ignored")
    return jsonify({"WARNING": "Unknown command — ignored"}), 400


@app.route("/cm")
def tasmota_cm():
    return handle_power_command("ADD UI")


@control_app.route("/cm")
def tasmota_cm_port80():
    return handle_power_command(f"Control UI :{CONTROL_PORT}")


@control_app.route("/add")
def add_document_port80():
    """Expose the currently selected ADD document on CONTROL_PORT."""
    add_log(f"Control UI :{CONTROL_PORT} GET /add", "ADD document retrieved")
    return jsonify(active_add)


@control_app.route("/add.html")
def add_document_html_port80():
    """Human-readable view of the currently selected ADD document on CONTROL_PORT."""
    add_log(f"Control UI :{CONTROL_PORT} GET /add.html", "ADD document retrieved as HTML")
    return Response(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{DEVICE_NAME} - ADD</title>"
        "<style>body{background:#252525;color:#eaeaea;font-family:monospace;"
        "padding:24px;}pre{white-space:pre-wrap;word-break:break-word;"
        "background:#1f1f1f;padding:16px;border-radius:6px;}</style>"
        f"</head><body><h2>{DEVICE_NAME}</h2><pre>"
        + json.dumps(active_add, ensure_ascii=False, indent=2)
        + "</pre></body></html>",
        mimetype="text/html"
    )



# ---------------------------------------------------------------------------
# Tasmota-style local control page — CONTROL_PORT
# ---------------------------------------------------------------------------

CONTROL_PAGE = r"""<!DOCTYPE html>
<html lang="en" class="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<link rel="icon" href="data:image/x-icon;base64,AAABAAEAEBACAAEAAQCwAAAAFgAAACgAAAAQAAAAIAAAAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA////AP5/b+H6X2/h8k9v4eZnb+Hud2/h7ndv4e53b+FmZm/hMkxv4ZgZb+HOc2/h5+dv4fPPb+H5n2/h/D9v4f5/b+EAAO4EAADuBAAA7gQAAO4EAADuBAAA7gQAAO4EAADuBAAA7gQAAO4EAADuBAAA7gQAAO4EAADuBAAA7gQAAO4E">
<title>__DEVICE_NAME__ - Main Menu</title>
<script>
var x=null,lt,to,tp,pc='',ft;

function eb(s){return document.getElementById(s);}
function qs(s){return document.querySelector(s);}
function sp(i){eb(i).type=(eb(i).type==='text'?'password':'text');}
function wl(f){window.addEventListener('load',f);}

function la(p){
  var a=p||'';
  clearTimeout(ft);
  clearTimeout(lt);

  if(x!=null){x.abort();}

  x=new XMLHttpRequest();
  x.onreadystatechange=function(){
    if(x.readyState==4 && x.status==200){
      eb('l1').innerHTML=x.responseText;
      clearTimeout(ft);
      clearTimeout(lt);
      lt=setTimeout(la,2345);
    }
  };

  x.open('GET','.?m=1'+a,true);
  x.send();
  ft=setTimeout(la,20000);
}

function lc(v,i,p){
  if(eb('s')){
    if(v=='h'||v=='d'){
      var sl=eb('sl4').value;
      eb('s').style.background='linear-gradient(to right,rgb('+sl+'%,'+sl+'%,'+sl+'%),hsl('+eb('sl2').value+',100%,50%))';
    }
  }
  la('&'+v+i+'='+p);
}

function jd(){
  var t=0,i=document.querySelectorAll('input,button,textarea,select');
  while(i.length>=t){
    if(i[t]){
      i[t]['name']=(i[t].hasAttribute('id')&&(!i[t].hasAttribute('name')))?i[t]['id']:i[t]['name'];
    }
    t++;
  }
}

function sf(s){
  var t=0,i=document.querySelectorAll('.hf');
  while(i.length>=t){
    if(i[t]){i[t].style.display=s?'block':'none';}
    t++;
  }
}

function noAction(ev){
  if(ev){ev.preventDefault();}
  return false;
}

wl(function(){la();});
wl(jd);
</script>
<style>
div,fieldset,input,select{padding:5px;font-size:1em;}
fieldset{background:#4f4f4f;}
p{margin:0.5em 0;}
input{width:100%;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;background:#dddddd;color:#000000;}
input[type=checkbox],input[type=radio]{width:1em;margin-right:6px;vertical-align:-1px;}
input[type=range]{width:99%;}
select{width:100%;background:#dddddd;color:#000000;}
textarea{resize:vertical;width:98%;height:318px;padding:5px;overflow:auto;background:#1f1f1f;color:#65c115;}
body{text-align:center;font-family:verdana,sans-serif;background:#252525;}
td{padding:0px;}
button{border:0;border-radius:0.3rem;background:#1fa3ec;color:#faffff;line-height:2.4rem;font-size:1.2rem;width:100%;-webkit-transition-duration:0.4s;transition-duration:0.4s;cursor:pointer;}
button:hover{background:#0e70a4;}
.bred{background:#d43535;}
.bred:hover{background:#931f1f;}
.bgrn{background:#47c266;}
.bgrn:hover{background:#5aaf6f;}
a{color:#1fa3ec;text-decoration:none;}
.p{float:left;text-align:left;}
.q{float:right;text-align:right;}
.r{border-radius:0.3em;padding:2px;margin:6px 2px;}
.hf{display:none;}
.power-state{
  text-align:center;
  font-size:2.4rem;
  line-height:1.15;
  font-weight:bold;
  padding:8px 5px 12px 5px;
}
.power-state.on{color:#eaeaea;}
.power-state.off{color:#eaeaea;}
</style>
</head>

<body>
<div style="background:#252525;text-align:left;display:inline-block;color:#eaeaea;min-width:340px;">
  <div style="text-align:center;color:#eaeaea;">
    <noscript>To use Tasmota, please enable JavaScript<br></noscript>
    <h3>Generic</h3>
    <h2>__DEVICE_NAME__</h2>
  </div>

  <div style="padding:0;" id="l1" name="l1"><div class="power-state off">OFF</div></div>

  <table style="width:100%">
    <tr>
      <td style="width:100%">
        <button onclick='la("&o=1");'>Toggle</button>
      </td>
    </tr>
    <tr></tr>
  </table>

  <div id="but3d" style="display:block;"></div>

  <p>
    <form id="but3" style="display:block;" action="#" method="get" onsubmit="return noAction(event);">
      <button type="submit">Configuration</button>
    </form>
  </p>

  <p>
    <form id="but4" style="display:block;" action="#" method="get" onsubmit="return noAction(event);">
      <button type="submit">Information</button>
    </form>
  </p>

  <p>
    <form id="but5" style="display:block;" action="#" method="get" onsubmit="return noAction(event);">
      <button type="submit">Firmware Upgrade</button>
    </form>
  </p>

  <p>
    <form id="but14" style="display:block;" action="#" method="get" onsubmit="return noAction(event);">
      <button type="submit">Console</button>
    </form>
  </p>

  <p>
    <form id="but0" style="display:block;" action="#" method="get" onsubmit="return noAction(event);">
      <button type="submit" name="rst" class="button bred">Restart</button>
    </form>
  </p>

  <div style="text-align:right;font-size:11px;">
    <hr/>
    <a href="https://bit.ly/tasmota" target="_blank" style="color:#aaa;">
      Tasmota 14.0.0 (release-tasmota) by Theo Arends
    </a>
  </div>
</div>
</body>
</html>"""


@control_app.route("/")
def control_page():
    """Tasmota-style main page and its lightweight status/toggle endpoint."""
    global power_state

    # AJAX call used by the Tasmota-style page.
    if request.args.get("m") == "1":
        if request.args.get("o") == "1":
            power_state = "OFF" if power_state == "ON" else "ON"
            add_log(
                f"Control UI :{CONTROL_PORT} → Toggle",
                f'Relay switched {power_state} → {{"POWER":"{power_state}"}}'
            )
        else:
            add_log(f"Control UI :{CONTROL_PORT} → State", f'Current state → {{"POWER":"{power_state}"}}')

        css_class = "on" if power_state == "ON" else "off"
        return Response(
            f'<div class="power-state {css_class}">{power_state}</div>',
            mimetype="text/html"
        )

    add_log(f"Control UI :{CONTROL_PORT} → Main Menu", f"{DEVICE_NAME} control page retrieved")
    return Response(CONTROL_PAGE.replace("__DEVICE_NAME__", DEVICE_NAME), mimetype="text/html")


@control_app.route("/favicon.ico")
def control_favicon():
    return Response(status=204)


def run_control_server():
    """Run the local Tasmota-style UI independently on CONTROL_PORT."""
    control_app.run(
        host="0.0.0.0",
        port=CONTROL_PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )


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


@app.route("/api/log/options", methods=["GET", "POST"])
def log_options():
    global SUPPRESS_CONTROL_STATE_LOG, log_entries

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        SUPPRESS_CONTROL_STATE_LOG = bool(data.get("suppress_control_state", False))

        if SUPPRESS_CONTROL_STATE_LOG:
            log_entries = deque(
                (
                    entry for entry in log_entries
                    if not is_control_state_log(
                        str(entry.get("action", "")),
                        str(entry.get("detail", ""))
                    )
                ),
                maxlen=200
            )

    return jsonify({"suppress_control_state": SUPPRESS_CONTROL_STATE_LOG})


@app.route("/api/log/download")
def download_log():
    filename = DEVICE_NAME.lower().replace(" ", "-") + "-log.json"
    return Response(
        json.dumps(list(log_entries), ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/log/clear", methods=["POST"])
def clear_log():
    log_entries.clear()
    return jsonify({"status": "ok"})


@app.route("/api/state")
def get_state():
    return jsonify({"power": power_state})


@app.route("/api/config")
def get_config():
    return jsonify({
        "device_name": DEVICE_NAME,
        "device_host": DEVICE_HOST,
        "add_port": ADD_PORT,
        "control_port": CONTROL_PORT,
        "json_port": JSON_PORT
    })


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------
#
# Gunicorn imports this module as "app:app". Therefore the Control UI server
# must be started during module initialization, not only inside __main__.
#
# IMPORTANT:
# Run Gunicorn with exactly ONE worker. The active ADD preset, relay state and
# live log are intentionally held in this process memory and are shared between
# the Gunicorn threads and the Control UI thread.
#
_control_thread = None
_control_thread_lock = threading.Lock()


def ensure_control_server_started():
    """Start the CONTROL_PORT server exactly once in this process."""
    global _control_thread

    with _control_thread_lock:
        if _control_thread is not None and _control_thread.is_alive():
            return

        _control_thread = threading.Thread(
            target=run_control_server,
            name=DEVICE_NAME.lower().replace(" ", "-") + "-control",
            daemon=True
        )
        _control_thread.start()


# This runs when imported by Gunicorn and when started directly with Python.
ensure_control_server_started()

add_log(
    f"{DEVICE_NAME} started",
    (
        f"Internal ADD port {ADD_PORT}; internal control port {CONTROL_PORT}; "
        f"advertised control endpoint {DEVICE_HOST}:{JSON_PORT}"
    )
)


if __name__ == "__main__":
    # Direct Python start remains available for local development.
    app.run(
        host="0.0.0.0",
        port=ADD_PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )
