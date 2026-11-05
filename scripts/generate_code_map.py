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


def parse_fastapi_routes(router_paths: list[Path]):
    all_routes = []
    for p in router_paths:
        if not p.exists():
            continue
        try:
            content = p.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(p))
            file_prefix = ""
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and "router" in target.id:
                            if isinstance(node.value, ast.Call):
                                for kw in node.value.keywords:
                                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                        file_prefix = kw.value.value

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for deco in node.decorator_list:
                        if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                            method = deco.func.attr.upper()
                            if method in {"GET", "POST", "PUT", "PATCH", "DELETE"} and deco.args:
                                raw_path = ast.literal_eval(deco.args[0]) if isinstance(deco.args[0], ast.Constant) else "?"
                                full_path = f"{file_prefix}{raw_path}" if file_prefix and not raw_path.startswith(file_prefix) else raw_path
                                doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
                                all_routes.append({
                                    "file": p.relative_to(REPO_ROOT).as_posix(),
                                    "method": method,
                                    "path": full_path,
                                    "func_name": node.name,
                                    "lineno": node.lineno,
                                    "doc": doc or "Route endpoint",
                                })
        except Exception as exc:
            print(f"Error parsing FastAPI routes in {p}: {exc}")
    return all_routes


def parse_css_design(styles_file: Path, light_file: Path):
    styles_text = styles_file.read_text(encoding="utf-8") if styles_file.exists() else ""
    light_text = light_file.read_text(encoding="utf-8") if light_file.exists() else ""

    dark_vars = {}
    root_match = re.search(r':root[^{]*\{([^}]+)\}', styles_text)
    if root_match:
        for line in root_match.group(1).splitlines():
            line = line.strip()
            if line.startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    dark_vars[parts[0].strip()] = parts[1].rstrip(";").strip()

    light_vars = {}
    light_match = re.search(r'\[data-theme=["\']?light["\']?\]\s*\{([^}]+)\}', light_text)
    if light_match:
        for line in light_match.group(1).splitlines():
            line = line.strip()
            if line.startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    light_vars[parts[0].strip()] = parts[1].rstrip(";").strip()

    all_keys = sorted(list(set(dark_vars.keys()) | set(light_vars.keys())))
    token_rows = []
    for k in all_keys:
        d_val = dark_vars.get(k, "—")
        l_val = light_vars.get(k, "—")
        category = "Color"
        if "radius" in k: category = "Shape / Radius"
        elif "bg" in k or "panel" in k: category = "Surface / Background"
        elif "line" in k or "border" in k or "grid" in k: category = "Border / Divider"
        elif "glow" in k: category = "Glow / Shadow"
        elif "text" in k or "muted" in k or "dim" in k: category = "Typography"
        token_rows.append({"token": k, "dark": d_val, "light": l_val, "category": category})

    key_selectors = [
        ".app-shell", ".topbar", ".topbar-right", ".workspace", ".assistant",
        "#hermes-resizer", ".card", ".metric-card", ".table-wrap",
        ".model-dropup-menu", ".diff-card", ".nav-rail", ".session-bar",
        ".engine-controls", ".modal", ".market-map-grid", ".chat-messages",
        ".skills-drawer"
    ]
    target_props = ["display", "grid-template-columns", "position", "background", "background-color", "color", "flex-wrap"]

    component_rows = []

    def scan_file(css_text: str, filename: str):
        lines = css_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            for sel in key_selectors:
                if re.search(rf'(?:^|[\s,>+~]){re.escape(sel)}(?:[\s,{{>]|$)', line):
                    if ":" in line and not any(p in line for p in [":root", "[data-theme"]):
                        continue
                    line_no = i + 1
                    body_lines = []
                    brace_depth = 0
                    started = False
                    j = i
                    while j < len(lines):
                        l = lines[j]
                        for char in l:
                            if char == '{':
                                brace_depth += 1
                                started = True
                            elif char == '}':
                                brace_depth -= 1
                        if started:
                            body_lines.append(l)
                        if started and brace_depth <= 0:
                            break
                        j += 1
                    body_text = "\n".join(body_lines)
                    props = {}
                    for prop in target_props:
                        pm = re.search(rf'(?:^|[;\s{{]){prop}\s*:\s*([^;}}]+)', body_text)
                        if pm:
                            props[prop] = pm.group(1).strip()

                    bg = props.get("background") or props.get("background-color") or "—"
                    if len(bg) > 42:
                        bg = bg[:39] + "..."
                    component_rows.append({
                        "selector": sel,
                        "file": filename,
                        "line": line_no,
                        "display": props.get("display", "—"),
                        "grid_cols": props.get("grid-template-columns", "—"),
                        "position": props.get("position", "—"),
                        "background": bg,
                        "color": props.get("color", "—"),
                        "flex_wrap": props.get("flex-wrap", "—"),
                    })
                    break
            i += 1

    scan_file(styles_text, "frontend/styles.css")
    scan_file(light_text, "frontend/theme_light_hermes.css")

    return token_rows, component_rows


def parse_frontend():
    html_ids = []
    html_path = REPO_ROOT / "frontend" / "index.html"
    if html_path.exists():
        html_text = html_path.read_text(encoding="utf-8")
        html_ids = re.findall(r'id=["\']([^"\']+)["\']', html_text)

    js_endpoints = set()
    js_funcs = []
    frontend_dir = REPO_ROOT / "frontend"
    for js_file in sorted(frontend_dir.glob("*.js")):
        js_text = js_file.read_text(encoding="utf-8")
        for ep in re.findall(r'api\(\s*["\']([^"\']+)["\']', js_text):
            js_endpoints.add(ep)
        lines = js_text.splitlines()
        for idx, line in enumerate(lines, 1):
            m = re.match(r'^(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(', line.strip())
            if m:
                js_funcs.append((m.group(1), js_file.name, idx))

    css_files = []
    for css_file in sorted(frontend_dir.glob("*.css")):
        line_count = len(css_file.read_text(encoding="utf-8").splitlines())
        css_files.append((css_file.name, line_count))

    return sorted(list(set(html_ids))), sorted(list(js_endpoints)), js_funcs, css_files


def generate_markdown():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metrics, file_list = collect_file_metrics()
    parsed_py = parse_python_files()
    routes = parse_fastapi_routes([
        REPO_ROOT / "backend" / "main.py",
        REPO_ROOT / "backend" / "routes_hermes.py",
        REPO_ROOT / "backend" / "routes_auth_settings.py",
        REPO_ROOT / "backend" / "routes_stocknow.py",
    ])
    html_ids, js_endpoints, js_funcs, css_files = parse_frontend()
    css_tokens, css_components = parse_css_design(
        REPO_ROOT / "frontend" / "styles.css",
        REPO_ROOT / "frontend" / "theme_light_hermes.css",
    )

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
    md.append("## 5. FastAPI Route Registry (All Sub-Routers & Endpoints)\n")
    md.append("| Method | Route Path | Module File | Line | Handler Function | Description |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in routes:
        md.append(f"| `{r['method']}` | `{r['path']}` | [`{r['file']}`](/{r['file']}#L{r['lineno']}) | `L{r['lineno']}` | `{r['func_name']}()` | {r['doc']} |")
    md.append("\n---\n")

    # Section 6
    md.append("## 6. Frontend DOM, JS Controller & CSS Design X-Ray\n")
    md.append("### Theme Color & Layout Tokens Table (`:root` Dark vs Light Mode)\n")
    md.append("| CSS Custom Property | Category | Dark Mode (`:root`) | Light Mode (`[data-theme=\"light\"]`) |")
    md.append("| :--- | :--- | :--- | :--- |")
    for t in css_tokens:
        md.append(f"| `{t['token']}` | {t['category']} | `{t['dark']}` | `{t['light']}` |")
    md.append("\n")

    md.append("### Component CSS Selector Map\n")
    md.append("| Component Selector | Stylesheet File | Line | Display | Grid / Layout | Position | Background / Color | Flex Wrap |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for c in css_components:
        grid_desc = f"`{c['grid_cols']}`" if c['grid_cols'] != "—" else "—"
        pos_desc = f"`{c['position']}`" if c['position'] != "—" else "—"
        disp_desc = f"`{c['display']}`" if c['display'] != "—" else "—"
        wrap_desc = f"`{c['flex_wrap']}`" if c['flex_wrap'] != "—" else "—"
        bg_desc = f"`{c['background']}`" if c['background'] != "—" else "—"
        md.append(f"| `{c['selector']}` | [`{c['file']}`](/{c['file']}#L{c['line']}) | `L{c['line']}` | {disp_desc} | {grid_desc} | {pos_desc} | {bg_desc} | {wrap_desc} |")
    md.append("\n")

    md.append("### Key DOM Identifiers (`frontend/index.html`)\n")
    md.append(f"Identified **{len(html_ids)}** distinct element IDs in the UI shell. Key controller anchors:\n")
    key_ids = [
        "overview", "watchlist", "market-map", "automation-control-bar",
        "master-automation-toggle", "mode-btn-polling", "mode-btn-live",
        "polling-interval-pills", "adapter-status-badge", "main-chart",
        "bucket-stack", "what-if-slider", "theme-toggle-btn", "topbar-clock-widget"
    ]
    md.append(", ".join(f"`#{i}`" for i in key_ids if i in html_ids) + "\n\n")

    md.append("### Frontend Stylesheets (`frontend/*.css`)\n")
    md.append("| Stylesheet File | Lines | Purpose |")
    md.append("| :--- | :--- | :--- |")
    for css_name, count in css_files:
        desc = "Daylight overrides & Hermes IDE sidebar" if "light" in css_name or "hermes" in css_name else "Core design tokens, layout & widgets"
        md.append(f"| `{css_name}` | {count} | {desc} |")
    md.append("\n")

    md.append("### Frontend API Contract Invocations (`frontend/*.js`)\n")
    md.append("| Endpoint Invocated | Direction | Purpose |")
    md.append("| :--- | :--- | :--- |")
    for ep in js_endpoints:
        md.append(f"| `{ep}` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |")
    md.append("\n")

    md.append("### Core JavaScript Controllers (`frontend/*.js`)\n")
    md.append("| Function | Module File | Line | Role |")
    md.append("| :--- | :--- | :--- | :--- |")
    for fn, mod, line in js_funcs:
        md.append(f"| `{fn}()` | `{mod}` | `L{line}` | Reactive DOM rendering / event controller |")
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

