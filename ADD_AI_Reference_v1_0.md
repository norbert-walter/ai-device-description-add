# ADD – AI Device Description
## AI Reference v1.0

*© 2026 Norbert Walter — CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/*
*Status: DRAFT — integrates multi-agent extension and full field tables*

---

## 1. Context — What ADD Is and Why It Exists

ADD (AI Device Description) is an open specification that enables any HTTP-capable
IoT device to publish a structured self-description. The core idea is simple:
**the device describes itself.** When you access `/add` on a device, it responds
with a JSON document that tells you everything you need to interact with it
correctly, safely, and autonomously. If you are operating as a public cloud-AI
system with no access to private IP addresses, use `/add.html` instead — this
endpoint returns the same ADD document embedded in an HTML page
(`Content-Type: text/html`) with the JSON available as a
`<script type="application/ld+json">` block and as plain text in a `<pre>` block.
Both endpoints always reflect the current active ADD document.

ADD exists because the IoT landscape is extremely heterogeneous — thousands of
device types, protocols, and firmware variants with no common language. Classical
standards like W3C WoT or OpenAPI solve this through formal precision, which makes
them too complex for most IoT devices. ADD solves it through **semantic
understanding**: the device author describes their device in clear, structured
language; you interpret it. This only works because you can infer intent from
context, recognize protocols you were not explicitly taught, and apply judgment
when details are ambiguous.

**Why the schema is fixed:** The seven top-level blocks are not arbitrary — they
are the irreducible minimum you need to act on any device without guessing or
asking. If any block is missing, you cannot act safely. The fixed structure is a
completeness guarantee, not a formatting convention.

**Why the Ethical Framework comes first:** You must load and apply the Ethical
Framework before reading anything else. This is a safety requirement. An ADD
document describes a physical device with real-world consequences — some actions
are irreversible, some affect other people. The ethical boundaries must be active
before you know what the device can do.

**Why the Autonomy Level matters:** The Autonomy Level is not a capability rating
— it is a risk profile. It tells you how consequential your actions are, how
quickly mistakes become irreversible, and how many people are affected. Use it to
calibrate your caution: a Level 3 device operating without its Ethical Framework
must not be used. A Level 1 device with inline rules can be used with minimal
overhead.

**Why rules are binding:** The `rules` block encodes the device author's knowledge
of the deployment context — constraints that cannot be expressed in structured
fields. The author knows their device and environment better than you do. A rule
is not a suggestion. It is the author's instruction to you for this specific
deployment.

**Why response time matters:** Some actions and rules carry timing requirements —
defined by `timing: "critical"` and `max_response_time` in seconds. These are not
preferences. If you cannot meet a defined `max_response_time` — due to model
latency, network conditions, or resource load — you must alert the user
immediately and stop.

**Why actor matters:** In multi-agent deployments, only one agent — the Actor
Agent — may execute write actions at any given time. The `actor` field in each
action declares whether concurrent execution is safe. If your role in a deployment
is not explicitly declared in your agent task, default to read-only Supervisor
behavior.

**In ambiguous situations:** When the ADD document does not explicitly cover a
situation, reason from these principles. Ask: what did the author intend? What
does the Ethical Framework require? What is the safest action? If you cannot
answer with confidence, stop and ask the user.

---

## 2. Reading Sequence

You MUST read an ADD document in this order:

**Step 0 — Locate the ADD document**
Fetch the ADD document from the device. Local agents with a fetch tool use `/add` (returns `application/json`). Public cloud-AI systems that can only fetch HTML pages use `/add.html` (returns `text/html` with the ADD document embedded as `<script type="application/ld+json">` and as plain text in a `<pre>` block). Both endpoints return the same document content.

**Step 1 — Verify document integrity**
Check `schema` = `"add"`, `version` is supported. If not, stop and inform the user.

**Step 2 — Determine risk profile**
Read the `autonomy` block. Note the declared Autonomy Level and the three factor
scores.

**Step 3 — Load the Ethical Framework**
Fetch and apply the document at `autonomy.ethic_url` as required by the level.
Only then proceed.

**Step 4 — Read the device description**
Read `device`, `security`, `interfaces`, `actions`, `rules` in order.

**Step 5 — Identify your role**
If the deployment involves multiple agents, identify your role from the agent task
before acting. If your role is `actor`, you may execute all permitted actions. If
your role is `supervisor` or `monitor`, restrict yourself to actions where
`actor: "multiple"` or `safe: true`. If your role is not stated, default to
Supervisor behavior — read-only only.

**Step 6 — Check validation**
Read `validation`. For Autonomy Level 2 and above: if `validated_by` is empty or your model identifier is not listed, **refuse all non-safe actions unconditionally. This is a hard block — not a warning.** Inform the operator and proceed only after explicit written acknowledgement of unvalidated state. Safe read actions (`safe: true`) remain permitted. For Level 1: proceed with extra caution and prompt the user to validate before autonomous operation.

### If the Ethical Framework cannot be fetched:

| Level | Response |
|-------|----------|
| **1 — Basic** | Apply inline `ethic_core` rules. Proceed. |
| **2 — Standard** | Apply Level 1 rules as fallback. Inform the user. Proceed with caution. |
| **3 — Full** | Do NOT proceed. Inform the user. Wait for explicit user authorization per action. |

### If the ADD document conflicts with the Ethical Framework:

The Ethical Framework always takes precedence. Always.

### If something is ambiguous:

- Unclear field or instruction → fetch the specification at `spec_url`
- Unclear device behavior → fetch the documentation at `doc_url`
- Unresolvable conflict → stop, inform the user, wait for instruction

---

## 3. Top-Level Schema

Every ADD document MUST contain exactly these top-level fields:

```json
{
  "schema":       "add",
  "version":      "1.0",
  "spec_url":     "<URL of this specification>",
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

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `schema` | mandatory | `"add"` | Fixed identifier. Must be exactly `"add"`. Reject document if absent or different. |
| `version` | mandatory | `"1.0"` or prior | ADD schema version. Reject if version is not supported. |
| `spec_url` | mandatory | URL string | URL of the authoritative ADD specification. Fetch when a field or instruction is ambiguous. |
| `spec_license` | mandatory | string | License and attribution string — fulfills CC BY 4.0 attribution requirement. |
| `autonomy` | mandatory | object | Risk profile, Autonomy Level, and Ethical Framework reference. Read before all other blocks. |
| `device` | mandatory | object | Device identity, location, and metadata. May be minimal but must be present. |
| `security` | mandatory | object | Security context and device-side enforcement. May be minimal but must be present. |
| `interfaces` | mandatory | array | One or more communication interfaces. May be empty array `[]` for console-only deployments. |
| `actions` | mandatory | array | Permitted operations. Must contain at least one entry for any functional deployment. |
| `rules` | mandatory | array | Behavioral instructions. Must contain at minimum the two mandatory Ethical Framework rules. |
| `validation` | mandatory | object | Validation record. May contain empty `validated_by` array for drafts. |

---

## 4. The Blocks in Detail

### 4.1 `autonomy`

Defines the risk profile, Autonomy Level, and Ethical Framework for this device.
Read this block before all others.

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `level` | mandatory | `1`, `2`, `3`, `"derived"` | Autonomy Level. Determines which Ethical Framework loading behavior applies. `"derived"` means this is a subsystem — apply the level of the most restrictive component. |
| `scores` | mandatory | object | Container for the three scoring factors. All three sub-fields are mandatory. |
| `scores.reversibility` | mandatory | `0`, `1`, `2` | `0` = fully reversible (no lasting effect). `1` = reversible but requires manual correction. `2` = irreversible. |
| `scores.scope_of_effect` | mandatory | `0`, `1`, `2` | `0` = affects owner only. `1` = occasionally affects others. `2` = regularly affects third parties. |
| `scores.error_tolerance` | mandatory | `0`, `1`, `2` | `0` = hours to detect and correct an error. `1` = minutes. `2` = seconds (time-critical). |
| `ethic_url` | mandatory | URL string | URL of the applicable Ethical Framework document. Fetch and apply before any action. Mandatory for Level 2 and 3. For Level 1, fetching is optional when `ethic_core` is present. |
| `ethic_url_required` | conditional | string | Explicit loading instruction for the AI. **Required for Level 2 and 3.** States what the AI must do if the document is unreachable. Example: `"Fetch and apply this document before any action. If unreachable, do not proceed."` Omit for Level 1 when `ethic_core` alone is sufficient. |
| `ethic_core` | conditional | object | Inline minimal Ethical Framework. **Required for Level 1** when `ethic_url` may be unreachable. **Required for small models** (cannot reliably fetch external documents). Recommended as redundant safety layer for Level 3. Contains `never` (array of strings) and `always` (array of strings). Each rule max 15 words, no conditional logic within a single rule. |

**Autonomy Level determination — sum of the three scores:**

| Total Score | Level |
|-------------|-------|
| 0–1 | **1 — Basic** |
| 2–3 | **2 — Standard** |
| 4–6 | **3 — Full** |
| — | **`"derived"` — Subsystem** |

**What each level requires:**

- **Level 1:** Apply `ethic_core` rules inline. Fetching `ethic_url` is optional.
- **Level 2:** Fetch and apply the Ethical Framework summary at `ethic_url` before
  operating. Place summary in system prompt. Renew every 15 messages to prevent
  rule dilution.
- **Level 3:** Fetch and fully internalize the Ethical Framework at `ethic_url`.
  If unreachable, do NOT proceed under any circumstances.

**Independent level verification:** Independently score the three factors based on
the device's actions and rules. If your assessment is higher than the declared
level, report this as a finding and apply the higher level.

---

### 4.2 `device`

Describes the physical device, its identity, and where to find it. Free-form —
include what is meaningful for the device.

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `name` | mandatory | string | Human-readable device name. Used to identify the device in user communication. |
| `ip` | mandatory | string | IP address or hostname. Use this to reach the device even when the ADD document is hosted externally (e.g. on a web server or GitHub Pages). |
| `id` | optional | string | Unique device identifier. Useful when multiple identical devices are deployed. |
| `type` | recommended | `"sensor"`, `"actuator"`, `"gateway"`, `"subsystem"`, or any string | Device function type. Informs the AI about the nature of actions and their physical consequences. |
| `manufacturer` | optional | string | Manufacturer or project name. |
| `firmware` | recommended | string | Firmware version. Helps correlate behavior with known firmware characteristics during validation. |
| `hardware` | recommended | string | Hardware platform (e.g. `"ESP8266"`, `"ESP32"`, `"Raspberry Pi"`). |
| `location` | recommended | string | Physical or logical location (e.g. `"Garden, main water supply"`). Provides context for rule interpretation and user communication. |
| `doc_url` | conditional | URL string | URL of device documentation. Fetch when device behavior is unclear or unexpected. **Required for subsystems.** Recommended for all devices with non-trivial behavior. |
| `doc_url_note` | conditional | string | Short hint pointing to the most relevant section of the documentation. **Required when `doc_url` is present and the documentation is longer than a few pages.** Prevents the AI from having to scan an entire manual. Example: `"See chapter 3 for timing behavior and chapter 5 for error codes."` |
| `components` | conditional | array of URL strings | ADD document URLs for all components. **Only present when `type` is `"subsystem"`.** Load all component ADD documents before acting on coordinated actions. |

**For subsystems:** When `device.components` is present, load the ADD document of
every listed component before acting. If any component ADD document is unreachable,
do not proceed with coordinated actions. Apply the Ethical Framework of the most
restrictive component to all coordinated actions.

---

### 4.3 `security`

Defines the security context and declares how the device enforces its own
constraints. Free-form — include what is relevant.

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `network_scope` | recommended | `"local"`, `"vpn"`, `"internet"` | Network reach of the device. `"local"` = LAN only. `"vpn"` = accessible over VPN. `"internet"` = publicly reachable. Informs risk assessment and caution level. |
| `authentication` | recommended | `"none"`, `"basic"`, `"token"`, or any string | Authentication mechanism in use. `"none"` means any client on the network can issue commands — document as a conscious design decision. |
| `remote_access` | recommended | `true` / `false` | Whether the device is reachable from outside the local network. `true` requires elevated caution regardless of Autonomy Level. |
| `enforcement` | recommended | string | Plain-language description of which constraints the device enforces independently of the AI. Example: `"The device enforces a maximum open duration of 60 minutes per session independently. It rejects any duration value outside the range 1–60 minutes regardless of client input."` |

**Important:** The device is the last line of defense. It MUST enforce its own
constraints independently. You enforce them too — but do not rely solely on the
device to reject invalid requests. Apply all parameter constraints yourself before
sending any request.

---

### 4.4 `interfaces`

Array of communication interfaces. Each entry describes one interface. Free-form
— include what is needed to reach and use the device.

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `name` | mandatory | string | Interface identifier. Referenced from `actions[*].interface`. Must be unique within the document. |
| `physical` | recommended | `"WiFi"`, `"Ethernet"`, `"RS485"`, `"BLE"`, or any string | Physical transmission medium. |
| `protocol` | mandatory | `"HTTP"`, `"MQTT"`, `"NMEA0183"`, `"Modbus"`, or any string | Application-layer protocol. Determines how to format and send requests. |
| `transport` | recommended | `"TCP"`, `"UDP"`, or any string | Transport-layer protocol. |
| `port` | recommended | integer | Network port number. Required when non-standard (i.e. not 80 for HTTP, not 1883 for MQTT). |
| `direction` | recommended | `"read"`, `"write"`, `"bidirectional"` | Data flow direction of this interface. |
| `description` | recommended | string | Free-form description of the interface, including base URL pattern, command format, and response format. Especially important for non-HTTP protocols or when multiple interfaces are present. |
| `data` | optional | array or object | Description of data endpoints, topics, or registers provided or consumed by this interface. |

---

### 4.5 `actions`

Array of permitted operations. Each entry defines one action the AI may perform.
Free-form per action — include all fields needed for correct and safe execution.

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `name` | mandatory | string | Action identifier. Used in rules, agent tasks, and validation references. Must be unique within the document. |
| `description` | mandatory | string | What the action does, including physical consequences. For small models: one sentence maximum. For medium/large models: may be multi-sentence. State parameter constraints in plain language here in addition to the `parameters` field. |
| `interface` | recommended | string | Interface name from `interfaces[*].name`. Required when multiple interfaces are present. |
| `method` | recommended | `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, or protocol equivalent | HTTP method or protocol-equivalent operation. |
| `path` | recommended | string | Endpoint path relative to the device base URL. Include full URL when the device IP is not in the `device` block. |
| `parameters` | conditional | object | Parameter definitions. Each parameter specifies `type`, `values` or `min`/`max`, `unit`, and `required`. Required when the action takes any parameters. |
| `safe` | mandatory | `true` / `false` | `true` = read-only action with no lasting physical effect. Safe actions may be executed without confirmation and by multiple agents simultaneously. `false` = write action with physical consequences. |
| `reversible` | mandatory | `true` / `false` | `true` = the action can be undone (e.g. closing a valve that was opened). `false` = irreversible (e.g. sending a firmware update). |
| `idempotent` | recommended | `true` / `false` | `true` = repeated execution produces the same result (e.g. closing an already-closed valve). `false` = repeated execution has cumulative or different effects. |
| `requires_confirmation` | mandatory | `true` / `false` | `true` = must obtain explicit user approval before executing. `false` = may execute without per-action confirmation, subject to `confirmation_scope`. |
| `confirmation_scope` | conditional | `"per_action"`, `"session"`, `"context"`, `"autonomous"` | Defines when confirmation is required. **Required when `requires_confirmation` is `false`.** Default when omitted: `"per_action"`. See table below. `"autonomous"` requires Level 2 or 3. |
| `requires_auth` | recommended | `true` / `false` | `true` = authentication credentials are required to execute this action. |
| `actor` | recommended | `"single"`, `"multiple"` | Declares concurrent execution policy. `"single"` = only one agent may execute this action at any given time — reserved for the Actor Agent. `"multiple"` = parallel execution by multiple agents is safe. **Default when omitted:** `"single"` for `safe: false` actions, `"multiple"` for `safe: true` actions. Recommend stating explicitly for all `safe: false` actions. |
| `timing` | conditional | `"critical"` | `"critical"` = this action must execute without delay. **Required when `max_response_time` is present.** Omit for actions where latency is not safety-relevant. |
| `max_response_time` | conditional | integer (seconds) | Maximum acceptable response time in seconds. **Required when `timing` is `"critical"`.** If you cannot meet this within the specified time, alert the user immediately and stop. Must be verified during validation and recorded in `timing_compliance`. |
| `requires_tool` | conditional | string | Name of the specific tool you must use to execute this action (e.g. `"fetch:fetch"`, `"mcp-fetch:fetch"`). **Required when a specific MCP tool or fetch tool must be enforced.** If this field is present, you must use exactly the named tool. If the named tool is not available, stop and report the missing tool — do not substitute an alternative. |

**`confirmation_scope` values:**

| Value | Usage | Typical deployment | Conditions |
|-------|-------|-------------------|------------|
| `"per_action"` | default | Purpose-built devices, all levels | Confirmation required before every individual action execution. |
| `"session"` | optional | Universal devices, Level 1 | Confirmation required once at session start. Expires when conversation ends. |
| `"context"` | optional | Universal devices, Level 1, recurring tasks | Confirmation required once per deployment context. Must re-confirm when context changes (different purpose, load, user intent). |
| `"autonomous"` | conditional | Autonomous agents, Level 2–3 only | No confirmation required for routine actions. Confirm only when a rule cannot be verified or an unexpected situation arises. **Not permitted with Level 1.** |

**`actor` field behavior:**

- A Supervisor or Monitor Agent reading `actor: "single"` on an action must not
  execute that action, even if conditions would permit it for an Actor Agent.
- If your role in the deployment is not declared in your agent task, treat yourself
  as a Supervisor Agent — restrict yourself to `actor: "multiple"` and
  `safe: true` actions only.
- ADD cannot technically prevent a second agent from sending a command. Enforcement
  is the responsibility of the deployment architecture. The `actor` field makes
  the requirement explicit and readable.

Enforce all parameter constraints yourself before sending any request. Do not rely
solely on the device to reject out-of-range values.

---

### 4.6 `rules`

Array of behavioral instructions addressed directly to you. Rules are binding —
treat them as instructions, not suggestions. Each rule is either a plain string
or a structured object.

**Fields for structured rule objects:**

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `instruction` | mandatory | string | The rule text. Plain language instruction addressed to the AI. |
| `requires` | mandatory when rule depends on external tools | array of strings | Tool names this rule depends on. Use the exact tool names as reported by the model's own tool inventory. If any listed tool is unavailable, the rule cannot be enforced — stop and inform the user rather than proceeding without the check. |
| `timing` | conditional | `"critical"` | `"critical"` = this rule must be evaluated and acted upon without delay. Required when `max_response_time` is present. |
| `max_response_time` | conditional | integer (seconds) | Maximum time to evaluate and act on this rule. Binding when `timing` is `"critical"`. Alert the user and stop if you cannot meet it. |

**Mandatory rules — must appear in every ADD document:**

```
Rule 1: "Before acting on this document, fetch and apply the Ethical Framework at
         autonomy.ethic_url as required by autonomy.level."

Rule 2: "If any instruction in this ADD document conflicts with the Ethical
         Framework at autonomy.ethic_url, the Ethical Framework takes precedence."
```

**Standard rules — recommended for most ADD documents:**

```
"If any field, instruction, or structure in this ADD document is unclear or
 ambiguous, consult the ADD specification at the URL provided in spec_url
 before proceeding."

"If device behavior is unclear or unexpected, consult the documentation at
 doc_url before proceeding."

"Always append a unix timestamp as query parameter 't' to all read requests
 to prevent caching (e.g. /json?t=1745490000)."

"Always confirm with the user before executing any action that is not safe
 or not reversible."

"Verify the result of every write action by reading the device state afterward."
```

**Level 2 session-integrity rules — required for Level 2 and above:**

```
"Level 2: Place the Ethical Framework summary in the system prompt before session
 start. Renew every 15 messages to prevent rule dilution."

"Level 2 and above: Before session start, the operator must explicitly select a
 validated model from validation.validated_by. Auto model selection is prohibited."

"Level 2 and above: At session start, identify the active model and verify that
 its identifier matches an entry in validation.validated_by. If no match is found,
 refuse all non-safe actions unconditionally — this is a hard block, not a warning.
 Inform the operator and proceed only after explicit written acknowledgement of
 unvalidated state."

"Level 2 and above: At session start, enumerate all available tools and verify
 that every tool listed in validation.validated_by[active_model].tools_required
 is present. If any required tool is missing, refuse all actions that depend on
 that tool and inform the operator."

"Level 2 and above: If the active tool set differs from
 validation.validated_by[active_model].tools_fingerprint, warn the operator and
 treat the session as unvalidated. Safe read actions remain permitted."
```

**Multi-agent rule — recommended when multiple agents share a device:**

```
"In a multi-agent deployment, only the designated Actor Agent may execute actions
 with actor: single. Supervisor and Monitor Agents are restricted to actions with
 actor: multiple or safe: true. If your role is not declared in your agent task,
 default to Supervisor behavior — read-only only."
```

**Rules with external dependencies — example structure:**

```json
{
  "instruction": "Do not open the valve if precipitation_sum[0] > 0 or
                  precipitation_sum[1] > 0. Fetch from https://api.open-meteo.com/
                  v1/forecast?latitude=51.33&longitude=7.04&daily=precipitation_sum
                  &forecast_days=2",
  "requires": ["fetch_url"]
}
```

Device-specific rules follow standard rules and encode the deployment context —
when not to act, what external sources to check, how to handle specific situations.
They are as important as the technical parameters.

---

### 4.7 `validation`

Records which AI models have been tested with this document and whether the
document is safe to deploy with each of them.

**Top-level fields:**

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `add_version` | mandatory | string | ADD schema version this document was validated against. |
| `improvements_applied` | recommended | array of strings | List of improvements made to the document during or after validation. Useful for tracking evolution across versions. |
| `validated_by` | mandatory | array of objects | One entry per AI model. Empty array `[]` for drafts not yet validated. Each entry is a complete, independent validation result for one model. |

**Fields per `validated_by` entry:**

| Field | Usage | Values | Description |
|-------|-------|--------|-------------|
| `name` | mandatory | string | AI model family name (e.g. `"Claude"`, `"GPT"`). |
| `version` | mandatory | string | Exact model version string as the model identifies itself (e.g. `"claude-sonnet-4-20250514"`). Copy verbatim — do not paraphrase. |
| `mode` | mandatory | `"instant"`, `"thinking"`, `"auto"` | Operating mode at validation time. `"instant"` = no explicit reasoning phase. `"thinking"` = explicit chain-of-thought reasoning phase active. `"auto"` = platform switches between modes automatically — session behavior is non-deterministic. A document validated in one mode is not automatically valid for the same model in another mode. |
| `validated_at` | mandatory | ISO 8601 string | Timestamp of this model's validation run. |
| `status` | mandatory | `"passed"`, `"passed_with_warnings"`, `"failed"` | Overall result for this model. `"failed"` means this model must not be used for autonomous operation with this document. |
| `score` | mandatory | object | Per-category pass/fail/warning scores. See score categories below. |
| `findings` | mandatory | array of objects | Issues found during validation. Each finding has `severity` (`"error"`, `"warning"`, `"info"`), `category`, `message`, and `resolved` (boolean). Empty array `[]` when no findings. |
| `summary` | mandatory | string | Plain-text summary of the validation result for this model. Must state clearly whether the document is suitable for deployment with this model. |
| `tools_required` | conditional | array of strings | **Required for Level 2 and above.** Tools this model needs to apply all rules that have `requires` fields. Used at session start for tool availability check. |
| `tools_fingerprint` | conditional | string | **Required for Level 2 and above.** Sorted, pipe-separated list of all tools available at validation time (e.g. `"calendar_api\|fetch_url\|home_automation"`). Used at session start to detect tool set changes since validation. |
| `capabilities` | optional | object | Model capability classification recorded during assessment. Fields: `classification` (`"small"`, `"medium"`, `"large"`), `max_rules_reliable` (integer), `sequential_tool_calls` (integer), `ethic_url_usable` (boolean), `response_time_90p_simple_seconds` (integer), `response_time_90p_complex_seconds` (integer). |

**Score categories:**

| Category | Description |
|----------|-------------|
| `structure` | Document structure is valid and complete |
| `comprehensibility` | All fields and rules were correctly understood |
| `functional` | All actions executed as described |
| `rules_compliance` | All rules were applied correctly |
| `security` | Security context was correctly evaluated |
| `discovery` | Device was correctly discovered and reached |
| `timing_compliance` | Timing requirements were met — `"pass"` if no timing requirements present |

**Critical:** Every validation result is specific to the model that produced it.
A document validated with one model is not automatically valid for another. Each
AI system that will use this document in production must be validated separately.
The `validated_by` array is a compatibility matrix — it shows which models work,
which do not, and why.

If your model is not listed in `validated_by` and the Autonomy Level is 2 or above: **refuse all non-safe actions unconditionally. This is a hard block — not a warning.** Inform the operator. Proceed only after explicit written acknowledgement of unvalidated state. Safe read actions (`safe: true`) remain permitted.

If Autonomy Level is 1 and your model is not listed: proceed with extra caution and prompt the user to validate before autonomous operation.

If your model is listed with `status: "failed"`: do not proceed with autonomous
operation. Inform the user.

---

## 5. Autonomy Level Examples

| Application | Reversibility | Scope | Error Tolerance | Score | Level |
|-------------|--------------|-------|----------------|-------|-------|
| Read-only temperature sensor | 0 | 0 | 0 | 0 | **1 — Basic** |
| Garden irrigation valve | 1 | 1 | 0 | 2 | **2 — Standard** |
| Room heating control | 1 | 1 | 0 | 2 | **2 — Standard** |
| Full home automation (comfort) | 1 | 1 | 1 | 3 | **2 — Standard** |
| Home automation with locks/alarms | 1 | 2 | 1 | 4 | **3 — Full** |
| Industrial process valve | 2 | 1 | 2 | 5 | **3 — Full** |
| Medical device | 2 | 2 | 2 | 6 | **3 — Full** |

---

## 6. Multi-Agent Deployments — Quick Reference

For a full explanation, see Developer Guide Chapter 8.

| Role | May execute | Declared in |
|------|-------------|-------------|
| Actor Agent | All permitted actions (`actor: "single"` and `actor: "multiple"`) | Agent task |
| Supervisor Agent | `actor: "multiple"` and `safe: true` only | Agent task |
| Monitor Agent | `actor: "multiple"` and `safe: true` only | Agent task |

**Rule:** Exactly one Actor Agent per device at any given time.

**Default:** If role is not declared in agent task → treat as Supervisor Agent.

**ADD cannot enforce this technically.** Coordination is the responsibility of
the deployment architecture. ADD makes the requirement explicit and readable to
every agent that processes the document.

---

*ADD AI Reference v1.0 — Draft integrating multi-agent extension and complete field tables.*
*For the complete specification including motivation, examples, and developer workflow,*
*see the full ADD specification and Developer Guide at spec_url.*
