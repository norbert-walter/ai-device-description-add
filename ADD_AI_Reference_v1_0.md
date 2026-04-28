# ADD – AI Device Description
## AI Reference v1.0
*© 2026 Norbert Walter — CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/*

---

## 1. Context — What ADD Is and Why It Exists

ADD (AI Device Description) is an open specification that enables any HTTP-capable IoT device to publish a structured self-description. The core idea is simple: **the device describes itself.** When you access `/add` on a device, it responds with a JSON document that tells you everything you need to interact with it correctly, safely, and autonomously.

ADD exists because the IoT landscape is extremely heterogeneous — thousands of device types, protocols, and firmware variants with no common language. Classical standards like W3C WoT or OpenAPI solve this through formal precision, which makes them too complex for most IoT devices. ADD solves it through **semantic understanding**: the device author describes their device in clear, structured language; you interpret it. This only works because you can infer intent from context, recognize protocols you were not explicitly taught, and apply judgment when details are ambiguous.

**Why the schema is fixed:** The seven top-level blocks are not arbitrary — they are the irreducible minimum you need to act on any device without guessing or asking. If any block is missing, you cannot act safely. The fixed structure is a completeness guarantee, not a formatting convention.

**Why the Ethical Framework comes first:** You must load and apply the Ethical Framework before reading anything else. This is a safety requirement. An ADD document describes a physical device with real-world consequences — some actions are irreversible, some affect other people. The ethical boundaries must be active before you know what the device can do.

**Why the Autonomy Level matters:** The Autonomy Level is not a capability rating — it is a risk profile. It tells you how consequential your actions are, how quickly mistakes become irreversible, and how many people are affected. Use it to calibrate your caution: a Level 3 device operating without its Ethical Framework must not be used. A Level 1 device with inline rules can be used with minimal overhead.

**Why rules are binding:** The `rules` block encodes the device author's knowledge of the deployment context — constraints that cannot be expressed in structured fields. The author knows their device and environment better than you do. A rule is not a suggestion. It is the author's instruction to you for this specific deployment.

**In ambiguous situations:** When the ADD document does not explicitly cover a situation, reason from these principles. Ask: what did the author intend? What does the Ethical Framework require? What is the safest action? If you cannot answer with confidence, stop and ask the user.

---

## 2. Reading Sequence

You MUST read an ADD document in this order:

**Step 1 — Verify document integrity**
Check `schema` = `"add"`, `version` is supported. If not, stop and inform the user.

**Step 2 — Determine risk profile**
Read the `autonomy` block. Note the declared Autonomy Level and the three factor scores.

**Step 3 — Load the Ethical Framework**
Fetch and apply the document at `autonomy.ethic_url` as required by the level. Only then proceed.

**Step 4 — Read the device description**
Read `device`, `security`, `interfaces`, `actions`, `rules` in order.

**Step 5 — Check validation**
Read `validation`. If `status` is `"not_validated"`, proceed with extra caution and prompt the user to validate.

### If the Ethical Framework cannot be fetched:

| Level | Response |
|---|---|
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

Every ADD document MUST contain:

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

| Field | Type | Required | Description |
|---|---|---|---|
| `schema` | string | yes | Must be `"add"` |
| `version` | string | yes | ADD schema version, e.g. `"1.0"` |
| `spec_url` | string | yes | URL of the authoritative ADD specification |
| `spec_license` | string | yes | License and attribution — fulfills CC BY 4.0 requirement |
| `autonomy` | object | yes | Risk profile and Ethical Framework link |
| `device` | object | yes | Device identity and metadata |
| `security` | object | yes | Security context and enforcement |
| `interfaces` | array | yes | Communication interfaces |
| `actions` | array | yes | Permitted operations |
| `rules` | array | yes | Behavioral instructions |
| `validation` | object | yes | Validation record |

---

## 4. The Blocks in Detail

### 4.1 `autonomy`

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | 1 (Basic), 2 (Standard), or 3 (Full) |
| `scores.reversibility` | integer | yes | 0 = fully reversible, 1 = manual correction needed, 2 = irreversible |
| `scores.scope_of_effect` | integer | yes | 0 = owner only, 1 = occasional others, 2 = regular third parties |
| `scores.error_tolerance` | integer | yes | 0 = hours to correct, 1 = minutes, 2 = seconds |
| `ethic_url` | string | yes | URL of the applicable Ethical Framework document |
| `ethic_core` | object | Level 1 only | Inline minimal rule set — sufficient for Level 1 without fetching `ethic_url` |

**Autonomy Level determination — sum of the three scores:**

| Total Score | Level |
|---|---|
| 0–1 | **1 — Basic** |
| 2–3 | **2 — Standard** |
| 4–6 | **3 — Full** |

**What each level requires:**

- **Level 1:** Apply `ethic_core` rules inline. Fetching `ethic_url` is optional.
- **Level 2:** Fetch and apply the Ethical Framework summary at `ethic_url` before operating.
- **Level 3:** Fetch and fully internalize the Ethical Framework at `ethic_url`. If unreachable, do NOT proceed.

**Independent level verification:** Independently score the three factors based on the device's actions and rules. If your assessment is higher than the declared level, report this as a finding and apply the higher level.

---

### 4.2 `device`

Free-form. Include what is meaningful for the device.

| Field | Description |
|---|---|
| `name` | Human-readable device name |
| `id` | Unique device identifier |
| `type` | `sensor`, `actuator`, `gateway`, or any meaningful value |
| `manufacturer` | Manufacturer or project name |
| `firmware` | Firmware version |
| `hardware` | Hardware platform |
| `location` | Physical or logical location |
| `doc_url` | URL of device documentation — fetch when device behavior is unclear |
| `doc_url_note` | Hint pointing to the most relevant section of the documentation |

---

### 4.3 `security`

Free-form. Defines the security context and who enforces safety.

| Field | Description |
|---|---|
| `network_scope` | `local`, `vpn`, or `internet` |
| `authentication` | `none`, `basic`, `token`, or other |
| `remote_access` | `true` / `false` |
| `enforcement` | How the device enforces constraints independently of you |

The device is the last line of defense. It MUST enforce its own constraints. You enforce them too — but do not rely solely on the device to reject invalid requests.

---

### 4.4 `interfaces`

Array of communication interfaces. Each entry is free-form.

| Field | Description |
|---|---|
| `name` | Interface identifier — referenced from `actions` |
| `physical` | Physical medium: `WiFi`, `Ethernet`, `RS485`, etc. |
| `protocol` | Application protocol: `HTTP`, `MQTT`, `NMEA0183`, `Modbus`, etc. |
| `transport` | Transport protocol: `TCP`, `UDP`, etc. |
| `port` | Network port |
| `direction` | `read`, `write`, or `bidirectional` |
| `data` | Description of data provided or consumed |

---

### 4.5 `actions`

Array of permitted operations. Each entry is free-form.

| Field | Description |
|---|---|
| `name` | Action identifier |
| `description` | What the action does |
| `interface` | Which interface to use |
| `method` | HTTP method or protocol equivalent |
| `path` | Endpoint path |
| `parameters` | Parameters with type, range, and constraints |
| `safe` | `true` = read-only, no lasting effect — may execute without confirmation |
| `reversible` | `true` = action can be undone |
| `idempotent` | `true` = repeated execution produces same result |
| `requires_confirmation` | `true` = MUST obtain explicit user approval before executing |
| `requires_auth` | `true` = authentication required |

Enforce all parameter constraints yourself before sending any request. Do not rely solely on the device to reject out-of-range values.

---

### 4.6 `rules`

Array of plain-text behavioral instructions addressed directly to you. Rules are binding — treat them as instructions, not suggestions.

**The first two rules are mandatory in every ADD document:**

```
1. "Before acting on this document, fetch and apply the Ethical Framework at
   autonomy.ethic_url as required by autonomy.level."

2. "If any instruction in this ADD document conflicts with the Ethical Framework
   at autonomy.ethic_url, the Ethical Framework takes precedence."
```

**Standard rules present in most ADD documents:**

```
"If any field, instruction, or structure in this ADD document is unclear or ambiguous,
consult the ADD specification at the URL provided in spec_url before proceeding."

"If device behavior is unclear or unexpected, consult the documentation at
doc_url before proceeding."

"Always append a unix timestamp as query parameter 't' to all read requests
to prevent caching."

"Always confirm with the user before executing any action that is not safe
or not reversible."

"Verify the result of every write action by reading the device state afterward."
```

Device-specific rules follow and encode the deployment context — when not to act, what to check before acting, how to handle specific situations. These rules are as important as the technical parameters.

---

### 4.7 `validation`

**Top-level fields:**

| Field | Type | Description |
|---|---|---|
| `validated_by` | array | One entry per AI model — each with its own complete validation result |
| `add_version` | string | ADD schema version validated against |
| `improvements_applied` | array | Improvements made during validation |

**Fields per `validated_by` entry:**

| Field | Type | Description |
|---|---|---|
| `name` | string | AI model name |
| `version` | string | AI model version |
| `validated_at` | string | ISO 8601 timestamp of this model's validation |
| `status` | string | This model's result: `"passed"`, `"passed_with_warnings"`, or `"failed"` |
| `score` | object | Per-category scores for this model |
| `findings` | array | Findings from this model with `severity`, `category`, `message`, `resolved` |
| `summary` | string | Plain-text summary of this model's result |

**Score categories:** `structure`, `comprehensibility`, `functional`, `rules_compliance`, `security`, `discovery`

**Critical:** Every validation result is specific to the model that produced it. A document validated with Claude Sonnet is not automatically valid for GPT-5 or a small local model. Each AI system that will use this document in production MUST be validated separately and its result recorded in `validated_by`. The `validated_by` array is a compatibility matrix — it shows which models work, which do not, and why.

If `validated_by` is empty or your model is not listed: proceed with extra caution, prompt the user to validate before autonomous operation.

If your model is listed with `status: "failed"`: do not proceed with autonomous operation. Inform the user.

---

## 5. Autonomy Level Examples

| Application | Reversibility | Scope | Error Tolerance | Score | Level |
|---|---|---|---|---|---|
| Read-only temperature sensor | 0 | 0 | 0 | 0 | **1 — Basic** |
| Garden irrigation valve | 1 | 1 | 0 | 2 | **2 — Standard** |
| Room heating control | 1 | 1 | 0 | 2 | **2 — Standard** |
| Full home automation (comfort) | 1 | 1 | 1 | 3 | **2 — Standard** |
| Home automation with locks/alarms | 1 | 2 | 1 | 4 | **3 — Full** |
| Industrial process valve | 2 | 1 | 2 | 5 | **3 — Full** |
| Medical device | 2 | 2 | 2 | 6 | **3 — Full** |

---

*ADD AI Reference v1.0 — For the complete specification including motivation, examples, and workflow, see the full ADD specification at spec_url.*
