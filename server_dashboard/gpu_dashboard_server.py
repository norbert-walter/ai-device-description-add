#!/usr/bin/env python3
"""
GPU dashboard for the G431-MM0 multi-GPU server.

Displays live utilization, VRAM usage, CPU/RAM load and running
llama-server instances per GPU. Allows assigning new models to a
specific free GPU (fixed assignment, no router mode) and starting/
stopping running instances directly.

Start:
    pip install flask psutil --break-system-packages
    python3 gpu_dashboard_server.py
Then open in browser: http://<server-ip>:9000
"""

import json
import os
import re
import signal
import socket
import struct
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import psutil
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

# State for delta calculation of disk/network throughput between two polls
_io_state = {"time": None, "disk": None, "net": None}

# Holds the last valid PCIe value + error counter per GPU to bridge brief
# dropouts/driver glitches instead of letting the display jump
_pcie_hold_state = {}

# Holds the currently-active log-file wrapper for each running instance,
# keyed by port (str): {"ai_log": _RotatingLogHandle, "data_log": _RotatingLogHandle}.
# Lets /api/delete-log reset a log while the instance keeps running: the
# writer thread only ever writes through the wrapper, never through a raw
# file object it cached itself — so swapping the wrapper's underlying file
# is invisible to it and no data is ever written to a detached, unreachable
# inode (which is what happened when the log file's path was simply
# unlink()'d out from under an actively-appending open handle).
_log_handles = {}
_log_handles_lock = threading.Lock()


class _RotatingLogHandle:
    """Wraps a single log file so it can be reset — old file closed and
    deleted, new one opened with a fresh header — while another thread
    keeps calling .write_and_flush() through this same wrapper."""

    def __init__(self, path, mode):
        self._path = path
        self._mode = mode
        self._lock = threading.RLock()
        self._file = self._open()

    def _open(self):
        if "b" in self._mode:
            return open(self._path, self._mode)
        return open(self._path, self._mode, encoding="utf-8")

    def write_and_flush(self, data):
        with self._lock:
            self._file.write(data)
            self._file.flush()

    def reset(self, header_text):
        """Closes the current file, deletes it, opens a brand-new file at
        the same path and writes header_text into it."""
        with self._lock:
            try:
                self._file.close()
            except Exception:
                pass
            try:
                if self._path.exists():
                    self._path.unlink()
            except OSError:
                pass
            self._file = self._open()
            if header_text:
                payload = header_text.encode() if "b" in self._mode and isinstance(header_text, str) else header_text
                self._file.write(payload)
                self._file.flush()

    def close(self):
        with self._lock:
            try:
                self._file.close()
            except Exception:
                pass


def _register_log_handle(port, key, handle):
    with _log_handles_lock:
        _log_handles.setdefault(str(port), {})[key] = handle


def _unregister_log_handle(port, key):
    with _log_handles_lock:
        h = _log_handles.get(str(port))
        if h:
            h.pop(key, None)
            if not h:
                _log_handles.pop(str(port), None)

# Holds the last known context-usage value per process (PID). /slots only delivers
# the usage fields while a request is actively being processed (is_processing:
# true) — between turns of an ongoing chat they are absent, even though the
# KV-cache remains occupied. Without this hold the display would incorrectly
# snap back to 0 whenever no request is currently running.
_context_used_hold = {}
_process_mode_map = {}  # pid -> mode label string

CONFIG_FILE = Path(__file__).parent / "gpu_dashboard_config.json"
LOG_DIR = Path(__file__).parent / "gpu_dashboard_logs"
LOG_DIR.mkdir(exist_ok=True)

MODEL_DIR = "/home/norbert-walter/AI-Models"
LLAMA_BIN = "/home/norbert-walter/llama.cpp/build/bin/llama-server"


# ---------- GGUF metadata: read context length ----------

_GGUF_SCALAR_SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
_GGUF_STRING, _GGUF_ARRAY = 8, 9
_context_length_cache = {}  # path -> (mtime, value)


def _gguf_read_string(f):
    length = struct.unpack("<Q", f.read(8))[0]
    return f.read(length).decode("utf-8", errors="replace")


def _gguf_skip_string(f):
    length = struct.unpack("<Q", f.read(8))[0]
    f.seek(length, 1)


def _gguf_read_scalar(f, vtype):
    raw = f.read(_GGUF_SCALAR_SIZES.get(vtype, 4))
    fmt = {2: "<H", 3: "<h", 4: "<I", 5: "<i", 10: "<Q", 11: "<q", 6: "<f", 12: "<d"}.get(vtype)
    if fmt:
        return struct.unpack(fmt, raw)[0]
    return raw[0] if raw else None


def _gguf_skip_value(f, vtype):
    if vtype == _GGUF_STRING:
        _gguf_skip_string(f)
    elif vtype == _GGUF_ARRAY:
        elem_type = struct.unpack("<I", f.read(4))[0]
        length = struct.unpack("<Q", f.read(8))[0]
        if elem_type == _GGUF_STRING:
            for _ in range(length):
                _gguf_skip_string(f)
        elif elem_type == _GGUF_ARRAY:
            for _ in range(length):
                _gguf_skip_value(f, _GGUF_ARRAY)
        else:
            f.seek(_GGUF_SCALAR_SIZES.get(elem_type, 4) * length, 1)
    else:
        f.seek(_GGUF_SCALAR_SIZES.get(vtype, 4), 1)


def get_gguf_context_length(path):
    """Reads the '<arch>.context_length' metadata from a GGUF file without loading it."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    cached = _context_length_cache.get(path)
    if cached and cached[0] == mtime:
        return cached[1]

    context_length = None
    try:
        with open(path, "rb") as f:
            if f.read(4) != b"GGUF":
                return None
            f.read(4)  # version, not needed
            struct.unpack("<Q", f.read(8))[0]  # tensor_count, not needed
            kv_count = struct.unpack("<Q", f.read(8))[0]
            for _ in range(kv_count):
                key = _gguf_read_string(f)
                vtype = struct.unpack("<I", f.read(4))[0]
                if key.endswith("context_length") and vtype in _GGUF_SCALAR_SIZES and vtype not in (_GGUF_STRING, _GGUF_ARRAY):
                    context_length = _gguf_read_scalar(f, vtype)
                else:
                    _gguf_skip_value(f, vtype)
    except Exception:
        return None

    _context_length_cache[path] = (mtime, context_length)
    return context_length


# ---------- GGUF metadata: read sampling parameters ----------

_GGUF_SAMPLING_KEYS = {
    "general.temperature":      "temp",
    "general.top_p":            "top_p",
    "general.top_k":            "top_k",
    "general.min_p":            "min_p",
    "general.repeat_penalty":   "repeat_penalty",
    "general.presence_penalty": "presence_penalty",
}
_sampling_params_cache = {}  # path -> (mtime, dict)


def get_gguf_sampling_params(path):
    """Reads author-recommended sampling parameters from GGUF metadata (if present)."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    cached = _sampling_params_cache.get(path)
    if cached and cached[0] == mtime:
        return cached[1]

    params = {}
    try:
        with open(path, "rb") as f:
            if f.read(4) != b"GGUF":
                return {}
            f.read(4)  # version
            struct.unpack("<Q", f.read(8))[0]  # tensor_count
            kv_count = struct.unpack("<Q", f.read(8))[0]
            for _ in range(kv_count):
                key = _gguf_read_string(f)
                vtype = struct.unpack("<I", f.read(4))[0]
                if key in _GGUF_SAMPLING_KEYS and vtype in _GGUF_SCALAR_SIZES and vtype not in (_GGUF_STRING, _GGUF_ARRAY):
                    val = _gguf_read_scalar(f, vtype)
                    if val is not None:
                        params[_GGUF_SAMPLING_KEYS[key]] = val
                else:
                    _gguf_skip_value(f, vtype)
    except Exception:
        pass

    _sampling_params_cache[path] = (mtime, params)
    return params


# ---------- Hybrid: load sampling params from .params.json or GGUF ----------

SAMPLING_DEFAULTS = {
    "instruct":          {"temp": 0.7, "top_p": 0.80, "top_k": 20,  "min_p": 0.0, "presence_penalty": 1.5, "repeat_penalty": 1.0},
    "think":             {"temp": 1.0, "top_p": 0.95, "top_k": 20,  "min_p": 0.0, "presence_penalty": 0.0, "repeat_penalty": 1.0},
    "think_coding":      {"temp": 0.6, "top_p": 0.95, "top_k": 20,  "min_p": 0.0, "presence_penalty": 0.0, "repeat_penalty": 1.0},
    "instruct_reasoning":{"temp": 1.0, "top_p": 1.00, "top_k": 40,  "min_p": 0.0, "presence_penalty": 2.0, "repeat_penalty": 1.0},
}


def load_sampling_params(model_name, mode="instruct"):
    """Returns sampling parameters for the given model and mode.
    Priority: <model>.params.json  →  GGUF metadata  →  built-in defaults."""
    base = Path(MODEL_DIR) / model_name
    params_file = Path(str(base).rsplit(".", 1)[0] + ".params.json")

    # 1. Sidecar .params.json
    if params_file.exists():
        try:
            data = json.loads(params_file.read_text())
            modes = data.get("modes", {})
            default_mode = data.get("default_mode", "instruct")
            return modes.get(mode, modes.get(default_mode, SAMPLING_DEFAULTS["instruct"]))
        except Exception:
            pass

    # 2. GGUF metadata
    gguf_params = get_gguf_sampling_params(str(base))
    if gguf_params:
        merged = dict(SAMPLING_DEFAULTS.get(mode, SAMPLING_DEFAULTS["instruct"]))
        merged.update(gguf_params)
        return merged

    # 3. Built-in defaults
    return dict(SAMPLING_DEFAULTS.get(mode, SAMPLING_DEFAULTS["instruct"]))


# ---------- Determine network IP ----------

def get_lan_ip():
    """Determines the IP address assigned in the LAN (not 127.0.0.1)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No actual traffic — only used to determine the outgoing interface IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# Effective bandwidth per lane and PCIe generation, approximate (MB/s) — for plausibility check
_PCIE_MB_PER_LANE = {"1": 250, "2": 500, "3": 985, "4": 1969, "5": 3938}


def _max_plausible_pcie_mb_s(gen, width):
    """Theoretical maximum per direction, with safety factor 2 (encoding overhead etc.)."""
    try:
        per_lane = _PCIE_MB_PER_LANE.get(str(gen), 985)  # fallback: Gen3 assumption
        return per_lane * int(width) * 2
    except Exception:
        return 20000  # generous fallback if gen/width is unknown


def _hold_pcie_value(idx, key, raw_value, is_valid):
    """Holds the last valid value on error; resets to 0 after 2 consecutive
    errors. `key` is 'rx' or 'tx'."""
    state = _pcie_hold_state.setdefault(idx, {})
    entry = state.setdefault(key, {"value": 0.0, "err_count": 0})

    if is_valid:
        entry["value"] = raw_value
        entry["err_count"] = 0
    else:
        entry["err_count"] += 1
        if entry["err_count"] >= 2:
            entry["value"] = 0.0
        # on err_count == 1: keep last value unchanged

    return entry["value"]


def get_pcie_status():
    """Reads PCIe throughput (RX/TX in MB/s) and link gen/width per GPU."""
    result = {}
    try:
        # Throughput: one sample is enough, dmon already delivers an averaged instantaneous rate
        out = subprocess.check_output(
            ["nvidia-smi", "dmon", "-c", "1", "-s", "t"], text=True, timeout=3,
        )
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            idx = int(parts[0])
            rx_mb = float(parts[-2]) if parts[-2] != "-" else 0.0
            tx_mb = float(parts[-1]) if parts[-1] != "-" else 0.0
            result[idx] = {"rx_mb_s": rx_mb, "tx_mb_s": tx_mb}
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,pcie.link.gen.current,pcie.link.width.current",
             "--format=csv,noheader,nounits"],
            text=True,
        )
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3:
                continue
            idx, gen, width = int(parts[0]), parts[1], parts[2]
            result.setdefault(idx, {})
            result[idx]["link_gen"] = gen
            result[idx]["link_width"] = width
    except Exception:
        pass

    return result


# ---------- Data collection: GPU ----------

def get_gpu_status():
    fields = "index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw"
    try:
        out = subprocess.check_output(
            ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
            text=True,
        )
    except Exception as e:
        return {"error": str(e)}

    gpus = []
    pcie = get_pcie_status()
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 8:
            continue
        idx, name, mem_total, mem_used, mem_free, util, temp, power = parts
        idx = int(idx)
        p = pcie.get(idx, {})
        link_gen = p.get("link_gen")
        link_width = p.get("link_width")
        max_plausible = _max_plausible_pcie_mb_s(link_gen, link_width)
        rx = p.get("rx_mb_s")
        tx = p.get("tx_mb_s")
        # Known NVML/driver glitch on older Tesla cards occasionally delivers
        # implausibly high sentinel values (e.g. exactly 200 GiB/s) instead of a real
        # measurement, or no value at all. In both cases the last valid value is held;
        # only after 2 consecutive errors is it reset to 0.
        rx_valid = rx is not None and rx <= max_plausible
        tx_valid = tx is not None and tx <= max_plausible
        rx_display = _hold_pcie_value(idx, "rx", rx, rx_valid)
        tx_display = _hold_pcie_value(idx, "tx", tx, tx_valid)
        gpus.append({
            "index": idx,
            "name": name,
            "mem_total_mb": float(mem_total),
            "mem_used_mb": float(mem_used),
            "mem_free_mb": float(mem_free),
            "utilization_pct": float(util),
            "temp_c": float(temp),
            "power_w": float(power) if power != "[N/A]" else None,
            "pcie_rx_mb_s": rx_display,
            "pcie_tx_mb_s": tx_display,
            "pcie_link_gen": link_gen,
            "pcie_link_width": link_width,
        })
    return {"gpus": gpus}


# ---------- Data collection: disk/network throughput ----------

def _format_rate(bytes_per_sec):
    """Returns (value, unit), automatically choosing MB/s or GB/s."""
    mb = bytes_per_sec / (1024 ** 2)
    if mb >= 1024:
        return round(mb / 1024, 2), "GB/s"
    return round(mb, 1), "MB/s"


_DISK_SKIP_FSTYPES = {
    "tmpfs", "devtmpfs", "squashfs", "overlay", "proc", "sysfs",
    "devpts", "cgroup", "cgroup2", "pstore", "efivarfs", "autofs",
    "mqueue", "debugfs", "tracefs", "securityfs", "configfs",
    "fusectl", "hugetlbfs", "bpf", "binfmt_misc",
}


def get_disk_usage():
    """Returns used/total capacity for every mounted physical disk (HDD/SSD),
    de-duplicated by device (so a disk mounted at several points is only
    listed once) and skipping virtual/pseudo filesystems."""
    disks = []
    seen_devices = set()
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        partitions = []
    for part in partitions:
        if part.fstype in _DISK_SKIP_FSTYPES:
            continue
        if part.device in seen_devices:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        seen_devices.add(part.device)
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "used_gb": round(usage.used / 1024**3, 1),
            "total_gb": round(usage.total / 1024**3, 1),
            "pct": usage.percent,
        })
    disks.sort(key=lambda d: d["mountpoint"])
    return disks


def get_io_status():
    now = time.time()
    disk_now = psutil.disk_io_counters()
    net_now = psutil.net_io_counters(pernic=True)

    prev_time = _io_state["time"]
    disk_prev = _io_state["disk"]
    net_prev = _io_state["net"]

    result = {"disk": None, "interfaces": [], "disk_usage": get_disk_usage()}

    if prev_time is not None and disk_now is not None and disk_prev is not None:
        elapsed = max(now - prev_time, 0.001)
        read_bps = (disk_now.read_bytes - disk_prev.read_bytes) / elapsed
        write_bps = (disk_now.write_bytes - disk_prev.write_bytes) / elapsed
        total_val, total_unit = _format_rate(max(read_bps, 0) + max(write_bps, 0))
        read_val, read_unit = _format_rate(max(read_bps, 0))
        write_val, write_unit = _format_rate(max(write_bps, 0))
        result["disk"] = {
            "total_value": total_val, "total_unit": total_unit,
            "read_value": read_val, "read_unit": read_unit,
            "write_value": write_val, "write_unit": write_unit,
        }

    if prev_time is not None and net_prev is not None:
        elapsed = max(now - prev_time, 0.001)
        for nic, counters in net_now.items():
            if nic not in net_prev:
                continue
            # Skip loopback interface, irrelevant for server throughput
            if nic == "lo":
                continue
            rx_bps = (counters.bytes_recv - net_prev[nic].bytes_recv) / elapsed
            tx_bps = (counters.bytes_sent - net_prev[nic].bytes_sent) / elapsed
            rx_val, rx_unit = _format_rate(max(rx_bps, 0))
            tx_val, tx_unit = _format_rate(max(tx_bps, 0))
            result["interfaces"].append({
                "name": nic,
                "rx_value": rx_val, "rx_unit": rx_unit,
                "tx_value": tx_val, "tx_unit": tx_unit,
            })

    _io_state["time"] = now
    _io_state["disk"] = disk_now
    _io_state["net"] = net_now
    return result


# ---------- Data collection: CPU / RAM ----------

def get_system_status():
    per_core = psutil.cpu_percent(percpu=True, interval=0.2)
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1 = load5 = load15 = None
    return {
        "cpu_per_core_pct": per_core,
        "cpu_avg_pct": sum(per_core) / len(per_core) if per_core else 0,
        "cpu_core_count": len(per_core),
        "load_avg": {"1min": load1, "5min": load5, "15min": load15},
        "ram_used_gb": round(vm.used / 1024**3, 2),
        "ram_total_gb": round(vm.total / 1024**3, 2),
        "swap_used_gb": round(sw.used / 1024**3, 2),
        "swap_total_gb": round(sw.total / 1024**3, 2),
    }


def check_health(port):
    """Queries the /health endpoint of the instance to detect loading status.
    Returns: 'loading', 'ready' or 'unreachable'."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            body = json.loads(resp.read().decode())
            status = body.get("status", "")
            if status == "ok":
                return "ready"
            return "loading"
    except urllib.error.HTTPError as e:
        # llama-server often responds with 503 while loading
        if e.code == 503:
            return "loading"
        return "unreachable"
    except Exception:
        return "unreachable"


def check_slots(port, pid):
    """Queries the /slots endpoint (only available when the instance was started
    with --slots) and returns the currently occupied context token count.
    A slot retains 'n_prompt_tokens' even after a request completes
    (is_processing: false) — this is the context length actually held in the
    KV-cache after the last turn. Only a slot that has never been assigned a task
    (no 'id_task') yields no usable data. During active processing
    'next_token.n_decoded' (tokens already generated in the current response)
    is added on top."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/slots")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            slots_data = json.loads(resp.read().decode())
        if not isinstance(slots_data, list) or not slots_data:
            return _context_used_hold.get(pid, 0)

        total_used = 0
        found_any = False
        for slot in slots_data:
            if "id_task" not in slot:
                continue  # slot has never been assigned a task
            n_prompt = slot.get("n_prompt_tokens", 0) or 0
            n_decoded = 0
            if slot.get("is_processing"):
                next_token = slot.get("next_token") or {}
                n_decoded = next_token.get("n_decoded", 0) or 0
            # Fallback to older/alternative field names if present
            n_past = slot.get("n_past")
            used = n_past if n_past is not None else (n_prompt + n_decoded)
            total_used += used
            found_any = True

        if found_any:
            _context_used_hold[pid] = total_used
            return total_used
        return _context_used_hold.get(pid, 0)
    except Exception:
        return _context_used_hold.get(pid, 0)


# ---------- Data collection: running llama-server processes ----------

def get_llama_processes():
    procs = []
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,args"], text=True)
    except Exception as e:
        return {"error": str(e)}

    for line in out.splitlines():
        line = line.strip()
        if "llama-server" not in line or "grep" in line:
            continue
        m = re.match(r"^(\d+)\s+(.*)$", line)
        if not m:
            continue
        pid, cmdline = m.group(1), m.group(2)

        port_m = re.search(r"--port\s+(\d+)", cmdline)
        model_m = re.search(r"-m\s+(\S+)", cmdline)
        ctx_m = re.search(r"(?:-c|--ctx-size)\s+(\d+)", cmdline)
        parallel_m = re.search(r"(?:-np|--parallel)\s+(\d+)", cmdline)
        port = port_m.group(1) if port_m else None
        model_path = model_m.group(1) if model_m else None
        model_name = os.path.basename(model_path) if model_path else None
        context_size = int(ctx_m.group(1)) if ctx_m else None
        parallel_sessions = int(parallel_m.group(1)) if parallel_m else None
        context_shift = "--context-shift" in cmdline
        slots_enabled = "--slots" in cmdline
        context_used = check_slots(port, int(pid)) if (slots_enabled and port) else None

        gpus_assigned = None
        try:
            with open(f"/proc/{pid}/environ", "rb") as f:
                env_raw = f.read().split(b"\x00")
            for entry in env_raw:
                if entry.startswith(b"CUDA_VISIBLE_DEVICES="):
                    gpus_assigned = entry.decode(errors="ignore").split("=", 1)[1]
        except Exception:
            pass

        procs.append({
            "pid": int(pid),
            "port": port,
            "model": model_name,
            "model_path": model_path,
            "gpus": gpus_assigned,
            "context_size": context_size,
            "context_shift": context_shift,
            "slots_enabled": slots_enabled,
            "context_used": context_used,
            "status": check_health(port) if port else "unreachable",
            "mode_label": _process_mode_map.get(int(pid), ""),
            "parallel_sessions": parallel_sessions,
        })
    active_pids = {p["pid"] for p in procs}
    for held_pid in list(_process_mode_map.keys()):
        if held_pid not in active_pids:
            del _process_mode_map[held_pid]
    for held_pid in list(_context_used_hold.keys()):
        if held_pid not in active_pids:
            del _context_used_hold[held_pid]

    return {"processes": procs}


# ---------- Configuration / model list ----------

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"assignments": []}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def list_available_models():
    p = Path(MODEL_DIR)
    if not p.exists():
        return []
    return sorted(f.name for f in p.glob("*.gguf"))


# Valid ranges for sampling parameters: (type, min, max)  — None means no bound
_SAMPLING_BOUNDS = {
    "temp":             (float, 0.0,  None),
    "top_p":            (float, 0.0,  1.0),
    "top_k":            (int,   0,    None),
    "min_p":            (float, 0.0,  1.0),
    "presence_penalty": (float, -2.0, 2.0),
    "repeat_penalty":   (float, 0.01, None),
}


def _clamp_sampling(params):
    """Validates and clamps sampling parameters to their allowed ranges.
    Drops any key whose value is not a finite number after conversion."""
    import math
    cleaned = {}
    for key, val in params.items():
        if key not in _SAMPLING_BOUNDS:
            continue
        typ, lo, hi = _SAMPLING_BOUNDS[key]
        try:
            val = typ(val)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(float(val)):
            continue
        if lo is not None:
            val = max(typ(lo), val)
        if hi is not None:
            val = min(typ(hi), val)
        cleaned[key] = val
    return cleaned


def build_command(model, gpus, port, threads, split_mode, context_shift=False, context_size=None, slots=False,
                  sampling=None, reasoning_format=None, parallel=1):
    cmd = [
        LLAMA_BIN, "-m", f"{MODEL_DIR}/{model}",
        "--port", str(port), "--gpu-layers", "999",
        "--threads", str(threads), "--host", "0.0.0.0",
        "-np", str(parallel),
    ]
    if "," in str(gpus) and split_mode:
        cmd += ["--split-mode", split_mode]
    if context_shift:
        cmd += ["--context-shift"]
    if context_size:
        cmd += ["-c", str(context_size)]
    if slots:
        cmd += ["--slots"]
    # Sampling parameters — clamp to valid ranges before use
    if sampling:
        sampling = _clamp_sampling(sampling)
        flag_map = {
            "temp":             "--temp",
            "top_p":            "--top-p",
            "top_k":            "--top-k",
            "min_p":            "--min-p",
            "presence_penalty": "--presence-penalty",
            "repeat_penalty":   "--repeat-penalty",
        }
        for key, flag in flag_map.items():
            if key in sampling:
                cmd += [flag, str(sampling[key])]
    # Reasoning format
    if reasoning_format and reasoning_format != "auto":
        cmd += ["--reasoning-format", reasoning_format]
    return cmd


# ---------- API: status ----------

@app.route("/api/status")
def api_status():
    return jsonify({
        "gpu": get_gpu_status(),
        "system": get_system_status(),
        "io": get_io_status(),
        "processes": get_llama_processes(),
        "models": list_available_models(),
        "host_ip": get_lan_ip(),
    })


@app.route("/api/model-sampling-params")
def api_model_sampling_params():
    model = request.args.get("model")
    mode  = request.args.get("mode", "instruct")
    if not model:
        return jsonify({"error": "model is required"}), 400
    path = os.path.join(MODEL_DIR, model)
    if not os.path.isfile(path):
        return jsonify({"error": "model not found"}), 404
    params = load_sampling_params(model, mode)
    # Detect source for UI hint
    params_file = Path(str(Path(path).with_suffix("")) + ".params.json")
    available_modes = ["instruct", "think"]  # default: both available
    if params_file.exists():
        source = "params.json"
        try:
            data = json.loads(params_file.read_text())
            defined = list(data.get("modes", {}).keys())
            if defined:
                available_modes = defined
        except Exception:
            pass
    elif get_gguf_sampling_params(path):
        source = "gguf"
    else:
        source = "default"
    return jsonify({"params": params, "source": source, "available_modes": available_modes})


@app.route("/api/models-with-params")
def api_models_with_params():
    """Returns a set of model filenames that have a matching .params.json sidecar."""
    p = Path(MODEL_DIR)
    result = set()
    if p.exists():
        for f in p.glob("*.gguf"):
            params_file = f.with_suffix("").with_suffix(".params.json")
            # also accept stem.params.json (without the .gguf part)
            params_file2 = Path(str(f).rsplit(".", 1)[0] + ".params.json")
            if params_file.exists() or params_file2.exists():
                result.add(f.name)
    return jsonify({"models_with_params": sorted(result)})


@app.route("/api/model-context-length")
def api_model_context_length():
    model = request.args.get("model")
    if not model:
        return jsonify({"error": "model is required"}), 400
    path = os.path.join(MODEL_DIR, model)
    if not os.path.isfile(path):
        return jsonify({"error": "model not found"}), 404
    ctx = get_gguf_context_length(path)
    if ctx is None:
        return jsonify({"error": "context length could not be determined"}), 200
    return jsonify({"context_length": ctx})


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        save_config(request.get_json())
        return jsonify({"ok": True})
    return jsonify(load_config())


# ---------- API: generate start command (text only) ----------

@app.route("/api/start-command", methods=["POST"])
def api_start_command():
    data = request.get_json()
    model, gpus, port = data.get("model"), data.get("gpus"), data.get("port")
    threads = data.get("threads", 1)
    parallel = data.get("parallel", 1)
    split_mode = data.get("split_mode")
    context_shift = bool(data.get("context_shift"))
    context_size = data.get("context_size")
    slots = bool(data.get("slots"))
    mode = data.get("mode", "instruct")
    sampling = data.get("sampling")  # explicit overrides from form
    reasoning_format = "none" if mode in ("instruct", "instruct_reasoning") else "deepseek"

    if not (model and gpus and port):
        return jsonify({"error": "model, gpus and port are required"}), 400
    try:
        port_int = int(port)
        if not (1024 <= port_int <= 65535):
            return jsonify({"error": f"Port {port_int} is not allowed. Use a port in range 1024–65535."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid port number."}), 400
    try:
        threads_int = int(threads)
        cpu_cores = len(psutil.cpu_percent(percpu=True, interval=0))
        if not (1 <= threads_int <= cpu_cores):
            threads_int = max(1, min(threads_int, cpu_cores))
    except (ValueError, TypeError):
        threads_int = 1
    try:
        parallel_int = int(parallel)
        parallel_int = max(1, min(5, parallel_int))
    except (ValueError, TypeError):
        parallel_int = 1

    # Merge: form overrides take precedence over auto-loaded params
    base_sampling = load_sampling_params(model, mode)
    if sampling:
        base_sampling.update({k: v for k, v in sampling.items() if v not in (None, "")})

    cmd = build_command(model, gpus, port, threads_int, split_mode, context_shift, context_size, slots,
                        sampling=base_sampling, reasoning_format=reasoning_format, parallel=parallel_int)
    cmd_str = f"CUDA_VISIBLE_DEVICES={gpus} " + " ".join(cmd)
    return jsonify({"command": cmd_str})


# ---------- API: actually start process ----------

@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json()
    model, gpus, port = data.get("model"), data.get("gpus"), data.get("port")
    threads = data.get("threads", 1)
    parallel = data.get("parallel", 1)
    split_mode = data.get("split_mode")
    context_shift = bool(data.get("context_shift"))
    context_size = data.get("context_size")
    slots = bool(data.get("slots"))
    mode = data.get("mode", "instruct")
    sampling = data.get("sampling")
    extra_params = data.get("extra_params", "").strip()
    reasoning_format = "none" if mode in ("instruct", "instruct_reasoning") else "deepseek"

    if not (model and gpus and port):
        return jsonify({"error": "model, gpus and port are required"}), 400
    try:
        port_int = int(port)
        if not (1024 <= port_int <= 65535):
            return jsonify({"error": f"Port {port_int} is not allowed. Use a port in range 1024–65535."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid port number."}), 400
    try:
        threads_int = int(threads)
        cpu_cores = len(psutil.cpu_percent(percpu=True, interval=0))
        threads_int = max(1, min(threads_int, cpu_cores))
    except (ValueError, TypeError):
        threads_int = 1
    try:
        parallel_int = int(parallel)
        parallel_int = max(1, min(5, parallel_int))
    except (ValueError, TypeError):
        parallel_int = 1

    # Merge: form overrides take precedence over auto-loaded params
    base_sampling = load_sampling_params(model, mode)
    if sampling:
        base_sampling.update({k: v for k, v in sampling.items() if v not in (None, "")})

    used_gpus = set()
    for p in get_llama_processes().get("processes", []):
        if p["gpus"]:
            used_gpus.update(p["gpus"].split(","))
    requested = set(str(gpus).split(","))
    overlap = requested & used_gpus
    if overlap:
        return jsonify({"error": f"GPU(s) {', '.join(sorted(overlap))} are already in use"}), 409

    cmd = build_command(model, gpus, port, threads_int, split_mode, context_shift, context_size, slots,
                        sampling=base_sampling, reasoning_format=reasoning_format, parallel=parallel_int)
    if extra_params:
        import shlex
        try:
            cmd += shlex.split(extra_params)
        except ValueError:
            cmd += extra_params.split()
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpus)

    import datetime, threading

    def _timestamp():
        """Returns current time as 'YYYY-MM-DD HH:MM:SS.mmm'."""
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"

    log_file = LOG_DIR / f"port-{port}.log"

    # Launch llama-server with a pipe so we can prepend timestamps line-by-line
    proc = subprocess.Popen(
        cmd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    # _log_event: set by _log_writer each time a line is written.
    # _done_event: set exactly once when _log_writer finishes (stdout closed).
    # _header_event: set once after _log_writer has written the start header.
    _log_event    = threading.Event()
    _done_event   = threading.Event()
    _header_event = threading.Event()

    _ai_log_handle = _RotatingLogHandle(log_file, "ab")
    _register_log_handle(port, "ai_log", _ai_log_handle)

    def _log_writer():
        """Writes the start header, then reads llama-server output line by
        line and prepends a wall-clock timestamp, writing everything through
        _ai_log_handle (never a raw file object) so /api/delete-log can
        reset the underlying file mid-run without losing future writes."""
        try:
            # Write header — no gap possible since it goes through the same handle
            _mode_labels = {"instruct": "Instant", "think": "Think",
                            "think_coding": "Think (Coding)",
                            "instruct_reasoning": "Instant (Reasoning)"}
            _mode_label = _mode_labels.get(mode, mode)
            header_lines = [
                "",
                "=" * 72,
                f"  {'Started':<8}: {_timestamp()}",
                f"  {'Model':<8}: {model}",
                f"  {'Port':<8}: {port}",
                f"  {'GPU(s)':<8}: {gpus}",
                f"  {'Threads':<8}: {threads}",
                f"  {'Sessions':<8}: {parallel_int}",
                f"  {'Context':<8}: {context_size or 'default'}"
                + ("  [shift]" if context_shift else ""),
                f"  {'Mode':<8}: {mode} ({_mode_label})  |  reasoning-format: {reasoning_format}",
                "  Sampling parameters:",
                *[f"    {k:<20} = {v}" for k, v in sorted(base_sampling.items())],
                f"  {'Command':<8}: CUDA_VISIBLE_DEVICES={gpus} " + " ".join(cmd),
                "=" * 72,
                "",
            ]
            _ai_log_handle.write_and_flush(("\n".join(header_lines) + "\n").encode())
            _header_event.set()   # signal: header written, data_logger may write its own

            for raw_line in proc.stdout:
                ts = _timestamp()
                date_part, time_part = ts.split(" ", 1)
                try:
                    decoded = raw_line.decode(errors="replace")
                    parts = decoded.split(None, 3)
                    if len(parts) >= 3:
                        rel_ts = parts[0]
                        level  = parts[1]
                        rest   = parts[2] if len(parts) == 3 else parts[2] + " " + parts[3]
                        formatted = f"{date_part} | {time_part} | {rel_ts} | {level} | {rest}"
                        if not formatted.endswith("\n"):
                            formatted += "\n"
                        encoded_line = formatted.encode()
                    else:
                        encoded_line = f"{date_part} | {time_part} | ".encode() + raw_line
                except Exception:
                    encoded_line = f"{date_part} | {time_part} | ".encode() + raw_line
                _ai_log_handle.write_and_flush(encoded_line)
                _log_event.set()   # signal: a line was written
        except Exception:
            _header_event.set()        # unblock _data_logger even on error
        finally:
            _unregister_log_handle(port, "ai_log")
            _ai_log_handle.close()
            _done_event.set()          # signal: stdout closed, process is done

    t = threading.Thread(target=_log_writer, daemon=True)
    t.start()

    # Store mode label for display in GPU info cards
    _mode_labels_map = {"instruct": "Instant", "think": "Think",
                        "think_coding": "Think (Coding)",
                        "instruct_reasoning": "Instant (Reasoning)"}
    _process_mode_map[proc.pid] = _mode_labels_map.get(mode, mode)

    # ---------- Data logger: GPU / CPU / RAM / PCIe / Disk ----------
    data_log_file = LOG_DIR / f"port-{port}-data.log"
    _data_log_handle = _RotatingLogHandle(data_log_file, "a")
    _register_log_handle(port, "data_log", _data_log_handle)

    def _data_logger():
        """Writes system metrics to the data log ONLY when _log_writer
        has just written a line — keeping both logs time-synchronous.
        Each row contains all GPUs as separate column groups side by side.
        All writes go through _data_log_handle (never a raw file object) so
        /api/delete-log can reset the underlying file mid-run."""
        SEP = " | "

        def fmt(val, decimals=1):
            if val is None:
                return "-"
            try:
                return f"{float(val):.{decimals}f}"
            except Exception:
                return str(val)

        def build_header(gpu_indices, iface_names):
            """Builds the column header dynamically based on actual GPU count
            and network interfaces present."""
            cols = ["Date      ", "Time          "]
            # One group of columns per GPU
            for idx in gpu_indices:
                g = f"GPU{idx}"
                cols += [
                    f"{g}_Load_%",
                    f"{g}_VRAM_used_MB",
                    f"{g}_VRAM_tot_MB",
                    f"{g}_Temp_C",
                    f"{g}_Power_W",
                    f"{g}_PCIe_RX_MB/s",
                    f"{g}_PCIe_TX_MB/s",
                ]
            # System columns
            cols += ["CPU_avg_%", "RAM_used_GB", "RAM_tot_GB", "Swap_used_GB",
                     "Disk_R_MB/s", "Disk_W_MB/s"]
            # One RX/TX pair per network interface
            for name in iface_names:
                cols += [f"{name}_RX_MB/s", f"{name}_TX_MB/s"]
            return SEP.join(cols)

        header_written = False
        gpu_indices  = []   # ordered list, determined on first measurement
        iface_names  = []   # ordered list of NIC names

        try:
            # Wait until _log_writer has written its start header, then
            # write a matching header into the data log for synchronisation.
            _header_event.wait(timeout=10.0)
            _mode_labels = {"instruct": "Instant", "think": "Think",
                            "think_coding": "Think (Coding)",
                            "instruct_reasoning": "Instant (Reasoning)"}
            _mode_label = _mode_labels.get(mode, mode)
            data_start_lines = [
                "",
                "=" * 72,
                f"  {'Started':<8}: {_timestamp()}",
                f"  {'Model':<8}: {model}",
                f"  {'Port':<8}: {port}",
                f"  {'GPU(s)':<8}: {gpus}",
                f"  {'Threads':<8}: {threads}",
                f"  {'Sessions':<8}: {parallel_int}",
                f"  {'Context':<8}: {context_size or 'default'}"
                + ("  [shift]" if context_shift else ""),
                f"  {'Mode':<8}: {mode} ({_mode_label})  |  reasoning-format: {reasoning_format}",
                "  Sampling parameters:",
                *[f"    {k:<20} = {v}" for k, v in sorted(base_sampling.items())],
                f"  {'Command':<8}: CUDA_VISIBLE_DEVICES={gpus} " + " ".join(cmd),
                "=" * 72,
                "",
            ]
            _data_log_handle.write_and_flush("\n".join(data_start_lines) + "\n")

            while True:
                if _done_event.is_set() and not _log_event.is_set():
                    break
                triggered = _log_event.wait(timeout=1.0)
                _log_event.clear()
                if not triggered:
                    if _done_event.is_set():
                        break
                    continue

                try:
                    ts = _timestamp()
                    date_part, time_part = ts.split(" ", 1)

                    gpu_data = get_gpu_status()
                    sys_data = get_system_status()
                    io_data  = get_io_status()

                    gpus_list = gpu_data.get("gpus", [])
                    assigned  = set(str(g) for g in str(gpus).split(","))
                    relevant  = [g for g in gpus_list if str(g["index"]) in assigned]
                    if not relevant:
                        relevant = gpus_list
                    # Sort by GPU index for consistent column order
                    relevant = sorted(relevant, key=lambda g: g["index"])

                    ifaces = io_data.get("interfaces", [])

                    # Write header once after first measurement is available
                    if not header_written:
                        gpu_indices  = [g["index"] for g in relevant]
                        iface_names  = [i["name"] for i in ifaces]
                        hdr = build_header(gpu_indices, iface_names)
                        _data_log_handle.write_and_flush(hdr + "\n" + "-" * len(hdr) + "\n")
                        header_written = True

                    # Build one data row
                    cols = [date_part, time_part]

                    # GPU columns — one group per GPU in fixed order
                    gpu_map = {g["index"]: g for g in relevant}
                    for idx in gpu_indices:
                        g = gpu_map.get(idx, {})
                        cols += [
                            fmt(g.get("utilization_pct"), 1),
                            fmt(g.get("mem_used_mb"), 0),
                            fmt(g.get("mem_total_mb"), 0),
                            fmt(g.get("temp_c"), 0),
                            fmt(g.get("power_w"), 1),
                            fmt(g.get("pcie_rx_mb_s"), 1),
                            fmt(g.get("pcie_tx_mb_s"), 1),
                        ]

                    # System columns
                    disk   = io_data.get("disk")
                    disk_r = fmt(disk["read_value"], 2) + disk.get("read_unit",  "") if disk else "-"
                    disk_w = fmt(disk["write_value"], 2) + disk.get("write_unit", "") if disk else "-"
                    cols += [
                        fmt(sys_data.get("cpu_avg_pct"), 1),
                        fmt(sys_data.get("ram_used_gb"), 2),
                        fmt(sys_data.get("ram_total_gb"), 2),
                        fmt(sys_data.get("swap_used_gb"), 2),
                        disk_r,
                        disk_w,
                    ]

                    # Network columns — one RX/TX pair per interface in fixed order
                    iface_map = {i["name"]: i for i in ifaces}
                    for name in iface_names:
                        ifc = iface_map.get(name, {})
                        cols += [
                            fmt(ifc.get("rx_value"), 2) + ifc.get("rx_unit", "") if ifc else "-",
                            fmt(ifc.get("tx_value"), 2) + ifc.get("tx_unit", "") if ifc else "-",
                        ]

                    _data_log_handle.write_and_flush(SEP.join(cols) + "\n")

                except Exception:
                    pass

            _data_log_handle.write_and_flush(f"# Process exited at {_timestamp()}\n")
        finally:
            _unregister_log_handle(port, "data_log")
            _data_log_handle.close()

    td = threading.Thread(target=_data_logger, daemon=True)
    td.start()

    return jsonify({"ok": True, "pid": proc.pid, "log": str(log_file)})


# ---------- API: stop process ----------

@app.route("/api/stop", methods=["POST"])
def api_stop():
    data = request.get_json()
    pid = data.get("pid")
    if not pid:
        return jsonify({"error": "pid is required"}), 400
    try:
        os.kill(int(pid), signal.SIGTERM)
    except ProcessLookupError:
        return jsonify({"error": "process not found (may have already exited)"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


# ---------- API: emergency stop — terminate all instances immediately ----------

@app.route("/api/stop-all", methods=["POST"])
def api_stop_all():
    procs = get_llama_processes().get("processes", [])
    stopped, failed = [], []
    for p in procs:
        try:
            os.kill(p["pid"], signal.SIGKILL)
            stopped.append(p["pid"])
        except Exception:
            failed.append(p["pid"])
    return jsonify({"ok": True, "stopped": stopped, "failed": failed})


@app.route("/api/log/<port>")
def api_log(port):
    if not re.fullmatch(r"\d+", port):
        return Response("Invalid port", status=400, mimetype="text/plain")
    log_file = LOG_DIR / f"port-{port}.log"
    if not log_file.exists():
        return Response(f"No log file found for port {port}.", status=404, mimetype="text/plain")
    # Show only the last ~200 KB to avoid loading very large logs completely
    max_bytes = 200_000
    size = log_file.stat().st_size
    with open(log_file, "rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
        content = f.read().decode(errors="replace")
    header = f"=== Log for port {port} ({log_file}) ===\n\n"
    return Response(header + content, mimetype="text/plain")


_HEADER_MARKER = "=" * 72
_DATA_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s*\|")


def _extract_last_header(path):
    """Finds the last complete header block in a log file (bounded by two
    '='*72 marker lines) and returns it verbatim, including any immediately
    following non-data lines (e.g. the column header + separator of the
    data log). Returns None if no complete header block is present."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    lines = text.splitlines()
    marker_idxs = [i for i, l in enumerate(lines) if l == _HEADER_MARKER]
    if len(marker_idxs) < 2:
        return None

    end_idx = marker_idxs[-1]
    start_idx = marker_idxs[-2]

    # Include the blank line directly preceding the opening marker, if present.
    lead_idx = start_idx - 1 if start_idx > 0 and lines[start_idx - 1].strip() == "" else start_idx

    # Keep everything after the closing marker that is not yet a timestamped
    # data row (e.g. the data log's column header + dashed separator line).
    tail_idx = end_idx + 1
    while tail_idx < len(lines) and not _DATA_LINE_RE.match(lines[tail_idx]):
        tail_idx += 1

    header_lines = lines[lead_idx:tail_idx]
    return "\n".join(header_lines) + "\n"


def _note_for_missing_header():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    return f"# Log cleared at {ts} — no previous header found.\n"


@app.route("/api/delete-log", methods=["POST"])
def api_delete_log():
    """Resets both log files (AI log + data log) for the given port: each
    is deleted and immediately recreated with the last complete header
    found in it beforehand (so the new file starts the same way a freshly
    started instance's log would, without a data section).

    If the instance is still running, its logger thread is still writing —
    but only ever through the registered _RotatingLogHandle wrapper, never
    a raw file object it cached itself. So resetting that wrapper here
    (close old file, delete it, open a new one with the header) is safe
    and the writer's next write transparently lands in the new file. Only
    when no live handle is registered (instance already stopped) does this
    fall back to a plain delete-and-recreate at the filesystem level."""
    data = request.get_json(silent=True) or {}
    port = data.get("port")
    if not port or not re.fullmatch(r"\d+", str(port)):
        return jsonify({"error": "Invalid or missing port."}), 400

    with _log_handles_lock:
        handles = dict(_log_handles.get(str(port), {}))

    results = {}
    any_error = False
    for suffix, key in ((".log", "ai_log"), ("-data.log", "data_log")):
        path = LOG_DIR / f"port-{port}{suffix}"
        header = _extract_last_header(path) if path.exists() else None
        handle = handles.get(key)

        if handle:
            try:
                handle.reset(header or _note_for_missing_header())
                results[key] = "cleared (instance still running)"
            except Exception as e:
                results[key] = f"error: {e}"
                any_error = True
            continue

        if not path.exists():
            results[key] = "not_found"
            continue
        try:
            path.unlink()
            with open(path, "w", encoding="utf-8") as f:
                f.write(header or _note_for_missing_header())
            results[key] = "recreated"
        except OSError as e:
            results[key] = f"error: {e}"
            any_error = True

    if any_error:
        return jsonify({"ok": False, "error": "Some log files could not be reset.", "results": results}), 500
    return jsonify({"ok": True, "results": results})


@app.route("/api/datalog/<port>")
def api_datalog(port):
    if not re.fullmatch(r"\d+", port):
        return Response("Invalid port", status=400, mimetype="text/plain")
    log_file = LOG_DIR / f"port-{port}-data.log"
    if not log_file.exists():
        return Response(f"No data log file found for port {port}.", status=404, mimetype="text/plain")
    max_bytes = 500_000
    size = log_file.stat().st_size
    with open(log_file, "rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
        content_raw = f.read().decode(errors="replace")
    header = f"=== Data log for port {port} ({log_file}) ===\n\n"
    return Response(header + content_raw, mimetype="text/plain")


@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI Server: Gigabyte G431-MM0 GPU Dashboard</title>
<style>
  body { font-family: system-ui, sans-serif; background:#0f1115; color:#e6e6e6; margin:0; padding:24px; }
  h1 { font-size: 20px; margin-bottom: 4px; }
  .conn-led { display:inline-block; width:11px; height:11px; border-radius:50%; margin-left:8px; vertical-align:middle; background:#555; box-shadow:0 0 4px rgba(0,0,0,0.4); transition: background 0.3s, box-shadow 0.3s; }
  .conn-led.online { background:#3ddc4a; box-shadow:0 0 6px #3ddc4a; }
  .conn-led.offline { background:#ff4d4d; box-shadow:0 0 6px #ff4d4d; }
  h2 { font-size: 16px; margin-top: 32px; }
  .sub { color:#888; font-size:13px; margin-bottom:24px; }
  .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(260px,1fr)); gap:14px; }
  .card { background:#1a1d24; border:1px solid #2a2e38; border-radius:10px; padding:14px; }
  .card h3 { margin:0 0 8px 0; font-size:14px; display:flex; justify-content:space-between; }
  .bar-bg { background:#2a2e38; border-radius:6px; height:10px; overflow:hidden; margin:4px 0; }
  .bar-fill { height:100%; background:linear-gradient(90deg,#4f8cff,#7ad1ff); }
  .bar-fill.mem { background:linear-gradient(90deg,#ff8c4f,#ffd17a); }
  .bar-fill.cpu { background:linear-gradient(90deg,#9d6bff,#c9a8ff); }
  .row { display:flex; justify-content:space-between; font-size:12px; color:#aaa; margin-top:2px; }
  .proc { display:flex; flex-direction:column; font-size:11px; color:#6fd66f; margin-top:8px; gap:4px; }
  .proc-header { display:flex; align-items:center; gap:6px; }
  .proc-btns { display:flex; gap:6px; }
  .proc a { color:#6fd66f; text-decoration:none; }
  .proc a:hover { text-decoration:underline; color:#9df59d; }
  .proc button { background:#3a1d1d; color:#ff9a9a; border:1px solid #5a2a2a; border-radius:4px; padding:2px 8px; cursor:pointer; font-size:11px; }
  .proc button.log-btn { background:#1d2a3a; color:#8fc4ff; border:1px solid #2a3e5a; }
  .proc button.data-log-btn { background:#1d2a3a; color:#8fb8ff; border:1px solid #2a3a5a; }
  .proc button.delete-log-btn { background:#3a2a12; color:#ffb84f; border:1px solid #5a4420; }
  .proc button.delete-log-btn:hover { background:#4a350f; }
  .status-badge { display:inline-flex; align-items:center; justify-content:center; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; line-height:1.4; border:1px solid transparent; }
  .status-badge.ready { background:#1a3a24; color:#6fd66f; border-color:#2a5a3a; }
  .status-badge.loading { background:#3a3320; color:#e0c060; border-color:#5a4e2a; }
  .status-badge.loading .spin-icon { display:inline-block; animation: spin 1s linear infinite; }
  .status-badge.unreachable { background:#3a1d1d; color:#ff9a9a; border-color:#5a2a2a; }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .free { color:#666; font-size:11px; margin-top:8px; }
  form { background:#1a1d24; border:1px solid #2a2e38; border-radius:10px; padding:16px; max-width:520px; }
  form label { display:block; font-size:12px; color:#aaa; margin-top:10px; }
  select, input { width:100%; padding:6px; margin-top:4px; background:#0f1115; color:#eee; border:1px solid #2a2e38; border-radius:6px; box-sizing:border-box; }
  .btn-row { display:flex; gap:10px; margin-top:14px; }
  .cmd-preview-wrap { margin-top:14px; }
  .cmd-preview-label { font-size:12px; color:#aaa; margin-bottom:4px; display:flex; align-items:center; gap:6px; }
  #cmd-preview { width:100%; min-height:64px; max-height:160px; overflow-y:auto; background:#0a0c10; color:#8fb8ff; border:1px solid #2a2e38; border-radius:6px; padding:8px 10px; font-family:monospace; font-size:11px; line-height:1.5; box-sizing:border-box; white-space:pre-wrap; word-break:break-all; resize:vertical; }
  .extra-params-wrap { margin-top:8px; }
  .extra-params-label { font-size:12px; color:#aaa; margin-bottom:4px; display:flex; align-items:center; gap:6px; }
  #extra-params { width:100%; background:#0f1115; color:#eee; border:1px solid #2a2e38; border-radius:6px; padding:6px 10px; font-family:monospace; font-size:11px; box-sizing:border-box; }
  button.primary { padding:8px 16px; background:#4f8cff; border:none; border-radius:6px; color:#fff; cursor:pointer; font-size:13px; }
  button.success { padding:8px 16px; background:#2e8b57; border:none; border-radius:6px; color:#fff; cursor:pointer; font-size:13px; }
  button.danger { padding:8px 16px; background:#a33; border:none; border-radius:6px; color:#fff; cursor:pointer; font-size:13px; font-weight:bold; }
  button.danger:hover { background:#c44; }
  pre { background:#0f1115; border:1px solid #2a2e38; border-radius:6px; padding:10px; font-size:12px; margin-top:12px; white-space:pre-wrap; word-break:break-all; }
  .checks { display:flex; gap:10px; flex-wrap:wrap; margin-top:4px; }
  .checks label { display:flex; align-items:center; gap:4px; font-size:12px; color:#ccc; margin-top:0; }
  .checks label.disabled { color:#555; }
  .checks label.disabled input { cursor:not-allowed; }
  .msg { font-size:12px; margin-top:8px; }
  .msg.ok { color:#6fd66f; }
  .msg.err { color:#ff9a9a; }
  .core-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:6px; margin-top:8px; }
  .core { font-size:10px; color:#888; }
  .help { display:inline-flex; align-items:center; justify-content:center; width:14px; height:14px; border-radius:50%; background:#2a2e38; color:#8fb8ff; font-size:10px; cursor:help; margin-left:4px; }
  .help:hover { background:#3a4050; }
  .mode-checks { display:flex; gap:16px; margin-top:10px; }
  .mode-checks label { display:flex; align-items:center; gap:6px; font-size:12px; color:#ccc; cursor:pointer; }
  .mode-checks input[type=radio] { width:auto; margin:0; accent-color:#4f8cff; }
  .sampling-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px 16px; margin-top:8px; }
  .sampling-grid label { display:flex; flex-direction:column; font-size:12px; color:#aaa; margin-top:0; }
  .sampling-grid input { width:100%; padding:5px; margin-top:3px; background:#0f1115; color:#eee; border:1px solid #2a2e38; border-radius:6px; box-sizing:border-box; }
  .sampling-grid .field-header { display:flex; align-items:center; gap:3px; }
  .param-source { font-size:10px; margin-top:6px; padding:4px 8px; border-radius:4px; display:inline-block; }
  .param-source.default { background:#1e2230; color:#666; }
  .param-source.gguf    { background:#1a2e1a; color:#6fd66f; }
  .param-source.json    { background:#1a2440; color:#8fb8ff; }
  .ctx-picker { position:relative; display:flex; gap:6px; align-items:center; }
  .ctx-picker input { flex:1; }
  .ctx-picker-btn { padding:4px 8px; background:#2a2e38; border:1px solid #3a3e4a; border-radius:6px; color:#ccc; cursor:pointer; font-size:12px; white-space:nowrap; }
  .ctx-picker-btn:hover { background:#3a4050; }
  .ctx-dropdown { position:absolute; top:100%; left:0; z-index:999; background:#1a1d24; border:1px solid #3a3e4a; border-radius:8px; padding:4px 0; min-width:130px; box-shadow:0 4px 16px rgba(0,0,0,0.5); display:none; }
  .ctx-dropdown.open { display:block; }
  .ctx-dropdown-item { padding:6px 14px; font-size:12px; color:#ccc; cursor:pointer; }
  .ctx-dropdown-item:hover { background:#2a2e38; color:#fff; }
  .ctx-dropdown-item.active { color:#8fb8ff; font-weight:bold; }
  .ctx-dropdown-item.model-max { color:#6fd66f; }
  .ctx-dropdown-item.model-max::after { content:" ★"; font-size:10px; }
  option.has-params     { background:#1a2e40; color:#8fd4ff; font-weight:bold; }
</style>
</head>
<body>
<h1>AI Server &middot; Gigabyte G431-MM0 &middot; GPU Dashboard <span id="conn-led" class="conn-led" title="Checking connection…"></span></h1>
<div class="sub">Live utilization, CPU/RAM &amp; manual model-to-GPU assignment &middot; updates every 1s</div>

<div class="grid" id="system-grid"></div>

<h2>GPUs <span id="gpu-summary"></span></h2>
<div id="gpu-grid" class="grid"></div>

<div style="margin-top:16px;">
  <button type="button" class="danger" id="btn-stop-all">Emergency Stop &middot; Unload all models</button>
  <span class="help" title="IMMEDIATELY terminates all running llama-server instances on all GPUs (SIGKILL, no graceful shutdown). Use this only in emergencies, e.g. when an instance is hanging, misbehaving, or you need to free the server for another purpose right away. Any in-flight requests will be aborted.">?</span>
  <div id="stop-all-msg" class="msg"></div>
</div>

<h2>Start new model</h2>
<form id="assign-form">
  <label>Model (from AI-Models) <span class="help" title="Models highlighted in light blue have a matching .params.json sidecar file — sampling parameters (temperature, top_p, top_k, etc.) and inference mode are loaded automatically from it. Models without a sidecar file fall back to GGUF metadata or built-in defaults.">?</span></label>
  <select id="model" required></select>
  <div id="model-context-info" style="font-size:11px; color:#888; margin-top:4px;"></div>

  <label>Assign GPU(s) <span class="help" title="Select one or more GPUs on which this model should run. One GPU = normal instance. Multiple GPUs = the model is split (see split mode), required when the model alone does not fit into the VRAM of a single card.">?</span></label>
  <div class="checks" id="gpu-checks"></div>

  <div style="display:flex; gap:16px; margin-top:10px;">
    <div style="flex:1 1 50%; display:flex; align-items:center; gap:6px; padding-top:22px;">
      <input type="checkbox" id="context_shift" style="width:auto; margin:0;">
      <span>Context-Shift</span>
      <span class="help" title="When enabled, llama-server automatically discards the oldest tokens when the maximum context length is reached and makes room for new ones (sliding-window behaviour), instead of rejecting the request with an error. Useful for long, ongoing conversations without a context reset; can reduce quality for tasks that require the full original context (e.g. document analysis) because older information is lost.">?</span>
    </div>
    <div style="flex:1 1 50%;">
      <label>Context length <span class="help" title="How many tokens (prompt + history + response) the model keeps in view at once. Pre-filled automatically with the maximum trained context length of the selected model. You can reduce this to save VRAM/RAM. Values above the model maximum are allowed (e.g. with YaRN RoPE scaling) but will trigger a warning — make sure your model supports the extended context length. Arrow keys step through the standard power-of-two values. Prefer the fixed steps (4096, 8192, 16384 … 1048576) — they match llama.cpp's internal KV-cache layout and avoid unexpected VRAM usage. Only deviate from these steps when the model itself specifies a different trained context length (shown with ★ in the list).">?</span></label>
      <div class="ctx-picker">
        <input type="number" id="context_size" min="1" required>
        <button type="button" class="ctx-picker-btn" id="ctx-picker-btn">▾ Steps</button>
        <div class="ctx-dropdown" id="ctx-dropdown"></div>
      </div>
      <div id="context-size-warning" style="font-size:11px; color:#f4a940; margin-top:3px; display:none;"></div>
    </div>
  </div>

  <label>Port <span class="help" title="TCP port on which this llama-server is reachable (e.g. http://&lt;server-IP&gt;:&lt;port&gt;). Each instance needs its own unused port. Ports 0–1023 are reserved for system services and are not allowed. The next free port starting from 8080 is pre-filled automatically.">?</span></label>
  <input type="number" id="port" min="1024" max="65535" value="8080" required>
  <div id="port-warning" style="font-size:11px; color:#f4a940; margin-top:3px; display:none;">⚠ Ports 0–1023 are reserved for system services and cannot be used.</div>

  <label>Threads <span class="help" title="Number of CPU threads for this instance (tokenization, sampling, GPU coordination — not the actual model computation, which runs on the GPU). With full GPU offloading, 1 thread is usually sufficient; with multiple GPUs in a group, 2 may be useful. Limited to the actual number of CPU cores on this machine.">?</span></label>
  <input type="number" id="threads" min="1" value="1" required>
  <div id="threads-warning" style="font-size:11px; color:#f4a940; margin-top:3px; display:none;"></div>

  <label>Parallel Sessions <span class="help" title="Number of parallel request slots for this instance (llama-server --np). Each slot gets its own share of the configured context size, so raising this splits the context among more simultaneous requests instead of giving each one the full size. Higher values allow more concurrent users/requests at the cost of less context per slot and more VRAM. 1 is right for a single user; use more only if this instance really needs to serve several requests at once.">?</span></label>
  <input type="number" id="parallel" min="1" max="5" value="1" required>

  <label>Split mode (only with &gt;1 GPU) <span class="help" title="Only relevant when multiple GPUs are selected. 'layer': model layers are distributed sequentially across GPUs (pipeline) — usually more compatible and the better starting point. 'row': true tensor parallelism, synchronised between GPUs at every layer — can be faster but requires more bandwidth between cards.">?</span></label>
  <select id="split_mode">
    <option value="layer">layer</option>
    <option value="row">row</option>
  </select>
  <div id="split-mode-warning" style="display:none; font-size:11px; color:#e0c060; margin-top:4px; padding:6px 8px; background:#3a3320; border-radius:6px;">
    ⚠ 'row' (tensor parallelism) requires "split buffers" which are not supported by the Tesla P100 (Pascal, Compute Capability 6.0) — the model will abort on startup with the error "device CUDA0 does not support split buffers". For multi-GPU distribution on P100 please use "layer".
  </div>

  <label style="display:flex; align-items:center; gap:6px; margin-top:14px;">
    <input type="checkbox" id="slots" style="width:auto; margin:0;">
    Enable slots endpoint
    <span class="help" title="Enables the /slots debug endpoint of llama-server (--slots). Allows the dashboard to display the currently occupied context usage live (bar below context length on the GPU tile), instead of only the configured upper limit. Note: /slots may also expose prompt contents depending on the llama.cpp version — usually not critical on an internal LAN, but do not enable for publicly accessible instances.">?</span>
  </label>

  <div style="margin-top:14px;">
    <div style="font-size:12px; color:#aaa; margin-bottom:4px;">
      Inference mode
      <span class="help" title="Selects the sampling parameter preset and sets --reasoning-format accordingly. Instant (instruct): focused responses without a thinking chain — reasoning-format none. Think: internal reasoning chain before answering — reasoning-format deepseek. Think (Coding): optimised for code/math with lower temperature — reasoning-format deepseek. Instant (Reasoning): model reasons internally but outputs only the final answer — reasoning-format none. Modes not present in the model's .params.json are greyed out. Without a .params.json all four modes are available with built-in defaults.">?</span>
    </div>
    <div class="mode-checks" style="display:grid; grid-template-columns:1fr 1fr; gap:6px 16px;">
      <label>
        <input type="radio" name="mode" id="mode-instruct" value="instruct" checked>
        Instant
      </label>
      <label>
        <input type="radio" name="mode" id="mode-think" value="think">
        Think
      </label>
      <label>
        <input type="radio" name="mode" id="mode-think_coding" value="think_coding">
        Think (Coding)
      </label>
      <label>
        <input type="radio" name="mode" id="mode-instruct_reasoning" value="instruct_reasoning">
        Instant (Reasoning)
      </label>
    </div>
  </div>

  <div style="margin-top:14px;">
    <div style="font-size:12px; color:#aaa; margin-bottom:2px;">
      Sampling parameters
      <span class="help" title="These values are loaded automatically from a .params.json sidecar file next to the model (highest priority), from GGUF metadata, or from built-in presets. You can override any value manually before starting. Changes here only affect this start — they are not saved permanently.">?</span>
      <span id="param-source-badge" class="param-source default"></span>
    </div>
    <div class="sampling-grid">
      <label>
        <span class="field-header">Temperature <span class="help" title="Controls randomness of token selection. Lower = more focused/deterministic (0.7 for Instruct), higher = more creative/exploratory (1.0 for Think). Range: 0.0–5.0, neutral: 1.0. Values above 2.0 rarely make sense in practice.">?</span></span>
        <input type="number" id="sp-temp" step="0.05" min="0" max="5">
      </label>
      <label>
        <span class="field-header">Top-P <span class="help" title="Nucleus sampling: keeps only tokens whose cumulative probability reaches this threshold. 0.80 (Instruct) = tighter focus, 0.95 (Think) = wider selection. Range: 0.0–1.0, 1.0 = disabled.">?</span></span>
        <input type="number" id="sp-top_p" step="0.05" min="0" max="1">
      </label>
      <label>
        <span class="field-header">Top-K <span class="help" title="Limits token selection to the K most probable candidates before other filters apply. 20 keeps only the strongest candidates. Range: 0–10000, 0 = disabled. Values above a few hundred rarely make a meaningful difference.">?</span></span>
        <input type="number" id="sp-top_k" step="1" min="0" max="10000">
      </label>
      <label>
        <span class="field-header">Min-P <span class="help" title="Removes tokens whose probability is below this fraction of the top token's probability. 0.0 = disabled (recommended for these presets). Range: 0.0–1.0.">?</span></span>
        <input type="number" id="sp-min_p" step="0.01" min="0" max="1">
      </label>
      <label>
        <span class="field-header">Presence penalty <span class="help" title="Penalises any token that has already appeared at least once in the context, regardless of how often. Encourages the model to introduce new topics and terms. 0.0 (Think) = no penalty, 1.5 (Instruct) = strong diversity push. Range: -2.0–+2.0.">?</span></span>
        <input type="number" id="sp-presence_penalty" step="0.1" min="-2" max="2">
      </label>
      <label>
        <span class="field-header">Repeat penalty <span class="help" title="Divides the logit of already-seen tokens by this factor, suppressing direct repetition loops. 1.0 = neutral (disabled). Values above ~1.3 can make common words like 'the' or 'and' unnatural. Range: 0.01–10.0, 1.0 = neutral.">?</span></span>
        <input type="number" id="sp-repeat_penalty" step="0.05" min="0" max="10">
      </label>
    </div>
  </div>

  <div class="cmd-preview-wrap">
    <div class="cmd-preview-label">
      Command preview
      <span class="help" title="This is the exact command that will be passed to llama-server. It updates automatically when you change any setting above. You can add extra llama-server parameters manually in the field below — only use valid llama-server flags (e.g. --mlock, --numa, --verbose). Invalid parameters will prevent the model from starting. Manual additions are discarded when you change any setting above.">?</span>
    </div>
    <pre id="cmd-preview">Select a model and GPU to see the command.</pre>
  </div>
  <div class="extra-params-wrap">
    <div class="extra-params-label">
      Additional parameters (optional)
      <span class="help" title="Append extra llama-server flags here, e.g. '--mlock' or '--numa distribute'. These are added verbatim to the end of the command. Only valid llama-server parameters are accepted — an unknown flag will cause llama-server to abort on startup. This field is cleared automatically when you change any setting above.">?</span>
    </div>
    <input type="text" id="extra-params" placeholder="e.g. --mlock --numa distribute">
  </div>
  <div class="btn-row">
    <button type="submit" class="success" id="btn-start">Start AI Model</button>
  </div>
  <div id="form-msg" class="msg"></div>
</form>

<script>
let portTouchedByUser = false;
document.getElementById('port').addEventListener('input', () => { portTouchedByUser = true; });

function _formatRateJs(mbPerSec) {
  if (mbPerSec >= 1024) {
    return { value: (mbPerSec / 1024).toFixed(2), unit: 'GB/s' };
  }
  return { value: mbPerSec.toFixed(1), unit: 'MB/s' };
}

document.getElementById('split_mode').addEventListener('change', (e) => {
  document.getElementById('split-mode-warning').style.display = e.target.value === 'row' ? 'block' : 'none';
});

function nextFreePort(processes) {
  const usedPorts = new Set(
    processes.filter(p => p.port).map(p => parseInt(p.port, 10))
  );
  let port = 8080;
  while (usedPorts.has(port)) port++;
  return port;
}

// ---------- Port validation ----------
const portInput = document.getElementById('port');
portInput.addEventListener('input', () => {
  portTouchedByUser = true;
  const val = parseInt(portInput.value);
  const warn = document.getElementById('port-warning');
  if (isFinite(val) && val < 1024) {
    warn.style.display = 'block';
  } else {
    warn.style.display = 'none';
  }
});

// ---------- Threads validation ----------
const threadsInput = document.getElementById('threads');
threadsInput.addEventListener('input', () => {
  _checkThreadsWarning();
});

// ---------- Parallel Sessions validation ----------
const parallelInput = document.getElementById('parallel');
parallelInput.addEventListener('change', () => {
  const min = parseInt(parallelInput.min);
  const max = parseInt(parallelInput.max);
  let val = parseInt(parallelInput.value);
  if (!isFinite(val)) val = 1;
  val = Math.max(min, Math.min(max, val));
  parallelInput.value = val;
});

function _checkThreadsWarning() {
  const warn  = document.getElementById('threads-warning');
  const max   = parseInt(threadsInput.max);
  const val   = parseInt(threadsInput.value);
  if (!warn) return;
  if (isFinite(val) && val < 1) {
    warn.style.display = 'block';
    warn.textContent   = '⚠ Minimum is 1 thread.';
  } else if (isFinite(max) && isFinite(val) && val > max) {
    warn.style.display = 'block';
    warn.textContent   = `⚠ Exceeds CPU core count (${max}). This may degrade performance.`;
  } else {
    warn.style.display = 'none';
    warn.textContent   = '';
  }
}

function setConnLed(online) {
  const led = document.getElementById('conn-led');
  if (!led) return;
  led.className = 'conn-led ' + (online ? 'online' : 'offline');
  led.title = online ? 'Connection to dashboard server active' : 'No connection to dashboard server';
}

async function refresh() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    await fetchModelsWithParams();
    renderSystem(data.system, data.io, data.gpu);
    renderGpus(data);
    renderModelSelect(data.models);

    if (!portTouchedByUser) {
      const procs = (data.processes && data.processes.processes) || [];
      document.getElementById('port').value = nextFreePort(procs);
    }
    // Apply CPU core count as max for threads input
    const coreCount = data.system && data.system.cpu_core_count;
    if (coreCount) {
      const ti = document.getElementById('threads');
      ti.max = coreCount;
      _checkThreadsWarning();
    }
    setConnLed(true);
  } catch (err) {
    setConnLed(false);
  }
}

function renderSystem(sys, io, gpuData) {
  const grid = document.getElementById('system-grid');
  if (!sys) { grid.innerHTML = ''; return; }
  const ramPct = (sys.ram_used_gb / sys.ram_total_gb * 100).toFixed(0);
  const swapPct = sys.swap_total_gb ? (sys.swap_used_gb / sys.swap_total_gb * 100).toFixed(0) : 0;
  const cores = sys.cpu_per_core_pct.map((v, i) =>
    `<div class="core">C${i}: ${v.toFixed(0)}%</div>`
  ).join('');

  const gpus = (gpuData && gpuData.gpus) || [];
  const pcieRxTotal = gpus.reduce((sum, g) => sum + (g.pcie_rx_mb_s || 0), 0);
  const pcieTxTotal = gpus.reduce((sum, g) => sum + (g.pcie_tx_mb_s || 0), 0);
  const pcieAvailable = gpus.some(g => g.pcie_rx_mb_s != null);
  const pcie = pcieAvailable ? {
    total: _formatRateJs(pcieRxTotal + pcieTxTotal),
    rx: _formatRateJs(pcieRxTotal),
    tx: _formatRateJs(pcieTxTotal),
  } : null;

  let diskCard = '';
  if (io && (io.disk || (io.disk_usage && io.disk_usage.length))) {
    const ioRows = io.disk ? `
      <div class="row"><span>Total</span><span>${io.disk.total_value} ${io.disk.total_unit}</span></div>
      <div class="row"><span>Read</span><span>${io.disk.read_value} ${io.disk.read_unit}</span></div>
      <div class="row"><span>Write</span><span>${io.disk.write_value} ${io.disk.write_unit}</span></div>
    ` : '';
    const usageRows = (io.disk_usage || []).map(d => {
      const barColor = d.pct >= 90 ? '#e05c5c' : (d.pct >= 75 ? '#e0a95c' : '#5ce0a0');
      return `
      <div class="row" style="margin-top:6px; color:#ccc;"><span title="${d.device}">${d.mountpoint}</span><span>${d.used_gb} / ${d.total_gb} GB</span></div>
      <div class="bar-bg"><div class="bar-fill" style="width:${d.pct}%; background:${barColor};"></div></div>
      `;
    }).join('');
    diskCard = `
    <div class="card">
      <h3>Disk I/O</h3>
      ${ioRows}
      ${usageRows}
    </div>`;
  }

  let netCard = '';
  if (io && io.interfaces && io.interfaces.length) {
    const rows = io.interfaces.map(nic => `
      <div class="row" style="margin-top:6px; color:#ccc;"><span>${nic.name}</span><span></span></div>
      <div class="row"><span>&darr; Receive</span><span>${nic.rx_value} ${nic.rx_unit}</span></div>
      <div class="row"><span>&uarr; Send</span><span>${nic.tx_value} ${nic.tx_unit}</span></div>
    `).join('');
    netCard = `
    <div class="card">
      <h3>Network</h3>
      ${rows}
    </div>`;
  }

  let pcieCard = '';
  if (pcie) {
    pcieCard = `
    <div class="card">
      <h3>PCIe I/O</h3>
      <div class="row"><span>Total</span><span>${pcie.total.value} ${pcie.total.unit}</span></div>
      <div class="row"><span>Receive (&darr;)</span><span>${pcie.rx.value} ${pcie.rx.unit}</span></div>
      <div class="row"><span>Send (&uarr;)</span><span>${pcie.tx.value} ${pcie.tx.unit}</span></div>
    </div>`;
  }

  grid.innerHTML = `
    <div class="card">
      <h3>CPU <span style="color:#888; font-weight:normal;">Load ${sys.load_avg['1min']?.toFixed(2) ?? '-'}</span></h3>
      <div class="row"><span>Avg. utilization</span><span>${sys.cpu_avg_pct.toFixed(0)}%</span></div>
      <div class="bar-bg"><div class="bar-fill cpu" style="width:${sys.cpu_avg_pct}%"></div></div>
      <div class="core-grid">${cores}</div>
    </div>
    <div class="card">
      <h3>RAM</h3>
      <div class="row"><span>Used</span><span>${sys.ram_used_gb} / ${sys.ram_total_gb} GB</span></div>
      <div class="bar-bg"><div class="bar-fill mem" style="width:${ramPct}%"></div></div>
      <div class="row" style="margin-top:10px;"><span>Swap</span><span>${sys.swap_used_gb} / ${sys.swap_total_gb} GB</span></div>
      <div class="bar-bg"><div class="bar-fill mem" style="width:${swapPct}%"></div></div>
    </div>
    ${pcieCard}
    ${diskCard}
    ${netCard}
  `;
}

// Fixed, well-distinguishable colour palette for the GPU group LEDs;
// grey is reserved for "no active instance" and is not assigned here.
const GPU_GROUP_COLORS = ['#4f8cff', '#ff9f40', '#b56fff', '#3ddc84', '#ff5d8f', '#e0d94f', '#40d9d9', '#ff7a45'];
const _gpuGroupColorMap = new Map(); // pid -> colour, stays stable as long as the process runs

function colorForPid(pid) {
  if (_gpuGroupColorMap.has(pid)) return _gpuGroupColorMap.get(pid);
  const used = new Set(_gpuGroupColorMap.values());
  const free = GPU_GROUP_COLORS.find(c => !used.has(c)) || GPU_GROUP_COLORS[_gpuGroupColorMap.size % GPU_GROUP_COLORS.length];
  _gpuGroupColorMap.set(pid, free);
  return free;
}

function renderGpus(data) {
  const grid = document.getElementById('gpu-grid');
  const gpus = (data.gpu && data.gpu.gpus) || [];
  const procs = (data.processes && data.processes.processes) || [];
  const hostIp = data.host_ip || location.hostname;

  const totalWatts = gpus.reduce((sum, g) => sum + (g.power_w || 0), 0);
  const totalVramUsed = gpus.reduce((sum, g) => sum + g.mem_used_mb, 0) / 1024;
  const totalVramAll = gpus.reduce((sum, g) => sum + g.mem_total_mb, 0) / 1024;
  const avgUtilization = gpus.length ? gpus.reduce((sum, g) => sum + g.utilization_pct, 0) / gpus.length : 0;
  document.getElementById('gpu-summary').textContent =
    gpus.length ? `· ${avgUtilization.toFixed(0)}% utilization · ${totalWatts.toFixed(0)} W total · ${totalVramUsed.toFixed(1)} / ${totalVramAll.toFixed(1)} GB VRAM` : '';

  grid.innerHTML = '';

  // Clean up orphaned colour assignments (process no longer present)
  // so the limited colour palette does not fill up with dead entries
  const activePids = new Set(procs.map(p => p.pid));
  for (const pid of Array.from(_gpuGroupColorMap.keys())) {
    if (!activePids.has(pid)) _gpuGroupColorMap.delete(pid);
  }

  gpus.forEach(g => {
    const memPct = (g.mem_used_mb / g.mem_total_mb * 100).toFixed(0);
    const ownProcs = procs.filter(p => p.gpus && p.gpus.split(',').includes(String(g.index)));
    const groupColor = ownProcs.length ? colorForPid(ownProcs[0].pid) : '#555';

    const card = document.createElement('div');
    card.className = 'card';
    const linkInfo = (g.pcie_link_gen && g.pcie_link_width)
      ? `Gen${g.pcie_link_gen} x${g.pcie_link_width}` : '';
    const pcieRow = `<div class="row"><span>PCIe ${linkInfo}</span><span>&darr;${(g.pcie_rx_mb_s ?? 0).toFixed(0)} &uarr;${(g.pcie_tx_mb_s ?? 0).toFixed(0)} MB/s</span></div>`;
    const ctxValues = ownProcs.filter(p => p.context_size).map(p => {
      if (p.context_shift) return '<span style="font-size:2em; line-height:1; vertical-align:middle;">&#8734;</span>';
      if (p.slots_enabled && p.context_used != null) {
        return `${p.context_used.toLocaleString('en-US')} / ${p.context_size.toLocaleString('en-US')}`;
      }
      return p.context_size.toLocaleString('en-US');
    });
    const multiGpuNote = ownProcs.length && String(ownProcs[0].gpus || '').includes(',')
      ? ' <span class="help" title="This instance is running on multiple GPUs in a group (split). Context length and utilization refer to the entire model, not this individual card — the value is identical on all participating cards.">?</span>'
      : '';
    const ctxPctProc = ownProcs.find(p => p.slots_enabled && p.context_used != null && p.context_size && !p.context_shift);
    const ctxPct = ctxPctProc
      ? ` <span style="color:#888; font-weight:normal;">${Math.min(100, (ctxPctProc.context_used / ctxPctProc.context_size) * 100).toFixed(0)}%</span>`
      : '';
    const ctxRow = ctxValues.length
      ? `<div class="row"><span>Context length${multiGpuNote}${ctxPct}</span><span>${ctxValues.join(' + ')}${ctxValues.some(v => !v.includes('&#8734;') && !v.includes('/')) ? ' Tokens' : ''}</span></div>` : '';
    // Utilization bar for context, analogous to VRAM, only when --slots is active
    // and an actual usage number was provided (not for context-shift/∞).
    const ctxUsageProc = ownProcs.find(p => p.slots_enabled && p.context_used != null && p.context_size && !p.context_shift);
    const ctxUsageBar = ctxUsageProc
      ? `<div class="bar-bg"><div class="bar-fill mem" style="width:${Math.min(100, (ctxUsageProc.context_used / ctxUsageProc.context_size) * 100).toFixed(0)}%"></div></div>`
      : '';
    // GPU label: coloured when active, grey when idle
    const gpuLabelColor = ownProcs.length ? groupColor : '#888';
    // Hardware name: strip vendor prefix and append VRAM capacity
    const hwName = (() => {
      const raw = (g.name || '').trim();
      const vram = g.mem_total_mb ? ` ${(g.mem_total_mb / 1024).toFixed(0)}GB` : '';
      return raw + vram;
    })();
    const modeLabel = ownProcs.length && ownProcs[0].mode_label
      ? `<div style="font-size:11px; color:#8fb8ff; margin-top:2px; margin-bottom:4px;">${ownProcs[0].mode_label}${ownProcs[0].parallel_sessions ? ` <span style="color:#c084fc;">&middot; Sessions: ${ownProcs[0].parallel_sessions}</span>` : ''}</div>`
      : '';
    card.innerHTML = `
      <h3><span style="color:${gpuLabelColor}; font-weight:bold;" title="${ownProcs.length ? 'Active — port ' + ownProcs[0].port : 'Idle'}">GPU ${g.index}</span> <span style="color:#888; font-weight:normal; font-size:13px;">${g.temp_c}&deg;C ${g.power_w ?? '-'}W</span></h3>
      <div style="font-size:11px; color:#aaa; margin-top:-4px; margin-bottom:4px;">${hwName}</div>
      ${modeLabel}
      <div class="row"><span>Load</span><span>${g.utilization_pct}%</span></div>
      <div class="bar-bg"><div class="bar-fill" style="width:${g.utilization_pct}%"></div></div>
      <div class="row"><span>VRAM</span><span>${(g.mem_used_mb/1024).toFixed(1)} / ${(g.mem_total_mb/1024).toFixed(1)} GB</span></div>
      <div class="bar-bg"><div class="bar-fill mem" style="width:${memPct}%"></div></div>
      ${ctxRow}
      ${ctxUsageBar}
      ${pcieRow}
      <div class="procs-container"></div>
    `;
    const procsContainer = card.querySelector('.procs-container');
    if (ownProcs.length) {
      ownProcs.forEach(p => {
        const row = document.createElement('div');
        row.className = 'proc';

        // Header row: link + status badge
        const header = document.createElement('div');
        header.className = 'proc-header';
        const link = document.createElement('a');
        link.setAttribute('href', `http://${hostIp}:${p.port}`);
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
        link.textContent = `:${p.port} → ${p.model}`;
        header.appendChild(link);
        const badge = document.createElement('span');
        if (p.status === 'ready') {
          badge.className = 'status-badge ready';
          badge.title = 'ready';
          badge.innerHTML = '&#10003;';
        } else if (p.status === 'loading') {
          badge.className = 'status-badge loading';
          badge.title = 'loading…';
          badge.innerHTML = '<span class="spin-icon">&#8635;</span>';
        } else {
          badge.className = 'status-badge unreachable';
          badge.title = 'unreachable';
          badge.innerHTML = '&#33;';
        }
        header.appendChild(badge);
        row.appendChild(header);

        // Button row: AI Log / Data Log / Stop
        const btns = document.createElement('div');
        btns.className = 'proc-btns';
        const aiLogBtn = document.createElement('button');
        aiLogBtn.textContent = 'AI Log';
        aiLogBtn.className = 'log-btn';
        aiLogBtn.title = 'Open llama-server log in a new window';
        aiLogBtn.onclick = () => window.open(`/api/log/${p.port}`, '_blank', 'noopener,noreferrer');
        btns.appendChild(aiLogBtn);
        const dataLogBtn = document.createElement('button');
        dataLogBtn.textContent = 'Data Log';
        dataLogBtn.className = 'data-log-btn';
        dataLogBtn.title = 'Open GPU/CPU/RAM metrics data log in a new window';
        dataLogBtn.onclick = () => window.open(`/api/datalog/${p.port}`, '_blank', 'noopener,noreferrer');
        btns.appendChild(dataLogBtn);
        const deleteLogBtn = document.createElement('button');
        deleteLogBtn.textContent = 'Delete Log';
        deleteLogBtn.className = 'delete-log-btn';
        deleteLogBtn.title = 'Delete both log files (AI Log + Data Log) for this model and start fresh ones with a new header';
        deleteLogBtn.onclick = () => deleteLog(p.port, p.model);
        btns.appendChild(deleteLogBtn);
        const stopBtn = document.createElement('button');
        stopBtn.textContent = 'Stop';
        stopBtn.title = 'Stop this model instance (SIGKILL)';
        stopBtn.onclick = () => stopProcess(p.pid);
        btns.appendChild(stopBtn);
        row.appendChild(btns);
        procsContainer.appendChild(row);
      });
    } else {
      procsContainer.innerHTML = '<div class="free">free</div>';
    }
    grid.appendChild(card);
  });

  const busyGpus = new Set();
  procs.forEach(p => {
    if (p.gpus) p.gpus.split(',').forEach(g => busyGpus.add(g));
  });

  const checks = document.getElementById('gpu-checks');
  const checkedBefore = new Set(
    Array.from(checks.querySelectorAll('input:checked')).map(c => c.value)
  );
  checks.innerHTML = gpus.map(g => {
    const isBusy = busyGpus.has(String(g.index));
    // Busy GPUs are never pre-selected, even if they were checked before
    const wasChecked = !isBusy && checkedBefore.has(String(g.index));
    return `<label class="${isBusy ? 'disabled' : ''}">
      <input type="checkbox" value="${g.index}" ${wasChecked ? 'checked' : ''} ${isBusy ? 'disabled' : ''}>
      GPU ${g.index}${isBusy ? ' (in use)' : ''}
    </label>`;
  }).join('');
}

let _modelsWithParams = new Set();

async function fetchModelsWithParams() {
  try {
    const res = await fetch('/api/models-with-params');
    const data = await res.json();
    _modelsWithParams = new Set(data.models_with_params || []);
  } catch (e) { /* silently ignore */ }
}

function renderModelSelect(models) {
  const sel = document.getElementById('model');
  if (sel.options.length !== models.length) {
    sel.innerHTML = models.map(m => {
      const hasParams = _modelsWithParams.has(m);
      const cls = hasParams ? ' class="has-params"' : '';
      const suffix = hasParams ? ' ✦' : '';
      return `<option value="${m}"${cls}>${m}${suffix}</option>`;
    }).join('');
    if (!sel.dataset.listenerAttached) {
      sel.addEventListener('change', updateModelContextInfo);
      sel.dataset.listenerAttached = '1';
    }
    updateModelContextInfo();
  }
}

let contextSizeTouchedByUser = false;
const _CTX_STEPS = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576];

document.getElementById('context_size').addEventListener('input', () => {
  contextSizeTouchedByUser = true;
  _checkContextWarning(document.getElementById('context_size'));
});

document.getElementById('context_size').addEventListener('keydown', (e) => {
  const ctxInput = e.target;
  const modelMax = parseInt(ctxInput.dataset.modelMax) || null;
  // Build step list: standard powers-of-two steps + model max if not already included
  let steps = [..._CTX_STEPS];
  if (modelMax && !steps.includes(modelMax)) {
    steps = [...steps, modelMax].sort((a, b) => a - b);
  }
  const cur = parseInt(ctxInput.value);
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    const next = steps.find(s => s > cur);
    if (next) { ctxInput.value = next; contextSizeTouchedByUser = true; _checkContextWarning(ctxInput); }
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    const prev = [...steps].reverse().find(s => s < cur);
    if (prev) { ctxInput.value = prev; contextSizeTouchedByUser = true; _checkContextWarning(ctxInput); }
  }
});

function _checkContextWarning(ctxInput) {
  const warn = document.getElementById('context-size-warning');
  if (!warn) return;
  const modelMax = parseInt(ctxInput.dataset.modelMax);
  const val      = parseInt(ctxInput.value);
  if (!isFinite(val)) { warn.style.display = 'none'; warn.textContent = ''; return; }
  if (modelMax && val > modelMax) {
    warn.style.display = 'block';
    warn.textContent = '⚠ Above model maximum — only valid with extended context support (e.g. YaRN).';
  } else if (!_CTX_STEPS.includes(val) && val !== modelMax) {
    warn.style.display = 'block';
    warn.textContent = '⚠ Non-standard value — use a power-of-two step (4096, 8192 … 1048576) to avoid unexpected VRAM usage in llama.cpp.';
  } else {
    warn.style.display = 'none';
    warn.textContent = '';
  }
  _renderCtxDropdown();
}

// ---------- Custom context-length dropdown ----------
function _renderCtxDropdown() {
  const ctxInput = document.getElementById('context_size');
  const dropdown = document.getElementById('ctx-dropdown');
  if (!dropdown) return;
  const modelMax = parseInt(ctxInput.dataset.modelMax) || null;
  const cur      = parseInt(ctxInput.value);
  // Build full step list, inserting model max if not already present
  let steps = [..._CTX_STEPS];
  if (modelMax && !steps.includes(modelMax)) {
    steps = [...steps, modelMax].sort((a, b) => a - b);
  }
  dropdown.innerHTML = steps.map(s => {
    const isActive   = s === cur;
    const isModelMax = s === modelMax;
    let cls = 'ctx-dropdown-item';
    if (isActive)   cls += ' active';
    if (isModelMax) cls += ' model-max';
    return `<div class="${cls}" data-val="${s}">${s.toLocaleString('en-US')}</div>`;
  }).join('');
  dropdown.querySelectorAll('.ctx-dropdown-item').forEach(item => {
    item.addEventListener('mousedown', (e) => {
      e.preventDefault();
      ctxInput.value = item.dataset.val;
      contextSizeTouchedByUser = true;
      _checkContextWarning(ctxInput);
      ctxInput.dispatchEvent(new Event('input', { bubbles: true }));
      dropdown.classList.remove('open');
    });
  });
}

(function _initCtxDropdown() {
  const btn      = document.getElementById('ctx-picker-btn');
  const dropdown = document.getElementById('ctx-dropdown');
  const ctxInput = document.getElementById('context_size');
  if (!btn || !dropdown) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    _renderCtxDropdown();
    dropdown.classList.toggle('open');
  });
  ctxInput.addEventListener('focus', () => {
    _renderCtxDropdown();
    dropdown.classList.add('open');
  });
  ctxInput.addEventListener('blur', () => {
    // Small delay so mousedown on an item fires first
    setTimeout(() => dropdown.classList.remove('open'), 150);
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.ctx-picker')) dropdown.classList.remove('open');
  });
})();

async function updateModelContextInfo() {
  const model = document.getElementById('model').value;
  const infoEl = document.getElementById('model-context-info');
  const ctxInput = document.getElementById('context_size');
  if (!model) { infoEl.textContent = ''; return; }
  infoEl.textContent = 'Determining context length…';
  try {
    const res = await fetch(`/api/model-context-length?model=${encodeURIComponent(model)}`);
    const data = await res.json();
    if (data.context_length) {
      infoEl.textContent = `Maximum trained context length: ${data.context_length.toLocaleString('en-US')} tokens`;
      if (!contextSizeTouchedByUser) {
        ctxInput.value = data.context_length;
      }
      ctxInput.dataset.modelMax = data.context_length;
      _checkContextWarning(ctxInput);
    } else {
      infoEl.textContent = 'Context length could not be determined.';
      ctxInput.dataset.modelMax = '';
      _checkContextWarning(ctxInput);
    }
  } catch (err) {
    infoEl.textContent = '';
  }
  // Load matching sampling parameters for the current mode
  const mode = document.querySelector('input[name="mode"]:checked')?.value || 'instruct';
  loadSamplingParams(model, mode);
}

// Clamp a numeric value to [lo, hi]; returns null if the value is not finite.
function _clampNum(val, lo, hi) {
  if (!isFinite(val)) return null;
  if (lo != null && val < lo) return lo;
  if (hi != null && val > hi) return hi;
  return val;
}

function _readSamplingField(id, parser, lo, hi) {
  const raw = parser(document.getElementById(id).value);
  return _clampNum(raw, lo, hi);
}

function getFormValues() {
  const mode = document.querySelector('input[name="mode"]:checked')?.value || 'instruct';
  return {
    model: document.getElementById('model').value,
    port: document.getElementById('port').value,
    threads: document.getElementById('threads').value,
    parallel: document.getElementById('parallel').value,
    split_mode: document.getElementById('split_mode').value,
    context_shift: document.getElementById('context_shift').checked,
    context_size: document.getElementById('context_size').value,
    slots: document.getElementById('slots').checked,
    gpus: Array.from(document.querySelectorAll('#gpu-checks input:checked:not(:disabled)')).map(c => c.value).join(','),
    mode,
    sampling: {
      temp:             _readSamplingField('sp-temp',             parseFloat, 0,     5),
      top_p:            _readSamplingField('sp-top_p',            parseFloat, 0,     1),
      top_k:            _readSamplingField('sp-top_k',            parseInt,   0, 10000),
      min_p:            _readSamplingField('sp-min_p',            parseFloat, 0,     1),
      presence_penalty: _readSamplingField('sp-presence_penalty', parseFloat, -2,    2),
      repeat_penalty:   _readSamplingField('sp-repeat_penalty',   parseFloat, 0.01, 10),
    },
  };
}

// ---------- Sampling parameter helpers ----------

async function loadSamplingParams(model, mode) {
  if (!model) return;
  try {
    const res = await fetch(`/api/model-sampling-params?model=${encodeURIComponent(model)}&mode=${mode}`);
    const data = await res.json();
    if (data.params) {
      const p = data.params;
      document.getElementById('sp-temp').value            = p.temp            ?? '';
      document.getElementById('sp-top_p').value           = p.top_p           ?? '';
      document.getElementById('sp-top_k').value           = p.top_k           ?? '';
      document.getElementById('sp-min_p').value           = p.min_p           ?? '';
      document.getElementById('sp-presence_penalty').value = p.presence_penalty ?? '';
      document.getElementById('sp-repeat_penalty').value  = p.repeat_penalty  ?? '';
    }
    const badge = document.getElementById('param-source-badge');
    const src = data.source || 'default';
    const labels = { 'params.json': ['json', '📄 from .params.json'], gguf: ['gguf', '📦 from GGUF metadata'], default: ['default', '⚙️ built-in defaults'] };
    const [cls, text] = labels[src] || labels['default'];
    badge.className = `param-source ${cls}`;
    badge.textContent = text;
    // Enable/disable mode radio buttons based on available_modes
    const available = data.available_modes || ['instruct', 'think', 'think_coding', 'instruct_reasoning'];
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
      const avail = available.includes(radio.value);
      radio.disabled = !avail;
      radio.closest('label').style.opacity = avail ? '' : '0.35';
      radio.closest('label').style.cursor  = avail ? '' : 'not-allowed';
      radio.closest('label').title = avail ? '' : 'Not defined in .params.json for this model';
      if (!avail && radio.checked) {
        const first = document.querySelector(`input[name="mode"][value="${available[0]}"]`);
        if (first) { first.checked = true; }
      }
    });
  } catch (e) { /* silently ignore */ }
}

document.querySelectorAll('input[name="mode"]').forEach(radio => {
  radio.addEventListener('change', () => {
    const model = document.getElementById('model').value;
    const mode = document.querySelector('input[name="mode"]:checked').value;
    loadSamplingParams(model, mode);
  });
});

function showMsg(text, ok) {
  const el = document.getElementById('form-msg');
  el.textContent = text;
  el.className = 'msg ' + (ok ? 'ok' : 'err');
}

// ---------- Live command preview ----------
let _previewDirty = false;   // true while user has typed extra params

async function updateCommandPreview() {
  const vals = getFormValues();
  const preview = document.getElementById('cmd-preview');
  if (!vals.model || !vals.gpus) {
    preview.textContent = 'Select a model and GPU to see the command.';
    return;
  }
  try {
    const res = await fetch('/api/start-command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(vals)
    });
    const data = await res.json();
    const cmd = data.command || data.error || '';
    const extra = document.getElementById('extra-params').value.trim();
    preview.textContent = extra ? cmd + ' ' + extra : cmd;
  } catch (e) {
    preview.textContent = 'Error fetching command preview.';
  }
}

// Clear extra-params and refresh preview when any control changes
function _onSettingChanged() {
  const ep = document.getElementById('extra-params');
  if (ep.value.trim()) {
    ep.value = '';
    _previewDirty = false;
  }
  updateCommandPreview();
}

// Hook all form controls to live-update the preview via event delegation.
// Delegation on the form element catches events from dynamically re-rendered
// children (GPU checkboxes, model select) without needing to re-attach listeners.
document.getElementById('assign-form').addEventListener('change', (e) => {
  if (e.target.id === 'extra-params') return;  // handled separately below
  _onSettingChanged();
});
document.getElementById('assign-form').addEventListener('input', (e) => {
  if (e.target.id === 'extra-params') return;
  _onSettingChanged();
});
// extra-params: only update preview text, do not clear
document.getElementById('extra-params').addEventListener('input', () => {
  _previewDirty = true;
  updateCommandPreview();
});

document.getElementById('assign-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const vals = getFormValues();
  if (!vals.gpus) { showMsg('Please select at least one GPU.', false); return; }
  const extra = document.getElementById('extra-params').value.trim();
  if (extra) vals.extra_params = extra;
  const res = await fetch('/api/start', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(vals)
  });
  const data = await res.json();
  if (data.ok) {
    showMsg(`Started (PID ${data.pid}) — Log: ${data.log}`, true);
    portTouchedByUser = false;
    contextSizeTouchedByUser = false;
    document.getElementById('extra-params').value = '';
    updateCommandPreview();
    // Several quick follow-up polls, because the /slots endpoint (for the context bar)
    // only responds once the server has fully started — this can take a while
    // depending on the model size.
    [800, 1800, 3500, 6000].forEach(delay => setTimeout(refresh, delay));
  } else {
    showMsg(data.error || 'Error starting instance', false);
  }
});

async function deleteLog(port, model) {
  if (!confirm(`Delete both log files for "${model}" (port ${port})?\n\nA new empty log file with a fresh header will be created immediately afterwards.`)) return;
  try {
    const res = await fetch('/api/delete-log', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({port})
    });
    const data = await res.json();
    if (!data.ok) alert(data.error || 'Error deleting log files');
  } catch (e) {
    alert('Error deleting log files.');
  }
}

async function stopProcess(pid) {
  if (!confirm(`Really terminate process PID ${pid}?`)) return;
  const res = await fetch('/api/stop', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({pid})
  });
  const data = await res.json();
  if (!data.ok) alert(data.error || 'Error stopping instance');
  refresh();
}

document.getElementById('btn-stop-all').addEventListener('click', async () => {
  if (!confirm('Really unload ALL running models immediately? In-flight requests will be aborted.')) return;
  const msgEl = document.getElementById('stop-all-msg');
  msgEl.textContent = 'Terminating…';
  msgEl.className = 'msg';
  const res = await fetch('/api/stop-all', { method: 'POST' });
  const data = await res.json();
  if (data.ok) {
    msgEl.textContent = `${data.stopped.length} instance(s) terminated${data.failed.length ? `, ${data.failed.length} failed` : ''}.`;
    msgEl.className = 'msg ' + (data.failed.length ? 'err' : 'ok');
  } else {
    msgEl.textContent = data.error || 'Error while terminating.';
    msgEl.className = 'msg err';
  }
  refresh();
});

refresh();
setInterval(refresh, 1000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=False, threaded=True)
