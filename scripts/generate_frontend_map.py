#!/usr/bin/env python3
"""Auto-Generated Frontend & Extension Knowledge Map Generator.

Zero external dependencies: uses only Python stdlib (ast, pathlib, re, json).
Audits UI hierarchy, Dark vs Light mode CSS parity, Backend-Frontend field contracts,
JS DOM bindings & API endpoints, and Extension sniffer selectors.
Produces `documentation/FRONTEND_MAP.md`.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "documentation" / "FRONTEND_MAP.md"


def audit_css_dark_light_parity() -> tuple[list[dict[str, str]], int]:
    """Audits dark backgrounds in styles.css vs light overrides in theme_light_hermes.css."""
    styles_css = (REPO_ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    light_css = (REPO_ROOT / "frontend" / "theme_light_hermes.css").read_text(encoding="utf-8")

    # Extract all [data-theme="light"] rules in light_css
    light_blocks = re.findall(r'\[data-theme=[\'"]light[\'"]\]\s*([^{]+)\{([^}]+)\}', light_css)
    light_map: dict[str, str] = {}
    for sel_group, body in light_blocks:
        bg_match = re.search(r'background(?:-color)?:\s*([^;!]+)', body)
        bg_val = bg_match.group(1).strip() if bg_match else "inherit"
        for sel in sel_group.split(","):
            s = sel.strip()
            # clean any remaining [data-theme="light"]
            s = re.sub(r'\[data-theme=[\'"]light[\'"]\]\s*', "", s).strip()
            if s:
                light_map[s] = bg_val

    # Targets to inspect in styles.css
    target_tokens = (
        ".tx-",
        "#tx-",
        "#company-search",
        ".tx-search-wrap",
        ".tx-ticket-header",
        ".tx-panel-header",
        "#tx-depth-table",
        ".tx-depth-foot",
        ".tx-depth-hint",
    )

    style_blocks = re.findall(r'([^{}]+)\{([^{}]+)\}', styles_css)
    audit_results: list[dict[str, str]] = []
    missing_count = 0

    seen_selectors: set[str] = set()

    for raw_sel, body in style_blocks:
        sel_clean = re.sub(r'/\*.*?\*/', '', raw_sel).strip()
        if not sel_clean or not any(token in sel_clean for token in target_tokens):
            continue

        bg_match = re.search(r'background(?:-color)?:\s*([#a-zA-Z0-9(),\.\s]+);', body)
        if not bg_match:
            continue

        dark_val = bg_match.group(1).strip()
        is_dark = bool(
            re.match(r'#(?:0|1|2)[0-9a-fA-F]{2,5}', dark_val)
            or dark_val.startswith("rgb(0")
            or dark_val.startswith("rgba(0")
            or dark_val.startswith("rgba(10")
        )
        if not is_dark:
            continue

        for sub_sel in sel_clean.split(","):
            sub_s = sub_sel.strip()
            if not any(token in sub_s for token in target_tokens):
                continue
            if sub_s in seen_selectors:
                continue
            seen_selectors.add(sub_s)

            # Check if covered in light_map (direct or prefix/submatch)
            light_override = light_map.get(sub_s)
            if not light_override:
                # check submatches or parent selectors
                for l_sel, l_bg in light_map.items():
                    if sub_s in l_sel or l_sel in sub_s:
                        light_override = l_bg
                        break

            status = "PARITY_OK" if light_override else "MISSING_LIGHT_OVERRIDE"
            if not light_override:
                missing_count += 1

            audit_results.append({
                "selector": sub_s,
                "dark_bg": dark_val,
                "light_override": light_override or "MISSING",
                "status": status,
            })

    return audit_results, missing_count


def audit_backend_frontend_contracts() -> tuple[list[dict[str, Any]], int]:
    """Audits emitted backend snapshot keys against accessed keys in frontend JS."""
    portfolio_py = (REPO_ROOT / "backend" / "portfolio.py").read_text(encoding="utf-8")
    tree = ast.parse(portfolio_py)

    backend_company_keys: set[str] = set()
    backend_snapshot_keys: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "append" and isinstance(node.func.value, ast.Name) and node.func.value.id == "company_views":
                if node.args and isinstance(node.args[0], ast.Dict):
                    for k in node.args[0].keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            backend_company_keys.add(k.value)

        if isinstance(node, ast.FunctionDef) and node.name == "snapshot_from_session":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Dict):
                    for k in sub.value.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            backend_snapshot_keys.add(k.value)

    app_js = (REPO_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    tx_js = (REPO_ROOT / "frontend" / "tradexpress_ui.js").read_text(encoding="utf-8")
    full_js = app_js + "\n" + tx_js

    accessed_comp = set(re.findall(r'\b(?:company|c)\.([a-zA-Z0-9_]+)\b', full_js))
    accessed_snap = set(re.findall(r'\b(?:snapshot|snap|state\.snapshot)\.([a-zA-Z0-9_]+)\b', full_js))

    js_builtins = {
        "filter", "map", "length", "forEach", "slice", "reduce", "find", "some", "every",
        "includes", "push", "sort", "dataset", "style", "append", "classList", "replaceChildren",
        "addEventListener", "innerHTML", "innerText", "textContent", "hidden", "disabled",
        "value", "checked", "open", "close", "setAttribute", "getAttribute", "type", "title",
    }
    accessed_comp = {k for k in accessed_comp if k not in js_builtins}
    accessed_snap = {k for k in accessed_snap if k not in js_builtins}

    matrix: list[dict[str, Any]] = []
    mismatch_count = 0

    for k in sorted(accessed_comp):
        is_ok = k in backend_company_keys
        if not is_ok:
            mismatch_count += 1
        matrix.append({
            "scope": "Company View (`company.*` / `c.*`)",
            "field": k,
            "emitted_in_backend": is_ok,
            "status": "CONTRACT_VERIFIED" if is_ok else "FIELD_MISMATCH",
        })

    for k in sorted(accessed_snap):
        is_ok = k in backend_snapshot_keys
        if not is_ok:
            mismatch_count += 1
        matrix.append({
            "scope": "Root Snapshot (`snapshot.*` / `state.snapshot.*`)",
            "field": k,
            "emitted_in_backend": is_ok,
            "status": "CONTRACT_VERIFIED" if is_ok else "FIELD_MISMATCH",
        })

    return matrix, mismatch_count


def map_js_functions_and_endpoints() -> list[dict[str, Any]]:
    """Maps JS functions to DOM IDs and API endpoints across frontend JS."""
    files = [
        "frontend/app.js",
        "frontend/charts.js",
        "frontend/hermes_ui.js",
        "frontend/tradexpress_ui.js",
    ]
    results: list[dict[str, Any]] = []

    for fpath in files:
        full_path = REPO_ROOT / fpath
        if not full_path.exists():
            continue
        content = full_path.read_text(encoding="utf-8")

        # Find functions: function name(...) or const name = (...) =>
        func_matches = re.finditer(r'(?:function\s+([a-zA-Z0-9_]+)|(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)', content)
        for m in func_matches:
            fname = m.group(1) or m.group(2)
            # Find next block or ~100 lines for DOM IDs and API calls
            start_pos = m.start()
            end_pos = min(len(content), start_pos + 4000)
            chunk = content[start_pos:end_pos]

            dom_ids = set(re.findall(r'(?:\$\(["\']([a-zA-Z0-9_-]+)["\']\)|getElementById\(["\']([a-zA-Z0-9_-]+)["\']\)|querySelector\(["\']#([a-zA-Z0-9_-]+)["\']\))', chunk))
            flat_dom = sorted({item for sub in dom_ids for item in sub if item})

            endpoints = set(re.findall(r'["\'](/(?:api|k)/[a-zA-Z0-9_/-]+)["\']', chunk))

            if flat_dom or endpoints:
                results.append({
                    "file": fpath,
                    "function": fname,
                    "dom_ids": flat_dom[:6],
                    "endpoints": sorted(list(endpoints))[:4],
                })

    return results


def map_extension_sniffer() -> dict[str, Any]:
    """Extracts extension Manifest V3 configuration, DOM selectors, storage keys, and endpoints."""
    ext_dir = REPO_ROOT / "extension" / "tradexpress_mirror"
    manifest_file = ext_dir / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}

    content_js = (ext_dir / "content.js").read_text(encoding="utf-8") if (ext_dir / "content.js").exists() else ""
    bg_js = (ext_dir / "background.js").read_text(encoding="utf-8") if (ext_dir / "background.js").exists() else ""

    selectors = re.findall(r'querySelector(?:All)?\(["\']([#\.\[][a-zA-Z0-9_=:,\s\-\[\]\"\'\*\^~]+)["\']\)', content_js)
    cleaned_selectors = sorted({s.strip() for s in selectors if "#" in s or "[" in s})

    storage_keys = sorted(set(re.findall(r'storage\.local\.(?:get|set)\(\s*\{?["\']?([a-zA-Z0-9_]+)', content_js + bg_js)))
    endpoints = sorted(set(re.findall(r'https?://[a-zA-Z0-9\.:]+/[a-zA-Z0-9_/-]+', content_js + bg_js)))

    return {
        "manifest": {
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "manifest_version": manifest.get("manifest_version"),
            "permissions": manifest.get("permissions", []),
            "host_permissions": manifest.get("host_permissions", []),
        },
        "targeted_selectors": cleaned_selectors[:15],
        "storage_keys": storage_keys,
        "endpoints": endpoints,
    }


def generate_frontend_map():
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    css_audit, missing_css = audit_css_dark_light_parity()
    field_matrix, missing_fields = audit_backend_frontend_contracts()
    js_map = map_js_functions_and_endpoints()
    ext_map = map_extension_sniffer()

    md: list[str] = []
    md.append("# 🗺️ Humming Bird Trading Cockpit V1 — Frontend Architecture & Contract Map\n")
    md.append(f"> **Auto-Generated on:** `{now_utc}` via `scripts/generate_frontend_map.py`  \n"
              f"> **Zero-Regression Mandate:** 0 `MISSING_LIGHT_OVERRIDE` CSS issues, 0 Field Contract mismatches.\n")
    md.append("---\n")

    # Section 1: UI Layout & Component Hierarchy Tree
    md.append("## 1. UI Layout & Component Hierarchy Tree\n")
    md.append("```text\n"
              "index.html (.app-shell)\n"
              "├── main.workspace.tx-workspace\n"
              "│   ├── header.tx-top-header (#tx-top-header)\n"
              "│   │   ├── .tx-topbar-brand (Logo, Title, SHADOW_DUMMY badge)\n"
              "│   │   └── .tx-topbar-telemetry (Client A/C, Buying Power, Gain/Loss, DSEX, Clock, RunMode, Automation)\n"
              "│   ├── nav.tx-main-nav (#tx-main-nav)\n"
              "│   │   ├── Tab: Trade Workstation (#tx-nav-trade -> #view-dashboard)\n"
              "│   │   ├── Tab: Market Map (#tx-nav-heatmap -> #view-heatmap-wrap)\n"
              "│   │   ├── Tab: Strategy Rules (#tx-nav-rules -> #view-rules-wrap)\n"
              "│   │   ├── Tab: T+2 Ledger (#tx-nav-ledger -> #view-ledger-wrap)\n"
              "│   │   ├── Tab: Learning Logs (#tx-nav-learning -> #tx-learning-view)\n"
              "│   │   └── Tab: Settings (#tx-nav-settings -> #view-settings)\n"
              "│   └── section#view-dashboard (#tx-trade-workspace)\n"
              "│       ├── top-pane: #tx-market-watch (~54% height)\n"
              "│       │   ├── header: .tx-mw-header (Category Tabs: My Favorites, GSC, L1, L2, All DSE; Search Box)\n"
              "│       │   └── table.tx-mw-table (#watchlist-thead, #watchlist-body: 13 NetPlus Columns)\n"
              "│       └── bottom-split: .tx-bottom-split (~46% height)\n"
              "│           ├── bottom-left: #tx-order-ticket (New Order Ticket, Steppers, 5-Level Depth, Submit Button)\n"
              "│           └── bottom-right: #tx-monitor-panel (Sub-tabs: Holdings, Orders, Account Summary [Donut + Mirror Card])\n"
              "├── aside#hermes-sidebar (Hermes AI Co-pilot Dock, 300..440px Resizable)\n"
              "│   ├── nav#hermes-tabs (Chat, Conversations, Changes, Skills)\n"
              "│   └── panes (#pane-hermes-chat, #pane-hermes-conversations, #pane-hermes-changes, #pane-hermes-skills)\n"
              "└── modals\n"
              "    ├── dialog#tx-confirm-order-modal (2-Step Execution Confirmation Modal)\n"
              "    ├── dialog#tx-cdp-setup-modal (1-Click Safe Browser Launcher)\n"
              "    └── dialog#deep-trend-modal (400-Candle Historical Chart)\n"
              "```\n")
    md.append("---\n")

    # Section 2: Dark vs Light Mode CSS Parity Audit Table
    md.append("## 2. Dark vs Light Mode CSS Parity Audit Table\n")
    md.append(f"Audit of `.tx-*`, `#tx-*`, and critical ticket/search elements in `styles.css` vs `theme_light_hermes.css`:\n\n"
              f"> **Status:** `{missing_css}` Missing Light Overrides.\n\n")
    md.append("| Selector | Dark Background in `styles.css` | Light Override in `theme_light_hermes.css` | Audit Status |")
    md.append("| :--- | :--- | :--- | :--- |")
    for row in css_audit:
        badge = "✅ PARITY_OK" if row["status"] == "PARITY_OK" else "❌ MISSING_LIGHT_OVERRIDE"
        md.append(f"| `{row['selector']}` | `{row['dark_bg']}` | `{row['light_override']}` | {badge} |")
    md.append("\n---\n")

    # Section 3: Backend Snapshot ↔ Frontend Field Contract Matrix
    md.append("## 3. Backend Snapshot ↔ Frontend Field Contract Matrix\n")
    md.append(f"Verification of data contracts between `backend/portfolio.py` and frontend JS (`app.js`, `tradexpress_ui.js`):\n\n"
              f"> **Status:** `{missing_fields}` Field Contract Mismatches.\n\n")
    md.append("| Scope | Field / Property Name | Emitted by Backend | Contract Status |")
    md.append("| :--- | :--- | :--- | :--- |")
    for row in field_matrix:
        badge = "✅ CONTRACT_VERIFIED" if row["status"] == "CONTRACT_VERIFIED" else "❌ FIELD_MISMATCH"
        md.append(f"| {row['scope']} | `{row['field']}` | {'Yes' if row['emitted_in_backend'] else 'No'} | {badge} |")
    md.append("\n---\n")

    # Section 4: JS Function → DOM IDs & API Endpoints Map
    md.append("## 4. JS Function → DOM IDs & API Endpoints Map\n")
    md.append("Mapping of client functions to active DOM elements and localhost API endpoints:\n\n")
    md.append("| File | Function Name | Referenced DOM IDs | API Endpoints Invoked |")
    md.append("| :--- | :--- | :--- | :--- |")
    for item in js_map[:30]:
        dom_str = ", ".join(f"`#{d}`" for d in item["dom_ids"]) if item["dom_ids"] else "—"
        ep_str = ", ".join(f"`{e}`" for e in item["endpoints"]) if item["endpoints"] else "—"
        md.append(f"| `{item['file']}` | `{item['function']}` | {dom_str} | {ep_str} |")
    md.append("\n---\n")

    # Section 5: Edge Extension Passive Sniffer Map
    md.append("## 5. Edge Extension Passive Sniffer Map (`extension/tradexpress_mirror/`)\n")
    md.append(f"- **Extension Name:** `{ext_map['manifest'].get('name')}` (v`{ext_map['manifest'].get('version')}`)\n"
              f"- **Target Origin:** `https://itrade.lbsbd.com/*` (100% read-only content script)\n"
              f"- **Host Permissions:** `{', '.join(ext_map['manifest'].get('host_permissions', []))}`\n\n"
              f"### 5.1 Targeted Broker DOM Selectors\n")
    for s in ext_map["targeted_selectors"]:
        md.append(f"- `{s}`")
    md.append(f"\n### 5.2 Storage Keys\n")
    for k in ext_map["storage_keys"]:
        md.append(f"- `{k}`")
    md.append(f"\n### 5.3 Localhost Endpoints Forwarded\n")
    for ep in ext_map["endpoints"]:
        md.append(f"- `{ep}`")
    md.append("\n")

    OUTPUT_FILE.write_text("\n".join(md), encoding="utf-8")
    print(f"Generated {OUTPUT_FILE} ({missing_css} missing light overrides, {missing_fields} field mismatches).")
    return missing_css, missing_fields


if __name__ == "__main__":
    generate_frontend_map()
