#!/usr/bin/env python3
"""Standard-Library AST X-Ray & Codebase Architecture Mapper.

Zero external dependencies: uses only Python stdlib (ast, inspect, re, pathlib).
Scans the repository and produces `documentation/CODEBASE_MAP.md`.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "documentation" / "CODEBASE_MAP.md"

IGNORE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".idea", ".vscode", "data", "browser_profile", "dist", "build", "node_modules"
}


def is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS or part.startswith("."):
            if part not in {".agentignore", ".cursorignore", ".opencodeignore"}:
                return True
    return False


def collect_file_metrics():
    stats = defaultdict(lambda: {"count": 0, "lines": 0})
    file_list = []
    for p in sorted(REPO_ROOT.rglob("*")):
        if p.is_file() and not is_ignored(p):
            rel = p.relative_to(REPO_ROOT)
            ext = p.suffix.lower() or p.name
            try:
                line_count = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
            except Exception:
                line_count = 0
            stats[ext]["count"] += 1
            stats[ext]["lines"] += line_count
            file_list.append((rel, line_count))
    return stats, file_list


class AstVisitor(ast.NodeVisitor):
    def __init__(self, filepath: Path, code_lines: list[str]):
        self.filepath = filepath
        self.code_lines = code_lines
        self.classes: list[dict[str, Any]] = []
        self.functions: list[dict[str, Any]] = []
        self.imports: list[str] = []
        self.current_class: dict[str, Any] | None = None
        self.current_func: dict[str, Any] | None = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}" if mod else alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        doc = ast.get_docstring(node) or ""
        end_line = getattr(node, "end_lineno", node.lineno)
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": end_line,
            "doc": doc.strip().split("\n")[0] if doc else "",
            "methods": [],
            "bases": [ast.unparse(b) for b in node.bases],
        }
        self.classes.append(class_info)
        self.current_class = class_info
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_func(node, is_async=True)

    def _record_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool = False):
        prev_func = self.current_func
        doc = ast.get_docstring(node) or ""
        end_line = getattr(node, "end_lineno", node.lineno)
        args_str = ast.unparse(node.args) if hasattr(ast, "unparse") else "..."
        returns_str = ast.unparse(node.returns) if node.returns and hasattr(ast, "unparse") else None

        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": end_line,
            "length": end_line - node.lineno + 1,
            "is_async": is_async,
            "args": args_str,
            "returns": returns_str,
            "doc": doc.strip().split("\n")[0] if doc else "",
            "calls": set(),
            "max_depth": self._compute_depth(node),
        }

        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.functions.append(func_info)

        self.current_func = func_info
        self.generic_visit(node)
        self.current_func = prev_func

    def visit_Call(self, node: ast.Call):
        if self.current_func:
            call_name = None
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            if call_name:
                self.current_func["calls"].add(call_name)
        self.generic_visit(node)

    def _compute_depth(self, node: ast.AST, current_depth: int = 1) -> int:
        max_d = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Match)):
                sub_d = self._compute_depth(child, current_depth + 1)
                if sub_d > max_d:
                    max_d = sub_d
            else:
                sub_d = self._compute_depth(child, current_depth)
                if sub_d > max_d:
                    max_d = sub_d
        return max_d


def parse_python_files():
    parsed = {}
    py_files = sorted(list((REPO_ROOT / "backend").rglob("*.py")) + list((REPO_ROOT / "scripts").rglob("*.py")))
    for pf in py_files:
        if is_ignored(pf):
            continue
        rel = pf.relative_to(REPO_ROOT).as_posix()
        try:
            content = pf.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(pf))
            lines = content.splitlines()
            visitor = AstVisitor(pf, lines)
            visitor.visit(tree)
            parsed[rel] = visitor
        except Exception as e:
            print(f"Skipping {rel}: {e}")
    return parsed


def parse_fastapi_routes(main_path: Path):
    routes = []
    if not main_path.exists():
        return routes
    try:
        content = main_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(main_path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                        method = deco.func.attr.upper()
                        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"} and deco.args:
                            path = ast.literal_eval(deco.args[0]) if isinstance(deco.args[0], ast.Constant) else "?"
                            doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
                            routes.append({
                                "method": method,
                                "path": path,
                                "func_name": node.name,
                                "lineno": node.lineno,
                                "doc": doc or "Route endpoint",
                            })
    except Exception as exc:
        print(f"Error parsing FastAPI routes: {exc}")
    return routes


def parse_frontend():
    html_ids = []
    html_path = REPO_ROOT / "frontend" / "index.html"
    if html_path.exists():
        html_text = html_path.read_text(encoding="utf-8")
        html_ids = re.findall(r'id=["\']([^"\']+)["\']', html_text)

    js_endpoints = []
    js_funcs = []
    js_path = REPO_ROOT / "frontend" / "app.js"
    if js_path.exists():
        js_text = js_path.read_text(encoding="utf-8")
        js_endpoints = sorted(list(set(re.findall(r'api\(\s*["\']([^"\']+)["\']', js_text))))
        lines = js_text.splitlines()
        for idx, line in enumerate(lines, 1):
            m = re.match(r'^(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(', line.strip())
            if m:
                js_funcs.append((m.group(1), idx))
    return sorted(list(set(html_ids))), js_endpoints, js_funcs


def generate_markdown():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metrics, file_list = collect_file_metrics()
    parsed_py = parse_python_files()
    routes = parse_fastapi_routes(REPO_ROOT / "backend" / "main.py")
    html_ids, js_endpoints, js_funcs = parse_frontend()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    md = []
    md.append("# 🗺️ Codebase AST Map & System Architecture Radar\n")
    md.append(f"> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **{now_iso}**.\n")
    md.append("---\n")

    # Section 1
    md.append("## 1. Repository Topology & File Metrics\n")
    md.append("| Extension / Type | File Count | Total Lines of Code | Description |")
    md.append("| :--- | :--- | :--- | :--- |")
    desc_map = {
        ".py": "Python Core Kernel, Engine & Hermes Agent",
        ".js": "Vanilla ES6+ Reactive Terminal Controller",
        ".html": "Single Page Application DOM Structure",
        ".css": "Custom Dark / Light / Terminal Design System",
        ".md": "Architecture & Strategy Documentation",
        ".txt": "Dependency Specifications",
        ".toml": "PyProject Configuration",
        ".example": "Environment Configuration Template",
    }
    total_files = sum(m["count"] for m in metrics.values())
    total_lines = sum(m["lines"] for m in metrics.values())
    for ext, stat in sorted(metrics.items(), key=lambda x: -x[1]["lines"]):
        desc = desc_map.get(ext, "Configuration / Asset")
        md.append(f"| `{ext}` | {stat['count']} | {stat['lines']:,} | {desc} |")
    md.append(f"| **TOTAL** | **{total_files}** | **{total_lines:,}** | *Entire Humming Bird Repository* |\n")

    # Section 2
    md.append("## 2. Internal Dependency & Import Graph\n")
    md.append("Shows intra-repo module dependencies within `backend/` and `scripts/`:\n")
    md.append("| Module File | Imported Internal Dependencies |")
    md.append("| :--- | :--- |")
    for mod_path, visitor in parsed_py.items():
        internal_deps = sorted(list(set(
            imp for imp in visitor.imports
            if imp.startswith("backend") or imp.startswith("scripts")
        )))
        dep_str = ", ".join(f"`{d}`" for d in internal_deps) if internal_deps else "*Independent Core Module*"
        md.append(f"| [`{mod_path}`](/{mod_path}) | {dep_str} |")
    md.append("\n---\n")

    # Section 3
    md.append("## 3. Python AST X-Ray & Class/Function Registry\n")
    for mod_path, visitor in parsed_py.items():
        md.append(f"### 📄 [`{mod_path}`](/{mod_path})\n")

        if visitor.classes:
            md.append("#### Classes & Methods\n")
            md.append("| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for c in visitor.classes:
                bases = ", ".join(c["bases"]) if c["bases"] else "object"
                doc = c["doc"] or "—"
                md.append(f"| `{c['name']}` | `L{c['lineno']}–L{c['end_lineno']}` | `{bases}` | {doc} | {len(c['methods'])} |")
            md.append("\n")

            for c in visitor.classes:
                if c["methods"]:
                    md.append(f"**Methods in `{c['name']}`:**\n")
                    md.append("| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |")
                    md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                    for m in c["methods"]:
                        calls = ", ".join(f"`{k}`" for k in sorted(list(m["calls"]))[:4]) or "—"
                        ret = f"`{m['returns']}`" if m["returns"] else "—"
                        md.append(f"| `{m['name']}` | `L{m['lineno']}–L{m['end_lineno']}` | `({m['args'][:35]}...)` | {ret} | {m['doc'] or '—'} | {calls} |")
                    md.append("\n")

        if visitor.functions:
            md.append("#### Standalone Functions\n")
            md.append("| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for f in visitor.functions:
                calls = ", ".join(f"`{k}`" for k in sorted(list(f["calls"]))[:4]) or "—"
                ret = f"`{f['returns']}`" if f["returns"] else "—"
                md.append(f"| `{f['name']}` | `L{f['lineno']}–L{f['end_lineno']}` | `({f['args'][:35]}...)` | {ret} | {f['doc'] or '—'} | {calls} |")
            md.append("\n")
        md.append("---\n")

    # Section 4
    md.append("## 4. Database Schema X-Ray (`backend/database.py`)\n")
    md.append("SQLAlchemy ORM Entities backing the deterministic ledger and Hermes state store:\n")
    db_visitor = parsed_py.get("backend/database.py")
    if db_visitor:
        md.append("| Model Entity | Line Range | Base | Purpose & Managed Ledger State |")
        md.append("| :--- | :--- | :--- | :--- |")
        for c in db_visitor.classes:
            if "Base" in c["bases"]:
                md.append(f"| `{c['name']}` | `L{c['lineno']}–L{c['end_lineno']}` | `Base` | {c['doc'] or 'Durable transactional entity'} |")
    md.append("\n---\n")

    # Section 5
    md.append("## 5. FastAPI Route Registry (`backend/main.py`)\n")
    md.append("| Method | Route Path | Handler Function | Line | Description |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    for r in routes:
        md.append(f"| `{r['method']}` | `{r['path']}` | `{r['func_name']}` | `L{r['lineno']}` | {r['doc']} |")
    md.append("\n---\n")

    # Section 6
    md.append("## 6. Frontend DOM & JS Controller X-Ray\n")
    md.append("### Key DOM Identifiers (`frontend/index.html`)\n")
    md.append(f"Identified **{len(html_ids)}** distinct element IDs in the UI shell. Key controller anchors:\n")
    key_ids = [
        "overview", "watchlist", "market-map", "automation-control-bar",
        "master-automation-toggle", "mode-btn-polling", "mode-btn-live",
        "polling-interval-pills", "adapter-status-badge", "main-chart",
        "bucket-stack", "what-if-slider", "theme-toggle-btn", "topbar-clock-widget"
    ]
    md.append(", ".join(f"`#{i}`" for i in key_ids if i in html_ids) + "\n\n")

    md.append("### Frontend API Contract Invocations (`frontend/app.js`)\n")
    md.append("| Endpoint Invocated | Direction | Purpose |")
    md.append("| :--- | :--- | :--- |")
    for ep in js_endpoints:
        md.append(f"| `{ep}` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |")
    md.append("\n")

    md.append("### Core JavaScript Controllers (`frontend/app.js`)\n")
    md.append("| Function | Line in `app.js` | Role |")
    md.append("| :--- | :--- | :--- |")
    for fn, line in js_funcs[:25]:
        md.append(f"| `{fn}()` | `L{line}` | Reactive DOM rendering / event controller |")
    md.append("\n---\n")

    # Section 7
    md.append("## 7. Code Health & Complexity Radar\n")
    md.append("Functions requiring architectural attention (> 70 lines or nesting depth >= 4):\n\n")
    md.append("| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    attention_count = 0
    for mod_path, visitor in parsed_py.items():
        all_funcs = visitor.functions + [m for c in visitor.classes for m in c["methods"]]
        for f in all_funcs:
            if f["length"] > 70 or f["max_depth"] >= 4:
                attention_count += 1
                rec = "Decompose into sub-functions" if f["length"] > 100 else "Acceptable; well-scoped logic"
                md.append(f"| `{mod_path}` | `{f['name']}` | {f['length']} | {f['max_depth']} | {rec} |")

    if attention_count == 0:
        md.append("| *All functions are under 70 lines and well-factored.* | | | | |")
    md.append("\n")
    md.append(f"> **Audit Summary:** {len(parsed_py)} Python modules inspected, {len(routes)} FastAPI endpoints registered, {total_lines:,} total LOC indexed.")

    OUTPUT_FILE.write_text("\n".join(md), encoding="utf-8")
    print(f"Generated {OUTPUT_FILE} ({len(md)} sections, {total_lines:,} LOC mapped).")


if __name__ == "__main__":
    generate_markdown()
