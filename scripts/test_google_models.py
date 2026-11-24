"""Google Direct Gemini Model Discovery & Tool-Calling Benchmark.

Tests all available Google Gemini models for:
1. Basic generateContent response + latency (ms)
2. Tool / Function Calling support with hb_place_order schema

ZERO SECRETS LEAK: API keys are read securely from environment or config files
and are never logged, printed, or committed.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def get_google_api_key() -> str:
    """Finds Google / Gemini API key without printing or exposing it."""
    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_KEY"):
        val = (os.getenv(env_var) or "").strip()
        if val:
            return val

    # Search in .env files
    candidates = [Path(".env"), Path.home() / ".hermes" / ".env"]
    for path in candidates:
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_KEY") and v:
                            return v
            except Exception:
                pass
    return ""


def list_gemini_models(api_key: str) -> list[str]:
    """Queries Google API to list all available models."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Benchmark/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            candidate_ids = []
            for m in models:
                name = m.get("name", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" not in methods:
                    continue
                clean_id = name.replace("models/", "").strip()
                lower = clean_id.lower()
                if any(x in lower for x in ("embedding", "imagen", "aqa", "tts", "veo", "learnlm", "robotics", "lyria", "clip")):
                    continue
                candidate_ids.append(clean_id)
            return candidate_ids
    except Exception as exc:
        print(f"Error listing models: {exc}", file=sys.stderr)
        return []


def test_basic_generate(model_id: str, api_key: str) -> tuple[bool, float, str]:
    """Tests basic text generation and measures round-trip latency in milliseconds."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Reply with only the word OK."}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 10},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            latency_ms = (time.perf_counter() - t0) * 1000
            res = json.loads(resp.read().decode("utf-8"))
            text = ""
            for c in res.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "text" in p:
                        text += p["text"]
            return True, round(latency_ms, 1), text.strip()
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000
        return False, round(latency_ms, 1), str(exc)


def test_tool_calling(model_id: str, api_key: str) -> tuple[bool, float, str]:
    """Tests function calling support using hb_place_order schema."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    tool_def = {
        "function_declarations": [
            {
                "name": "hb_place_order",
                "description": "Submit a virtual BUY or SELL order.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "symbol": {"type": "STRING", "description": "Ticker symbol e.g. BANKASIA"},
                        "side": {"type": "STRING", "enum": ["BUY", "SELL"], "description": "Order side"},
                        "quantity": {"type": "INTEGER", "description": "Number of shares"},
                        "price": {"type": "NUMBER", "description": "Limit price in BDT"},
                    },
                    "required": ["symbol", "side", "quantity"],
                },
            }
        ]
    }
    payload = {
        "contents": [{"parts": [{"text": "Preview buy 10 BANKASIA at 18.40"}]}],
        "tools": [tool_def],
        "tool_config": {
            "function_calling_config": {
                "mode": "ANY"
            }
        },
        "generationConfig": {"temperature": 0.0},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            latency_ms = (time.perf_counter() - t0) * 1000
            res = json.loads(resp.read().decode("utf-8"))
            for c in res.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "functionCall" in p:
                        fc = p["functionCall"]
                        fn_name = fc.get("name")
                        fn_args = fc.get("args", {})
                        if fn_name == "hb_place_order":
                            return True, round(latency_ms, 1), f"Called {fn_name}({fn_args})"
            return False, round(latency_ms, 1), "No functionCall in response parts"
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000
        return False, round(latency_ms, 1), str(exc)


def main() -> None:
    api_key = get_google_api_key()
    if not api_key:
        print("ERROR: No Google API key found in env or .env files.", file=sys.stderr)
        sys.exit(1)

    print("Fetching active Google Gemini models...")
    models = list_gemini_models(api_key)
    print(f"Found {len(models)} candidate models.")

    priority_candidates = [
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.1-pro-preview",
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-omni-flash-preview",
    ]

    # Select existing models from priority list first, then any other gemini chat models
    candidates_to_test = [m for m in priority_candidates if m in models]
    remaining = [m for m in models if m not in candidates_to_test and ("gemini" in m or "gemma" in m)]
    candidates_to_test.extend(remaining[: 12 - len(candidates_to_test)])

    results = []
    print("\nRunning smoke tests (Basic generation & Tool calling)...")
    for m in candidates_to_test:
        sys.stdout.write(f"Testing {m:<32} ... ")
        sys.stdout.flush()

        time.sleep(1.0)
        basic_ok, basic_lat, basic_info = test_basic_generate(m, api_key)
        tool_ok = False
        tool_lat = 0.0
        tool_info = ""

        if basic_ok:
            time.sleep(1.0)
            tool_ok, tool_lat, tool_info = test_tool_calling(m, api_key)

        status = "PASSED" if (basic_ok and tool_ok) else ("TEXT_ONLY" if basic_ok else "FAILED")
        print(f"[{status}] Basic: {basic_lat}ms, Tool: {tool_lat}ms")

        results.append({
            "model_id": m,
            "basic_ok": basic_ok,
            "basic_latency_ms": basic_lat,
            "tool_call_ok": tool_ok,
            "tool_latency_ms": tool_lat,
            "status": status,
            "detail": tool_info if tool_ok else basic_info,
        })

    # Print Table
    col_w = [34, 10, 14, 12, 10]
    header = f"{'Model ID':<{col_w[0]}} | {'Basic OK':<{col_w[1]}} | {'Tool-Call OK':<{col_w[2]}} | {'Latency ms':<{col_w[3]}} | {'Status':<{col_w[4]}}"
    sep = f"{'-'*col_w[0]}-+-{'-'*col_w[1]}-+-{'-'*col_w[2]}-+-{'-'*col_w[3]}-+-{'-'*col_w[4]}"

    print("\n" + "=" * len(header))
    print("GOOGLE DIRECT GEMINI MODELS BENCHMARK REPORT")
    print("=" * len(header))
    print(header)
    print(sep)
    for r in results:
        b_str = "YES" if r["basic_ok"] else "NO"
        t_str = "YES" if r["tool_call_ok"] else "NO"
        lat = r["tool_latency_ms"] if r["tool_call_ok"] else r["basic_latency_ms"]
        lat_str = f"{lat:.0f} ms"
        print(f"{r['model_id']:<{col_w[0]}} | {b_str:<{col_w[1]}} | {t_str:<{col_w[2]}} | {lat_str:<{col_w[3]}} | {r['status']:<{col_w[4]}}")
    print("=" * len(header) + "\n")

    # Save redacted report
    report_path = Path("scratch/google_models_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Benchmark results written to {report_path}")


if __name__ == "__main__":
    main()
