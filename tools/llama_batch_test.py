#!/usr/bin/env python3
"""
llama_batch_test.py
====================
Automatisierter Batch-Test gegen llama-server (OpenAI-kompatible API).
Verwendet rohe TCP-Sockets ohne http.client — verhindert Keep-Alive-Hänger.

Konfiguration: Abschnitt CONFIG unten anpassen.
"""

import json
import time
import datetime
import sys
import socket
import urllib.request
from urllib.parse import urlparse

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
LLAMA_SERVER_URL = "http://192.168.1.22:8888"

MODEL        = "qwen3.5-4B-Q4-GPU"

PROMPT = """Lade die Datei /data/Arbeitsanweisung.txt und befolge die Arbeitsschritte in der korrekten Reiehnfolge. Achte darauf, dass 10 Arbeitspunkte abgearbeitet werden. Führe alle Arbeitsschritte aus ohne anzuhalten. Kann ein Punkt nicht ausgeführt werden, so gehe zum nächsten Punkt und protokolliere den Grund in der Ergebnisdatei. Beachte beim Laden der ADD-Gerätebeschreibung, dass es sich um eine Aktionsspezifikation handelt. Insbesondere wird dort die korrekte Tool-Nutzung beschrieben. Damit bekommst Du die physische Kontrolle über die Hardware. Bei Aufgaben, die echte Hardware-Interaktion oder sequenzielle Tool-Nutzung erfordern, muss die Handlungsabfolge (Planen -> Handeln -> Verifizieren) strikt eingehalten werden, nicht nur die logische Reihenfolge der Punkte. "Ausführen" bedeutet immer: Tool aufrufen, Antwort warten, Ergebnis nutzen. Achtung! Das ist keine Simulation. Das ist ein realer Einsatz."""

SYSTEM_PROMPT   = "You are a helpful assistant."  # None zum Deaktivieren

REPEAT_COUNT    = 50
MAX_TOKENS      = 4096
TEMPERATURE     = 0.7
CONNECT_TIMEOUT = 10    # Sekunden für TCP-Connect
READ_TIMEOUT    = 300   # Sekunden ohne Daten → Timeout

OUTPUT_FILE = "batch_results.jsonl"
VERBOSE     = True
# ─────────────────────────────────────────────


def build_messages():
    messages = []
    if SYSTEM_PROMPT:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": PROMPT})
    return messages


def raw_http_post(host, port, path, body_bytes, connect_timeout, read_timeout):
    """
    Führt einen einzelnen HTTP/1.0 POST über einen rohen TCP-Socket durch.
    HTTP/1.0 hat kein Keep-Alive — Server schließt Verbindung nach Response.
    Gibt den Response-Body als bytes zurück (chunked wird manuell dekodiert).
    """
    request = (
        f"POST {path} HTTP/1.0\r\n"
        f"Host: {host}:{port}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode("utf-8") + body_bytes

    sock = socket.create_connection((host, port), timeout=connect_timeout)
    sock.settimeout(read_timeout)

    try:
        sock.sendall(request)

        # Rohe Antwort einlesen bis Verbindung geschlossen
        raw = b""
        while True:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                raw += chunk
            except socket.timeout:
                break  # Keine Daten mehr
    finally:
        sock.close()

    # HTTP-Header vom Body trennen
    header_end = raw.find(b"\r\n\r\n")
    if header_end == -1:
        raise ValueError("Kein HTTP-Header-Ende gefunden")

    headers_raw = raw[:header_end].decode("utf-8", errors="replace")
    body        = raw[header_end + 4:]

    # Status-Code aus erster Header-Zeile
    status_line = headers_raw.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1])

    return status_code, body


def send_prompt(run_index: int) -> dict:
    parsed = urlparse(LLAMA_SERVER_URL)
    host   = parsed.hostname
    port   = parsed.port or 80

    payload = {
        "messages":    build_messages(),
        "max_tokens":  MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream":      True,
    }
    if MODEL:
        payload["model"] = MODEL

    body_bytes = json.dumps(payload).encode("utf-8")

    t_start       = time.monotonic()
    model_id      = MODEL or "unknown"
    content_parts = []
    tool_calls    = {}
    finish_reason = None
    tokens_prompt = None
    tokens_compl  = None

    try:
        status, body = raw_http_post(
            host, port, "/v1/chat/completions",
            body_bytes, CONNECT_TIMEOUT, READ_TIMEOUT
        )

        if status != 200:
            return _error(run_index, model_id,
                          f"HTTP {status}: {body[:300].decode('utf-8', errors='replace')}",
                          t_start)

        # SSE-Zeilen parsen
        for raw_line in body.split(b"\n"):
            line = raw_line.decode("utf-8", errors="replace").strip()

            if not line.startswith("data:"):
                continue

            payload_str = line[len("data:"):].strip()

            if payload_str == "[DONE]":
                break

            try:
                sse = json.loads(payload_str)
            except json.JSONDecodeError:
                continue

            if "model" in sse:
                model_id = sse["model"]

            if sse.get("usage"):
                tokens_prompt = sse["usage"].get("prompt_tokens")
                tokens_compl  = sse["usage"].get("completion_tokens")

            for choice in sse.get("choices", []):
                delta = choice.get("delta", {})

                fr = choice.get("finish_reason")
                if fr:
                    finish_reason = fr

                token = delta.get("content")
                if token:
                    content_parts.append(token)

                for tc_delta in delta.get("tool_calls", []):
                    idx  = tc_delta.get("index", 0)
                    func = tc_delta.get("function", {})
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.get("id"):
                        tool_calls[idx]["id"] = tc_delta["id"]
                    if func.get("name"):
                        tool_calls[idx]["name"] += func["name"]
                    if func.get("arguments"):
                        tool_calls[idx]["arguments"] += func["arguments"]

        elapsed = time.monotonic() - t_start
        content = "".join(content_parts)
        tc_list = [tool_calls[k] for k in sorted(tool_calls)] if tool_calls else None

        if tokens_compl is None:
            tokens_compl = len(content_parts)

        return {
            "run":           run_index,
            "timestamp":     datetime.datetime.now().isoformat(),
            "model":         model_id,
            "prompt":        PROMPT,
            "response":      content,
            "tool_calls":    tc_list,
            "finish_reason": finish_reason,
            "tokens_prompt": tokens_prompt,
            "tokens_compl":  tokens_compl,
            "elapsed_s":     round(elapsed, 3),
            "error":         None,
        }

    except socket.timeout:
        return _error(run_index, model_id,
                      f"Timeout: {READ_TIMEOUT}s ohne Daten", t_start)
    except Exception as e:
        return _error(run_index, model_id, str(e), t_start)


def _error(run_index, model_id, msg, t_start):
    return {
        "run": run_index, "timestamp": datetime.datetime.now().isoformat(),
        "model": model_id, "prompt": PROMPT, "response": None,
        "tool_calls": None, "finish_reason": None,
        "tokens_prompt": None, "tokens_compl": None,
        "error": msg,
        "elapsed_s": round(time.monotonic() - t_start, 3),
    }


def check_server():
    try:
        with urllib.request.urlopen(f"{LLAMA_SERVER_URL}/health", timeout=5) as r:
            status = json.loads(r.read()).get("status", "?")
            print(f"[INFO] llama-server erreichbar — Status: {status}")
            return True
    except Exception as e:
        print(f"[ERROR] llama-server nicht erreichbar: {e}")
        return False


def main():
    print("=" * 60)
    print(f"  llama Batch-Test  |  {REPEAT_COUNT}x Wiederholungen")
    print("=" * 60)

    if not check_server():
        sys.exit(1)

    errors       = 0
    total_tokens = 0
    total_time   = 0.0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i in range(1, REPEAT_COUNT + 1):
            print(f"\n[{i:>3}/{REPEAT_COUNT}] Sende Prompt ...", end=" ", flush=True)

            result = send_prompt(i)
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()

            if result["error"]:
                errors += 1
                print(f"FEHLER: {result['error'][:80]}")
            else:
                tok = result.get("tokens_compl") or 0
                total_tokens += tok
                total_time   += result["elapsed_s"]
                tps = round(tok / result["elapsed_s"], 1) if result["elapsed_s"] > 0 else "?"
                tc  = result.get("tool_calls")
                tc_info = f"  {len(tc)} tool_call(s)" if tc else ""
                print(f"OK  {result['elapsed_s']:.1f}s  {tok} tok  ({tps} t/s){tc_info}")

                if VERBOSE and result["response"]:
                    preview = result["response"].replace("\n", " ")[:120]
                    print(f"         → {preview}")

                if VERBOSE and result.get("tool_calls"):
                    for tc in result["tool_calls"]:
                        print(f"         🔧 {tc['name']}({tc['arguments'][:80]})")

    ok_runs = REPEAT_COUNT - errors
    print("\n" + "=" * 60)
    print("  ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Läufe gesamt : {REPEAT_COUNT}")
    print(f"  Erfolgreich  : {ok_runs}")
    print(f"  Fehler       : {errors}")
    if ok_runs > 0:
        print(f"  Ø Zeit/Run   : {total_time / ok_runs:.2f}s")
        print(f"  Ø Token/Run  : {total_tokens // ok_runs}")
        if total_time > 0:
            print(f"  Ø Throughput : {total_tokens / total_time:.1f} t/s")
    print(f"  Ergebnisse   : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
