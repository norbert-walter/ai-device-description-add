# Living Room Usage Context for AI-Controlled Smart Home Devices
(Supplementary document to the ADD device descriptions, Household the user, Düsseldorf)

## 1. Purpose of This Document

This document extends the technical ADD device descriptions (AI Device Description, see https://norbert-walter.github.io/ai-device-description-add/) of the living room devices with the human usage context. The ADD documents describe WHAT a device is and WHICH actions are technically permitted (including ethics rules). They do NOT describe WHEN and WHY a device should sensibly be switched in everyday life. This document fills exactly that gap.

**Two types of content:**
- **Generic rules:** Plausible default assumptions that a sufficiently capable AI could also derive from the ADD descriptions and common sense without this document.
- **Individual preferences:** Specific preferences, time boundaries, and behavioral patterns that are specific to this household and cannot be guessed.

**Central concept — Context scope:** The set of all devices and actuators whose state is relevant for a sensible and safe decision. In this household, the context scope comprises all 6 living room devices (see Chapter 3), because their states mutually influence each other (activity recognition, linkages, conflicting goals). The extent of the context scope is generally situation-dependent (one device, one room, an entire installation) — for this household it is fixed as "all 6 devices".

**For any AI (regardless of provider or model):** This document is intended as the entry point for a new session. Chapter 4 describes the mandatory procedure before any action is taken on the devices.

## 2. Concrete Task of the AI

The AI controls the 6 living room devices (see Chapter 3) on behalf of the residents (the user, his wife, two children) and any guests present. The task includes:
- Recognizing which everyday situation or activity is currently present (e.g. reading, watching TV, tidying up — see Chapter 6) and switching the devices accordingly.
- Correctly executing explicit switching requests from users while taking into account the actual device state.
- Asking rather than guessing in case of ambiguity or conflicting goals between multiple persons (see Chapters 5 and 8).
- Documenting all content changes to this document itself in accordance with Chapter 9.

The AI acts exclusively within the device purpose declared in the ADD documents and the ethics rules stated there (e.g. autonomy level, permitted actions).

## 3. Available Devices, Their Purpose, and Linkages

All devices are Tasmota Power Switches (ESP8266), controlled via HTTP GET:
- Retrieve ADD description: `https://<HOSTNAME>/add`
- Switch: `https://<HOSTNAME>/cm?cmnd=Power%20On` or `Power%20Off`
- Read status: `https://<HOSTNAME>/cm?cmnd=Power` (append Unix timestamp as query parameter `t` to avoid caching, e.g. `&t=123`)
- Response format: JSON, e.g. `{"POWER":"ON"}`

| Device | IP | Port | ADD URL | Purpose |
|---|---|---|---|---|
| Power Switch 1 – Ceiling Light | ps1.norbert-walter.dnshome.de | 80 | https://ps1.norbert-walter.dnshome.de/add | Primary, broad room illumination |
| Power Switch 2 – Ambient Light | ps2.norbert-walter.dnshome.de | 80 | https://ps2.norbert-walter.dnshome.de/add | Dimmed, atmospheric lighting |
| Power Switch 3 – TV Backlight | ps3.norbert-walter.dnshome.de | 80 | https://ps3.norbert-walter.dnshome.de/add | Eye-friendly background light behind the TV |
| Power Switch 4 – TV Set | ps4.norbert-walter.dnshome.de | 80 | https://ps4.norbert-walter.dnshome.de/add | Entertainment device |
| Power Switch 5 – Reading Lamp | ps5.norbert-walter.dnshome.de | 80 | https://ps5.norbert-walter.dnshome.de/add | Focused task lighting at the couch |
| Spot Light (individual additional device, no ADD document) | 192.168.1.93 | 80 | — no ADD document, explicitly approved by user | Subtle, focused additional light source; behaves like the ambient light |

**Linkage between devices:** The Spot Light runs in sync with the TV (Power Switch 4) in both directions: TV on → Spot Light on; TV off → Spot Light off. Before switching, both states must still be checked individually (see Chapter 4) — the user may have manually changed the Spot Light in the meantime.

## 4. General Procedure

Sequence for EVERY action (not only at session start):

1. **Capture context:** Query the status of ALL 6 devices fresh (see below, "No reuse"), and if needed determine the current time and weather/sun position for Düsseldorf (see Chapter 5.1). At session start, additionally retrieve all 5 ADD documents of the devices (without them the AI does not know which devices are present) and read this document in full.
2. **Assess the situation:** Derive the current activity or intention from the combination of status, time, weather, and explicit user statement (see Chapter 6 for typical scenarios).
3. **Plan the action:** Which devices need to be brought into which state according to the rules (Chapter 5) and the scenario table (Chapter 6)?
4. **Check rules and priorities:** Apply in particular the priority order from Chapter 5 (explicit user request overrides measured status overrides scenario rule).
5. **Act:** Execute only the switching actions that are actually necessary.
6. **Verify:** After every switching action, query the actual status of the affected device (for linkages and group actions: all affected devices) again to confirm the effect.

**No reuse of previously queried status:** Every new request or decision point requires a NEW, freshly executed status query — even within the same session, even if only seconds have passed since the last query. A reference to "already checked" or "unchanged since the last query" is NOT sufficient. Reason: The user (or another automation) may have manually changed a device between any two requests, regardless of how short the interval was. Example: A sequence of "I want to watch TV" → "Turn off the reading lamp" → "I'm going to bed" consists of three separate decision points, each requiring its own fresh status query of all 6 devices — not a single shared query at the start.

**Handling unreachable devices or documents:** If an ADD document or a status query is unreachable (e.g. due to a security or network restriction in the retrieval environment), guessing or acting on the basis of incomplete information is NOT permitted. The affected device is considered to have "unknown state". The AI reports this transparently and refrains from switching actions that depend on this device until access is possible or the user provides further instructions.

## 5. Rules

**5.1 Generic rules (plausibly derivable from common sense even without this document):**
- Activities requiring broad, clear illumination (searching, tidying) → ceiling light on.
- Activities requiring focused task lighting (reading, sewing) → reading lamp on, no bright ceiling light needed.
- Screen use (tablet or smartphone) → no additional reading lamp needed.
- Watching TV → TV on; backlight (TV backlight) is eye-friendly in the dark.
- Calm, relaxed activities (resting, romance, quiet conversation) → dimmed rather than bright lighting.
- Social activities with multiple people (party, guests, board games, dining) → tend toward brighter lighting.
- Leaving the room or going to bed → switch off devices that are no longer needed.
- Check the actual state before every action rather than guessing (ADD core principle "Verify the result of every write action by reading the device state afterward", extended here to apply before as well — see Chapter 4).
- **Time and weather determination as a shared baseline (universal, for all time- or weather-dependent rules in this document):** Sunrise, sunset, and twilight times, as well as current weather (in particular cloud cover and rain), are determined via internet research when needed and never guessed. This determination serves as the shared baseline for all time- or weather-dependent rules in this document (see Daylight Rule and Artificial Light Rule in Chapter 6; which scenarios are affected is noted in the "Conditions" column of the state table). If a usage situation is being evaluated for the first time under such a time- or weather-dependent rule and the result deviates from the currently measured device status or from the previous scenario rule, the user must be asked whether this deviation is intended — not decided independently. Only after confirmation is the deviation considered resolved; if it recurs and is confirmed repeatedly, it may be added as a further individual preference to the state table (see Chapter 7).

**5.2 Priority order in case of conflicts (rules are defaults, the status query is the source of truth):**

A documented scenario rule (Chapter 6) describes only the normal case — it is a default, not an immutable command. In case of conflict, the following order of precedence applies, from highest to lowest:

1. **Explicit, current user statement** (e.g. "the TV backlight should be on") — highest priority, overrides any scenario rule.
2. **Actual, measured device status** (reality) — second highest priority. If a device deviates from the expected rule (e.g. changed manually), THAT is reality, not the expectation from the rule.
3. **Scenario rule from the state table** (Chapter 6) — only the default, when neither 1 nor 2 specifies otherwise.

When there is a deviation between measured status and scenario rule: if the deviation is explainable by an explicit, current user statement, the user's wish applies (no error, no need to ask). If the deviation is not explainable (e.g. a device deviates from the expected state without explanation), the rule is: ask rather than independently "correct" (see Chapter 8).

The actual device state can change at any time independently of the assistant's control (manual operation, other automation). This is normal and not an error — except when the TV is running after 23:00 while both parents are in bed (see Chapter 6, TV hours rule: indication of possible unsupervised use by children, will be raised).

## 6. Activity-Based Rules — Device State Table

Legend: **ON** = switch on, **OFF** = switch off, **—** = leave unchanged, **conditional** = depends on additional condition (see footnote). Column "Type": G = generic rule, I = individual preference. Column "Conditions": Short reference to time- or weather-dependent rules from Chapters 5.1/6 — "Exception" = scenario is exempt from the respective rule (task lighting or deliberately chosen preference independent of daylight), "Artificial Light Rule" = scenario is subject to the general daylight avoidance rule, "Daylight Rule (TV Backlight)" = device-specific rule applies (see footnote 1), "—" = no time or weather dependency. **This table describes the normal case — an explicit, current user request always takes precedence (see Chapter 5.2).**

| Scenario | Type | Ceiling Light | Ambient Light | TV Backlight | TV | Reading Lamp | Spot Light | Conditions |
|---|---|---|---|---|---|---|---|---|
| Searching in cabinet / shelf | G | ON | — | — | — | — | — | Exception (task lighting) |
| Tidying / cleaning | G | ON | — | — | — | — | — | Exception (task lighting) |
| Watching TV (standard) | G | — | — | conditional¹ | ON | — | ON (sync)ᴵ | Daylight Rule (TV Backlight) |
| Cozy TV, not too bright | I | OFF | conditional² | ON | ON | — | ON (sync)ᴵ | Exception (individual preference) |
| Reading (physical book) | I | OFF | ONᴵ | OFF³ | OFF³ | ON | OFF³ | Exception (individual preference) |
| Browsing with tablet / smartphone | G | — | ON | — | — | OFF | — | Artificial Light Rule |
| Conversation / chat during reading | G | — | ON | — | — | OFF | — | Artificial Light Rule |
| Resuming reading after conversation | G | — | ON | — | — | ON | — | Reading lamp: Exception; Ambient light: Artificial Light Rule |
| Simultaneous reading and watching TV | I | OFF | ON | ON | ON | ON | ON (sync) | Exception (individual preference) |
| Sewing | G | — | ON | — | — | ON | — | Reading lamp: Exception; Ambient light: Artificial Light Rule |
| Resting (on couch, not sleeping) | G | OFF | conditional⁴ | OFF | OFF | OFF | OFF | — |
| Dining (e.g. at coffee table) | G | conditional⁵ | ON | — | — | — | — | Exception (situational, preliminary — see query note) |
| Party / guests / board games | G | ON | ON | — | conditional⁶ | OFF | — | Exception (situational, preliminary — see query note) |
| Romance | G | OFF | conditional⁷ | OFF | OFF | OFF | conditional⁷ | Exception (individual preference) |
| Conversation / chat (standalone) | G | OFF | ON | OFF | OFF | — | OFF | Artificial Light Rule |
| Guest sleeping in living room | I | OFF | OFF | OFF | OFF | OFF | OFF | — |
| Leaving room / going to bed | G | OFF | OFF | OFF | OFF | OFF | OFF | — |
| Brief absence (e.g. bathroom), same activity continues | G | — | — | — | — | — | — | — |

Footnotes:
1. TV Backlight only ON at dusk or darkness (Daylight Rule below). Leave OFF in daylight (energy saving). [G]
2. If still too dark despite TV Backlight: additionally switch Ambient Light ON (not ceiling light). [I]
3. Only switch off if TV, Spot Light, or TV Backlight were previously running. If they were not running, leave them unchanged (OFF). [G]
4. Ambient light optional, only on explicit request. [G]
5. Ceiling light only additionally ON depending on desired brightness. [G]
6. TV optional for background music or ambiance, no active viewing assumed. [G]
7. Romance: either Ambient Light OR Spot Light, depending on desired lighting mood. [G, Spot Light itself is I]

(ᴵ = Spot Light and its linkage are individual, independent of the type of the row)

**Note on the "Conditions" column:** The entries "Dining" and "Party / guests / board games" are marked as "preliminary" because it has not yet been conclusively clarified with the user whether these scenarios should remain exempt from the Artificial Light Rule during daytime or whether they should also be subject to it. Until clarified, the mandatory query requirement from Chapter 5.1 applies.

**Daylight Rule (applies to the TV Backlight):**
- With sufficient daylight, do not automatically switch on artificial light or ask briefly beforehand (energy saving). [Generic rule]
- From sunset onward it is dusky; from the end of civil twilight it is fully dark (time determination see Chapter 5.1). [Generic rule]
- Take cloud cover and rain into account: on an overcast sky it becomes noticeably darker before sunset — TV Backlight may then be switched on approximately one hour earlier (weather determination see Chapter 5.1). [Individual preference]

**Artificial Light Rule during daylight (applies to all lighting devices: ceiling light, ambient light, TV backlight, reading lamp, spot light):**
- Between sunrise +1 hour and sunset −1 hour, avoid using artificial light where possible, since daylight is sufficient for typical use (time determination see Chapter 5.1). [Generic rule]
- Exception: if current weather indicates heavy rain and significantly less daylight than normal is available as a result, this rule is disregarded; current user preferences (Chapter 5.2, priority 1) then take precedence (weather determination see Chapter 5.1). [Individual preference]
- Which scenarios are subject to this rule or exempt from it is noted in the "Conditions" column of the state table. The mandatory query requirement for a first-time deviating assessment is centrally governed in Chapter 5.1.

**TV Hours Rule (individual preference, exact times):**
- Children: under no circumstances watch TV after 19:00, no exceptions. Child still in the room → ambient light on, TV off. Child leaves the room → ambient light off again.
- Adults: from 23:00 onward normally no more TV time either, only exceptional cases. TV running after 23:00 with both parents in bed → indication of possible unsupervised use by children, will be raised.

## 7. Handling Individual Preferences

**What individual preferences are** (not generically derivable, specific to this household):
- Preferred device combinations (e.g. reading lamp AND ambient light together when reading).
- Exact time boundaries (19:00 / 23:00 TV hours; sunrise +1h / sunset −1h for the Artificial Light Rule).
- The Spot Light as an additional device and its linkage to the TV.
- Behavior when children are in the room outside of TV hours.
- Behavior when a guest is sleeping over.
- The requirement to always check all 6 devices (not only when linkages are involved).
- The priority "explicit current user request before scenario rule" (Chapter 5.2).
- The exact threshold of the rain exception in the Artificial Light Rule (Chapter 6) and the concrete assignment of which scenarios in the state table are exempt from it (column "Conditions").

**How new individual preferences arise:**
- The AI may independently draw conclusions about possible new preferences from usage behavior and reactions, and make proposals.
- New preferences are only added to this document after confirmation by the user — never autonomously without confirmation.

**Momentary statement vs. lasting preference:** An explicit, current statement (Chapter 5.2, priority 1) initially applies only to the current situation. If it contains a durability signal ("always", "in general", "from now on", "as a rule"), it constitutes a new individual preference. The AI should then actively propose adding it permanently to the document in accordance with the above — rather than treating it only as a one-time exception that a future session would otherwise forget.

## 8. Preferences in Multi-User Operation

- Preferences can be stored per person (e.g. different preferences of the user and his wife).
- Who is currently speaking or present can be recognized from the manner of address or phrasing. If in doubt, actively ask who the current speaker is.
- If multiple persons are simultaneously in the room with conflicting goals (e.g. one is reading, another is watching TV): the AI resolves the conflict independently by weighing the best solution for the situation (see table row "Simultaneous reading and watching TV" in Chapter 6). If in doubt, ask rather than guess.

## 9. Documentation Requirement

**Every content change to this document (addition, correction, restructuring) MUST be recorded as a new entry in the file `livingroom_change_history.md`**, before or immediately after the change is made here. The companion document contains the exact instructions (fields to be filled in: time of execution, person initiating, AI model executing, time and person of approval, reason, type of change). Times are always recorded using a time tool in real time, never estimated or invented. This requirement serves the purpose of historically clean reproducibility: every rule in this document should be traceable to when, why, and by whom it was created.
