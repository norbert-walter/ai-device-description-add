# ADD – Test Equipment and Evaluation Methodology

This document describes the hardware, software, and test methodology used to develop and evaluate the ADD standard. It is intended to make the research environment transparent and reproducible — both for external reviewers and for contributors who want to run comparable experiments.

> **Why this matters for ADD specifically:**  
> LLMs are probabilistic systems. The same model, the same ADD document, and the same task can produce different outcomes depending on which tools are available, how they are configured, and what client environment is used. Reproducible conclusions about model behavior require reproducible test environments — identical MCP tools, identical tool configurations, and documented test setups. This is not optional for ADD research; it is a methodological prerequisite.

---

## Testing Methodology

ADD testing is not a single activity. It spans a range of investigation types, from open-ended early exploration to tightly controlled multi-model comparisons. The following three levels describe how work actually progresses.

### Level 1 — Exploration

**Purpose:** Discover what is possible, surface unexpected behaviors, and identify promising research directions.

Exploration tests are open-ended and qualitative. A new ADD document, a new model, or a new tool configuration is tried without a fixed protocol. The goal is not to reach a definitive conclusion but to generate hypotheses and notice things that merit closer investigation.

Typical questions at this level:
- Does the model read and apply the ADD document without additional prompting?
- Does it respect rule boundaries when asked to do something the ADD explicitly forbids?
- How does it react when a required external resource (weather service, schedule) is unavailable?
- Does framing the task differently change how strictly the model interprets the rules?

Results from this level are documented informally in experiment logs. They guide what gets promoted to Level 2.

---

### Level 2 — Comparative Evaluation

**Purpose:** Compare the behavior of different models under identical, reproducible conditions.

Comparative tests use a fixed test setup: the same ADD document, the same task, the same MCP tools, the same tool configuration. Only the model changes. This makes it possible to attribute behavioral differences to the model rather than to the environment.

Key requirements for valid comparative evaluation:
- **Identical MCP tool set.** The same tools, in the same versions, must be available to all models being compared. A model that has access to a web search tool but another does not is not a fair comparison for tasks where external information is relevant.
- **Identical task framing.** The same initial prompt, worded identically, is used for all models.
- **Documented setup.** Model name, quantization, context size, and client environment are recorded for every test run.
- **Reproducible client environment.** Tests are run in the same client (e.g., llama-ui, LocalAI, Claude Desktop) for all models in a comparison series.

Client-side MCP tools have proven most practical at this level, because they can be integrated into multiple test clients (Claude Desktop, Claude Web, ChatGPT Web, llama-ui, LocalAI) without modification. This makes it possible to compare cloud frontier models and local open-weight models under a consistent tool environment.

---

### Level 3 — Targeted Deep Analysis

**Purpose:** Investigate a specific hypothesis or behavioral pattern in depth.

Deep analysis tests are designed around a concrete question that emerged from Level 1 or Level 2 work. They use structured, repeatable protocols — often multi-cycle runs, adversarial framings, or systematic variation of a single parameter — and produce documented, citable findings.

Examples of Level 3 investigations:
- **Rule dilution over long sessions.** How does a model's adherence to ADD rules change as context length grows? At what point do rules begin to fade?
- **Adversarial framing.** If the same prohibited action is requested through an indirect or goal-oriented framing, does the model still refuse?
- **Rule interpretation auditing.** Can a model be prompted to make its interpretation of ADD binding rules explicit before acting, and does that explicit statement predict its subsequent behavior?
- **ADD document complexity vs. model capability.** Does adding more rules improve safety outcomes for larger models while degrading performance for smaller ones?
- **Resource cost vs. capability.** Using the AI server's runtime monitoring, how do context usage, computation time, and energy consumption scale with model size and ADD document complexity?

Deep analysis tests generate structured log output that can be referenced in writeups and shared as reproducible test cases.

---

### Overview: Levels, Hardware, and Investigation Goals

| Level | Hardware used | OS | Investigation goals |
|---|---|---|---|
| **1 — Exploration** | Workstation PC<br>Dell Precision 5820 | Ubuntu MATE 24.04 LTS | Initial contact with new models, ADD documents, or tool configurations; frontier model evaluation via web clients; qualitative observation of model behavior; research and documentation; hypothesis generation |
| **2 — Comparative Evaluation** | Dell Precision 5820<br>KI-Server | Ubuntu MATE 24.04 LTS | Cross-model comparison under identical MCP tool environments; local open-weight models vs. frontier models; structured test protocols with fixed task framing |
| **3 — Deep Analysis** | KI-Server | Ubuntu MATE 24.04 LTS | Systematic multi-cycle investigations; runtime monitoring of context, compute, and energy; adversarial framing; rule dilution over long sessions; multi-agent setups |

The Dell Optiplex Micro 7020 runs permanently and hosts all Docker-based services (LocalAI, ADD Simulator, MCP server containers). All other systems are brought up on demand for specific test sessions.

---

## Hardware Infrastructure

| Image | Equipment | Role in Test System |
|---|---|---|
| <img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/Dell_Optiplex_7020.jpg" width="200" height="200" style="object-fit:contain;"> | **Dell Optiplex Micro 7020**<br>i5-14500T, 64 GB RAM | Hosts Docker-based services: LocalAI, ADD Simulator, MCP server containers. Runs up to 50 different models for offline and on-premise testing. Primary environment for local model evaluation (small to mid-size models without GPU requirements). |
| <img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/Dell_Precision_5820.jpg" width="200" height="200" style="object-fit:contain;"> | **Dell Precision 5820**<br>AMD RX 6700 XT (12 GB VRAM), 128 GB RAM, 8 TB HDD | Local LLM inference via Vulkan/llama.cpp. Supports small to mid-size quantized models. Used for exploratory runs and model qualification before multi-GPU deployment. |
| <img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/KI_Server_Gigabyte_G431-MMO.png" width="200" height="200" style="object-fit:contain;"> | **KI-Server G431-MM0**<br>6× NVIDIA P100 (16 GB VRAM each), 96 GB total VRAM, 1 TB SSD | Multi-GPU inference via CUDA/llama.cpp. Runs models from 4B to approximately 70B parameters. Enables parallel model instances, multi-agent configurations, and runtime monitoring during tests. Central platform for Level 2 and Level 3 evaluation. |

### AI Server — Extended Evaluation Capabilities

The AI server runs a management tool that provides runtime visibility into model behavior during active test sessions:

- Multiple model instances run simultaneously on separate GPUs — enabling direct side-by-side comparison without reloading
- Per-instance monitoring of context window size and live context utilization — visible during the session, not only after it
- Per-GPU metrics: load, VRAM consumption, temperature, power draw
- Configurable context size, context shift, and inference slots per instance
- Individual model logs and a global emergency stop
- System-wide monitoring: CPU, RAM, swap, PCIe I/O, disk I/O, network

This makes it possible to observe not only *whether* a model succeeds at an ADD task, but *how* it uses its context, how much compute it consumes, and whether these scale predictably with model size or ADD document complexity.

**A natural experiment format at this level:**  
Run the same ADD scenario with 4B, 9B, 14B, 32B, and 70B models in sequence. For each run, record: task outcome (PASS / PARTIAL / FAIL), peak context usage, processing time, peak VRAM, average GPU load, and energy consumption. This turns a capability comparison into a capability-vs.-cost comparison — directly relevant to the question of which model size is appropriate for which class of ADD deployment.

---

## IoT Test Devices

| Status | Device | Role in Test System |
|---|---|---|
| ✅ | **Sonoff devices** (various) | Tasmota-flashed actuators used as simple ADD-compatible test targets. Represent the realistic low-end of the deployment spectrum: cheap, widely deployed, HTTP-capable hardware. Primary device class for valve, switch, and relay scenarios. |
| ✅ | **Yachta Windsensor 2.1** | Real deployed marine hardware with ADD-enabled firmware. Tests ADD under actual network conditions with real sensor data (wind speed, wind angle). Approximately 250 units shipped; ADD rollout in progress to existing users. |
| ✅ | **OBP40 / OBP60** (Open Boat Projects multifunction displays) | Multi-interface marine hardware (NMEA 2000, NMEA 0183, WiFi, display). Used for testing ADD on complex, multi-protocol real devices and for dashboard integration work. |

The combination of simulated devices (ADD Simulator), simple real actuators (Sonoff/Tasmota), and fully instrumented real hardware (Yachta, OBP) covers the evaluation range from controlled laboratory conditions to actual field deployment.

---

## Software Infrastructure

### MCP Tools

MCP tools are the primary mechanism by which AI models interact with external resources during ADD tests. Their configuration has a direct effect on test outcomes and must be documented and kept consistent within a test series.

The Dell Optiplex Micro 7020, Dell Precision 5820, and KI-Server are all accessible remotely via web clients, so tests with frontier models can be run against locally hosted infrastructure without requiring physical access to the machines.

**Client-side MCP tools** (recommended for comparative testing):

Client-side tools are integrated via the AI model's MCP configuration and export their functionality over the network to the test system. They run as Docker containers on the Dell Optiplex Micro 7020, which provides them centrally to all test environments. This means the same tool instances are available to Claude Desktop, Claude Web, ChatGPT Web, llama-ui, and LocalAI without any per-client installation — which makes them the practical choice for cross-environment and cross-model comparisons. This approach has proven most versatile in practice.

| Tool | Function |
|---|---|
| `fetch` | HTTP requests to IoT devices and external APIs |
| `time` | Current date and time — required for time-rule evaluation |
| `search` | Web search for external context |
| `file` | Read/write access to local files (logs, configuration) |
| `github` | Access to ADD documents and specifications on GitHub |

Available as Docker images on [Docker Hub (openboatprojects)](https://hub.docker.com/u/openboatprojects).

**Server-side MCP tools** (for server-resident environments):

Server-side tools run as persistent Docker containers on the server and are accessed over the network. They are available for LocalAI and other environments that support network-based MCP services. Useful for multi-agent setups and scenarios requiring server-resident services. Note that llama.cpp does not support server-side MCP tools; client-side tools must be used there.

| Tool | Function |
|---|---|
| `fetch` | HTTP requests |
| `time` | Current date and time |
| `search` | Web search |
| `wait` | Timed delays — for testing scheduled or time-conditional ADD rules |
| `tasmota` | Direct Tasmota device control |

Available as Docker images on [Docker Hub (openboatprojects)](https://hub.docker.com/u/openboatprojects).

---

### AI Runtimes

| Status | Software | Description |
|---|---|---|
| ✅ | **LocalAI** ([Docker Hub](https://github.com/norbert-walter/localai)) | Docker-based local inference system. Runs 50+ models, serves an OpenAI-compatible API, integrates with llama-ui and LocalAI clients. Primary runtime for local model testing. |
| ✅ | **llama.cpp / llama-server** | Direct inference backend used on the Dell Precision 5820 (Vulkan) and the AI server (CUDA). Supports MCP tool integration via `--ui-mcp-proxy`. |
| ✅ | **Cloud frontier model APIs** | Claude (Anthropic), ChatGPT (OpenAI), Gemini (Google) — accessed via their respective web clients or APIs. Used for Level 2 cross-model comparisons that include frontier models. |

---

### ADD-Specific Software

| Status | Software | Description |
|---|---|---|
| ✅ | **ADD Simulator** | Simulates a Tasmota-based valve with a complete ADD document, including logging. Docker-based, portable. Available on [Docker Hub](https://hub.docker.com/r/openboatprojects/add-simulator). Used as the primary controlled test target for Level 2 and Level 3 experiments. |
| 🔧 | **Test Scripts** | Automated test routines spanning multiple cycles with structured logging. In development. |
| 📋 | **Test Bench** | A comprehensive evaluation harness for systematic AI qualification against ADD — standardized task sets, scoring, regression testing. Planned. |

---

## Reproducibility and Limitations

ADD experiments are reproducible in setup but not fully deterministic in outcome — this is a property of the systems under test, not a gap in the methodology.

**What is reproducible:**
- The ADD document presented to the model
- The MCP tools available and their configuration
- The task framing (initial prompt)
- The model identity, version, and quantization
- The client environment and inference parameters

**What is not reproducible:**
- Individual model outputs — LLMs are stochastic; the same input will not always produce the same output
- Model weights for cloud frontier models — versions change without notice
- Context-dependent behaviors in long sessions — earlier turns affect later outputs in ways that cannot be fully controlled

**Consequence for test design:** Level 2 and Level 3 tests use structured logging of all variable parameters. Where stochastic variation is relevant (e.g., pass rate across repeated runs), multiple cycles are run and the distribution is reported, not a single outcome.

---

## Log Files and Experiment Records

Every test session produces log output. Structured experiment records include:

```
Experiment:       <id>
Model:            <name>, <quantization>
Context size:     <tokens>
ADD version:      <version>
Task:             <description>
Result:           PASS / PARTIAL / FAIL

Prompt tokens:    <n>
Generated tokens: <n>
Peak context:     <n> tokens
Duration:         <s>
Peak VRAM:        <GB>
Avg. GPU load:    <%>
Energy:           <Wh>
Human intervention: yes / no

Notes:            <observations>
```

Log files from the AI server management tool, the ADD Simulator, and LocalAI are combined with the experiment record to provide a full picture of each test run.

The long-term goal is to connect these log sources into a unified ADD Model Evaluation Harness — where test outcome, context trajectory, and resource cost are recorded together, automatically, at the end of each experiment.

---

*For the ADD standard itself, see [README.md](README.md).*  
*For device implementation guidance, see [ADD Developer Guide v1.0](ADD_Developer_Guide_v1_0.md).*
