# AI Server · GPU Dashboard

<img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/AI_Server_Dashboard_EN.png" alt="AI Server GPU Dash Board" width="800">

A live web dashboard for managing **llama-server** instances on a multi-GPU server. It shows system utilization, VRAM usage, and running model instances in real time — and lets you start, stop, and configure new instances directly from the browser.

> Runs on **port 9000**. Start with `python3 gpu_dashboard_server.py`, then open `http://<server-ip>:9000` in any browser.

---

## Core Functions

### System Overview (top row)
The top row shows the most important system metrics at a glance:

| Tile | Content |
|---|---|
| **CPU** | Average utilization, load average (1 min), per-core breakdown |
| **RAM** | Used / total RAM and swap with progress bars |
| **PCIe I/O** | Total PCIe throughput across all GPUs (RX + TX in MB/s) |
| **Disk I/O** | Read/write throughput of all block devices |
| **Network** | RX/TX throughput per network interface |

All values update every second via HTTP polling — no WebSockets, no page reload required.

### GPU Cards
Each GPU is shown as an individual card containing:

- **Load** (utilization in %)
- **Temperature** (°C) and **power draw** (W)
- **VRAM** usage with progress bar (used / total in GB)
- **Context length** — tokens currently held in the KV cache, as a percentage and absolute value
- **PCIe link** (generation and lane width) and current throughput
- The **assigned model** with port number, status badge (loading / ready), and action buttons

If multiple GPUs share one llama-server instance (tensor-parallel split), they are visually grouped with a shared color.

### "Start new model" Form
The form at the bottom allows you to assign a model to one or more GPUs:

- Select a `.gguf` model from `~/AI-Models`
- Assign one or more GPUs (GPUs currently in use are grayed out)
- Set context length, parallel sessions, threads, split mode, port
- Configure sampling parameters (temperature, top_p, top_k, min_p, etc.)
- A **live command preview** updates with every change — you can inspect the exact `llama-server` call before starting
- **"Show command only"** copies the command without executing it; **"Start directly"** launches the instance immediately

### Emergency Stop
The red **"Emergency Stop – Unload all models"** button terminates all running llama-server instances at once. In-flight requests are aborted immediately.

---

## Log Files

The log files are the primary tool for understanding what is actually happening inside a running system — beyond the live values visible in the dashboard. They enable a wide range of analyses:

- **Performance evaluation:** Token throughput (tokens/s) per request, per model and per GPU configuration can be read directly from the data log. This makes it easy to compare different models, quantization levels (Q4 vs. Q8 vs. BF16) or split strategies under identical load conditions.
- **Performance optimization:** Bottlenecks become visible in the log — for example when prompt processing drops from 200 t/s to 135 t/s as context grows, or when a specific model takes significantly longer to load than expected. These patterns point to where tuning effort pays off.
- **Context depth optimization:** The data log records prompt token count and generated token count for every request. Over time this shows the actual context depth distribution in practice, making it possible to fine-tune the `--ctx-size` parameter: large enough to avoid truncation, small enough to keep VRAM consumption and KV-cache overhead under control.
- **Monitoring agent activity:** In a multi-agent setup (e.g. orchestrator + workers on separate ports and GPUs), each instance logs independently. The logs can be compared side by side to see which agent handles which tasks, how often workers are called, and where idle time or queuing occurs.
- **Energy consumption per token and task:** Combined with the power draw figures recorded per poll (W per GPU), the data log's token counts allow estimating energy cost per request or per task type — relevant for sizing and for comparing the efficiency of different models at equal output quality.
- **Load distribution optimization:** When multiple instances run in parallel, the logs reveal whether load is evenly distributed or whether individual instances are saturated while others are idle. This informs decisions about port assignment, parallel session counts (`--parallel`) and GPU allocation.
- **PCIe, disk and network throughput analysis:** The dashboard records PCIe RX/TX per GPU, disk read/write rates and network throughput per interface once per second. Sustained high PCIe throughput during inference can indicate that a model does not fit into VRAM and weight data is being streamed — a clear signal to switch to a smaller quantization or fewer split GPUs.
- **CPU utilization:** The log helps correlate CPU load spikes with specific request patterns. On EPYC systems with few cores (e.g. 4-core EPYC 3151), the CPU can become the bottleneck under parallel load — not PCIe or GPU — which shows up as elevated load averages alongside idle GPU utilization.
- **Startup and error diagnosis:** The AI log captures the full llama-server startup sequence including model loading, layer distribution across GPUs, context allocation and any driver warnings or quantization notices. This is the first place to look when an instance fails to reach "ready" status.

Each llama-server instance produces **two separate log files** under `~/gpu_dashboard_logs/`:

| File | Content | Typical use |
|---|---|---|
| `port-<PORT>.log` | Raw llama-server output (model loading messages, request traces, error output) | Diagnosing startup errors, tracking inference activity, checking quantization warnings |
| `port-<PORT>-data.log` | Structured data log of all requests and responses with timestamps, token counts and throughput figures | Performance analysis, capacity planning, identifying slow or oversized requests |

### Accessing Logs

- **In the browser:** click the **"Log"** or **"Data Log"** button on each GPU card → the current log file opens as plain text via `GET /api/log/<port>`
- **On disk:** directly at `~/gpu_dashboard_logs/port-<port>.log` and `port-<port>-data.log`

### Resetting Logs

The **"Delete Log"** button resets both log files for an instance **while it keeps running**: the old file is closed and deleted, a new empty file with a fresh header is opened immediately. This is useful when you want to start a clean measurement without reloading the model (which takes minutes for large models). Internally a `_RotatingLogHandle` wrapper ensures the writer thread never loses a line during the reset — no data is written to a detached, unreachable file handle.

---

## Data Flow

<img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/Dashboard_Data_Flow_EN.png" alt="Dash Board Data Flow" width="800">

The dashboard follows a strict **collect → bundle → poll → render** pattern. Nothing is stored in a database; all values are live snapshots.

### 1 · Data Sources

| Source | Type | Data |
|---|---|---|
| `nvidia-smi --query-gpu` | NVIDIA Tool | GPU index, name, VRAM used/free/total, utilization %, temperature, power draw |
| `nvidia-smi dmon -s t` | NVIDIA Tool | PCIe throughput per GPU (RX/TX in MB/s) |
| `nvidia-smi --query-gpu=pcie.link.*` | NVIDIA Tool | PCIe generation and lane width (for plausibility check) |
| `psutil.cpu_percent(percpu=True)` | Python library | Per-core CPU utilization, average, core count |
| `os.getloadavg()` | Python stdlib | Load average (1/5/15 min) |
| `psutil.virtual_memory()` | Python library | RAM used/total/free |
| `psutil.swap_memory()` | Python library | Swap used/total |
| `psutil.disk_io_counters()` | Python library | Disk read/write throughput (delta between two polls) |
| `psutil.net_io_counters(pernic=True)` | Python library | Network RX/TX per interface (delta between two polls) |
| `ps -eo pid,args` | Linux tool | Running llama-server processes with PID and command line |
| `/proc/<pid>/environ` | Linux kernel (procfs) | `CUDA_VISIBLE_DEVICES` → GPU assignment per process |
| `http://127.0.0.1:<port>/health` | llama-server API | Instance status: loading / ready / unreachable |
| `http://127.0.0.1:<port>/slots` | llama-server API | Context tokens in use per slot, `is_processing` flag |
| `.gguf` file (binary header parser) | Model file | Maximum context length, recommended sampling parameters |
| `<model>.params.json` (sidecar) | Config file | Mode-specific sampling parameters (instruct / think / think_coding / instruct_reasoning) |
| `gpu_dashboard_config.json` | Config file | Persisted instance configuration (model, port, GPU) |
| `socket` UDP (no traffic) | Python stdlib | LAN IP address of the server |

### 2 · Backend (Flask, Python)

On every request to `/api/status` the backend:

1. **Collects** fresh data from all sources listed above
2. **Validates** values — e.g. the PCIe hold logic suppresses implausible driver-glitch values (known issue on older Tesla cards) for one poll cycle before resetting to 0
3. **Caches** GGUF metadata by file modification time to avoid re-parsing large model files on every poll
4. **Bundles** everything into a single JSON response

### 3 · Frontend (HTML / CSS / JavaScript)

The browser calls `GET /api/status` every second (`setInterval(refresh, 1000)`), parses the JSON, and rebuilds the UI entirely from the current data:

- `renderSystem()` — CPU, RAM, PCIe, disk and network cards with progress bars
- `renderGpus()` — one card per GPU; processes are matched to their GPU via `CUDA_VISIBLE_DEVICES` and colored stably by PID for the lifetime of the process
- `renderModelSelect()` — dropdown populated from the list of available `.gguf` files

After starting or stopping an instance, additional polls are triggered at 800 ms, 1.8 s, 3.5 s and 6 s, because the `/slots` endpoint only responds once the model has fully loaded.

---

## API Endpoints

<img src="https://raw.githubusercontent.com/norbert-walter/ai-device-description-add/refs/heads/main/pictures/Dashboard_Endpoints_EN.png" alt="Dash Board Endpoints" width="800">

The dashboard exposes its own REST API on **port 9000**, which can also be called directly (e.g. from scripts or monitoring tools).

### Status & Information (GET)

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard HTML/JS (the web interface) |
| `GET /api/status` | All system data as JSON (GPU, CPU, RAM, disk, network, running processes, model list, server IP) |
| `GET /api/config` | Current saved configuration |
| `GET /api/models` | List of available `.gguf` model files |
| `GET /api/model-context-length?model=<name>` | Maximum context length read directly from the GGUF header |
| `GET /api/model-sampling-params?model=<name>&mode=<mode>` | Recommended sampling parameters for a model and mode |
| `GET /api/models-with-params` | List of models that have a `.params.json` sidecar file |
| `GET /api/log/<port>` | Current AI log for the instance on the given port |
| `GET /api/datalog/<port>` | Current data log for the instance on the given port |

### Instance Management (POST)

| Endpoint | Description |
|---|---|
| `POST /api/start` | Start a new llama-server instance (model, GPU, port, context, sampling params, …) |
| `POST /api/start-command` | Return the start command as text only — without executing it (live preview) |
| `POST /api/stop` | Stop a single instance by PID |
| `POST /api/stop-all` | Terminate all running instances immediately |
| `POST /api/delete-log` | Reset both log files for an instance (port) while it keeps running |
| `GET/POST /api/config` | Read or save the dashboard configuration |

### llama-server Chat API (Ports 8080–8088)

Each running llama-server instance provides its own **OpenAI-compatible API** on its assigned port:

| Endpoint | Description |
|---|---|
| `GET /health` | Instance status (loading / ready) |
| `GET /slots` | Slot and context usage |
| `POST /completion` | Single-turn text completion |
| `POST /chat/completions` | Chat completion (OpenAI-compatible — works with Open WebUI, LM Studio, and custom clients) |
| `GET /models` | List of loaded models |

Chat clients (Open WebUI, LM Studio, custom applications) connect **directly** to these ports and do not go through the dashboard on port 9000.

---

## Prerequisites

### Hardware

The dashboard is designed for Linux servers with one or more **NVIDIA GPUs**. Any CUDA-capable card works in principle — it has been developed and tested on Tesla P100 PCIe 16 GB cards (Pascal architecture, CUDA compute capability 6.0). The more VRAM per card, the larger the models you can run.

> **Note on Pascal (P100/GP100):** CUDA 12.9 is required, as CUDA 13.0 no longer compiles Pascal kernels. The `row` split mode is not supported on Pascal — the dashboard shows a warning if you select it.

### Software

| Component | Version / Notes |
|---|---|
| **Operating system** | Linux (tested on Ubuntu 24.04 LTS) |
| **NVIDIA driver** | 580.x or newer recommended (`ubuntu-drivers autoinstall`) |
| **CUDA toolkit** | 12.x (12.9 for Pascal GPUs) — required to build llama.cpp |
| **`nvidia-smi`** | Included with the NVIDIA driver, must be in `PATH` |
| **Python** | 3.10 or newer |
| **Flask** | `pip install flask --break-system-packages` |
| **psutil** | `pip install psutil --break-system-packages` |
| **llama.cpp** (`llama-server`) | Self-compiled with CUDA support — see below |

### Building llama.cpp

The dashboard launches `llama-server` from a fixed path (`~/llama.cpp/build/bin/llama-server`). Build it once with CUDA support:

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)
```

> Use the **absolute path** to the binary in your system — a relative path can cause the process not to be found by the dashboard.

### Models

Place your `.gguf` model files in `~/AI-Models/`. The dashboard scans this directory on every refresh and lists all `.gguf` files in the "Start new model" dropdown. Optionally, place a `<model>.params.json` sidecar file next to a model to define mode-specific sampling parameters (instruct / think / think_coding / instruct_reasoning).

### Starting the Dashboard

```bash
# Install dependencies (once)
pip install flask psutil --break-system-packages

# Start the dashboard
python3 gpu_dashboard_server.py
```

Then open **`http://<server-ip>:9000`** in any browser. The dashboard also works from a remote machine on the same network — just replace `<server-ip>` with the server's LAN address shown in the title bar.
