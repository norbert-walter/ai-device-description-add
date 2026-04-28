# ADD Examples — By Model Size

This directory contains ADD documents optimized for specific AI model sizes. The same physical device may need a different ADD document depending on which AI system will use it.

---

## Why Model Size Matters for ADD

A frontier-class model (GPT-4o, Claude Sonnet, Gemini Ultra) and a small local model (7B–13B parameters, running on a Raspberry Pi or edge device) have fundamentally different capabilities when reading and applying an ADD document:

| Capability | Small Model | Large Model |
|---|---|---|
| Reading complex nested JSON | Limited | Full |
| Inferring intent from loose descriptions | Weak | Strong |
| Fetching and applying external Ethical Framework | Often not possible | Standard |
| Following long rule lists reliably | Degrades beyond ~8 rules | Reliable up to 20+ rules |
| Recognizing niche protocols from description | Weak | Strong |
| Handling ambiguity in field descriptions | Weak | Strong |

This means: **an ADD document that works perfectly with a large model may fail silently with a small model.**

---

## Guidelines for Small Models (< 13B parameters)

Small models are appropriate for Level 1 deployments and simple Level 2 devices where the AI runs locally on constrained hardware.

**DO:**
- Use `ethic_core` instead of `ethic_url` — small models often cannot fetch external documents
- Keep the `rules` block to 8 rules or fewer — reliability drops significantly beyond this
- Use simple, direct language in all descriptions — no compound sentences, no relative clauses
- Specify every parameter explicitly — do not rely on inference
- Use only one interface — multiple interfaces increase parsing complexity
- Keep action descriptions to one sentence each
- Use concrete values instead of references: write `"min": 1, "max": 60"` not `"see device documentation"`
- Test with the specific model and firmware version you will deploy

**AVOID:**
- Nested parameter objects more than two levels deep
- Rules that reference other rules or create conditional chains
- Interface descriptions that require understanding a niche protocol
- Any instruction that requires the model to fetch external content
- Ambiguous field names that could be misinterpreted
- Long `description` strings — keep them under 20 words

**Ethical Framework for small models:**
Small models MUST use `ethic_core` with inline rules rather than `ethic_url`. The inline rules should be:
- Maximum 5 `never` rules
- Maximum 5 `always` rules
- Each rule maximum 15 words
- No conditional logic within a single rule

---

## Guidelines for Medium Models (13B–70B parameters)

Medium models are appropriate for Level 1 and Level 2 deployments where the AI runs on a local server or capable edge device.

**DO:**
- You may use `ethic_url` if the model has network access, but include `ethic_core` as fallback
- Keep the `rules` block to 12 rules or fewer
- Descriptions can be two to three sentences
- Multiple interfaces are supported
- Niche protocols should be described with an analogy to a familiar protocol

**AVOID:**
- Relying on the model to infer unstated parameter constraints
- Rules with complex conditional logic
- Expecting the model to maintain context across very long ADD documents (> 300 lines)

---

## Guidelines for Large / Frontier Models

Large frontier models (GPT-4o, Claude Sonnet/Opus, Gemini Ultra) are appropriate for all Autonomy Levels including Level 3 critical infrastructure.

**These models can handle:**
- Full `ethic_url` fetch and application
- Complex nested JSON structures
- Long rule lists (20+ rules)
- Niche protocol descriptions from context alone
- Ambiguous descriptions with reasonable inference
- Long ADD documents with rich detail

**Even for large models:**
- Be explicit about safety-critical constraints — do not rely on inference for anything that matters
- Level 3 devices MUST be validated with the specific frontier model that will be used in production
- Two independent frontier models should validate Level 3 critical infrastructure

---

## File Naming Convention

Files in this directory follow the pattern:
`device-type-level-modelsize.json`

Examples:
- `temperature-sensor-basic-small.json` — Level 1 sensor, optimized for small models
- `irrigation-valve-standard-medium.json` — Level 2 actuator, optimized for medium models
- `cnc-machine-full-large.json` — Level 3 machine, requires frontier model

---

## The Same Device, Two ADD Documents

To illustrate the difference, this directory includes the irrigation valve (Level 2) in two versions:

- `irrigation-valve-standard-small.json` — for a small local model running on a home server
- `irrigation-valve-standard-large.json` — the full version from the main example collection

Comparing these two documents shows concretely what must be simplified for small models and what the tradeoffs are.
