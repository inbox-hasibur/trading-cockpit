#!/usr/bin/env python3
"""Standard-Library AST X-Ray & Codebase Architecture Mapper.

Zero external dependencies: uses only Python stdlib (ast, inspect, os, pathlib, re, subprocess).
Scans the repository and produces `documentation/CODEBASE_MAP.md`.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "documentation" / "CODEBASE_MAP.md"

EXCLUDED_DIR_NAMES = {
    "vendor",
    "node_modules",
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "scratch",
}

EXCLUDED_PREFIXES = (
    "vendor/",
    "node_modules/",
    ".venv/",
    "venv/",
    ".git/",
    "backend/data/",
    ".pytest_cache/",
    "dist/",
    "build/",
    "scratch/",
)

MAJOR_EXTENSIONS = {
    ".py",
    ".json",
    ".md",
    ".js",
    ".css",
    ".txt",
    ".ps1",
    ".html",
    ".yaml",
    ".toml",
    ".sh",
    ".bat",
}

EXTENSION_DESCRIPTIONS = {
    ".py": "Python Core Kernel, Engine, Tests & Plugins",
    ".js": "Vanilla ES6+ Reactive Terminal Controller & UI",
    ".html": "Single Page Application DOM Structure",
    ".css": "Custom Dark / Light / Terminal Design System",
    ".md": "Architecture & Strategy Documentation",
    ".json": "Fixtures & Configuration",
    ".yaml": "Manifest & Plugin Configuration",
    ".toml": "PyProject Configuration",
    ".txt": "Dependency Specifications",
    ".ps1": "Windows PowerShell Automation",
    ".sh": "Shell Scripts",
    ".bat": "Batch Launchers",
    "other": "Other Configuration, Assets & Dotfiles",
}


def is_excluded(path: Path | str, repo_root: Path = REPO_ROOT) -> bool:
    """Check if a path should be excluded based on directory rules.

    Excludes: vendor/, node_modules/, .venv/, venv/, .git/, __pycache__/,
              backend/data/, .pytest_cache/, dist/, build/, scratch/.
    """
    p = Path(path)
    if not p.is_absolute():
        rel = p
    else:
        try:
            rel = p.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return True

    rel_posix = rel.as_posix()

    # 1. Direct prefix or exact matches
    for prefix in EXCLUDED_PREFIXES:
        clean_prefix = prefix.rstrip("/")
        if rel_posix == clean_prefix or rel_posix.startswith(prefix):
            return True

    # 2. Check directory segments in the relative path
    parts = rel.parts
    for part in parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return True

    if len(parts) > 0 and parts[0] in EXCLUDED_DIR_NAMES:
        return True

    return False


def get_pinned_vendor_commit(repo_root: Path = REPO_ROOT) -> str:
    """Retrieve pinned submodule commit for vendor/hermes-agent from git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", ":vendor/hermes-agent"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        sha = proc.stdout.strip()
        if sha and len(sha) == 40:
            return sha
    except Exception:
        pass

    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root / "vendor" / "hermes-agent"), "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        sha = proc.stdout.strip()
        if sha and len(sha) == 40:
            return sha
    except Exception:
        pass

    return "b777adb7918713e5786cc9d95ad5b854074f2cb6"


def discover_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Discover files using git ls-files + untracked non-ignored files,
    falling back to os.walk with explicit directory excludes.
    """
    discovered: list[Path] = []
    git_worked = False

    try:
        cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        for line in proc.stdout.splitlines():
            item = line.strip()
            if not item:
                continue
            abs_p = (repo_root / item).resolve()
            if abs_p.is_file() and not is_excluded(abs_p, repo_root):
                discovered.append(abs_p)
        git_worked = True
    except Exception:
        git_worked = False

    if not git_worked:
        for root, dirs, files in os.walk(str(repo_root)):
            root_p = Path(root)
            dirs[:] = [d for d in dirs if not is_excluded(root_p / d, repo_root)]
            for f in files:
                abs_p = (root_p / f).resolve()
                if abs_p.is_file() and not is_excluded(abs_p, repo_root):
                    discovered.append(abs_p)

    return sorted(list(set(discovered)))


def collect_file_metrics(discovered_files: list[Path], repo_root: Path = REPO_ROOT):
    """Collect file counts and LOC grouped by extension, grouping long-tail as 'other'."""
    stats = defaultdict(lambda: {"count": 0, "lines": 0})
    file_list = []

    for p in discovered_files:
        if not p.is_file():
            continue
        rel = p.relative_to(repo_root)
        raw_suffix = p.suffix.lower()

        # Extensions from pathlib suffix of real files only; long tail grouped as "other"
        if not raw_suffix or raw_suffix not in MAJOR_EXTENSIONS:
            ext_key = "other"
        else:
            ext_key = raw_suffix

        try:
            line_count = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            line_count = 0

        stats[ext_key]["count"] += 1
        stats[ext_key]["lines"] += line_count
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


def parse_python_files(discovered_files: list[Path], repo_root: Path = REPO_ROOT) -> dict[str, AstVisitor]:
    """Parse all discovered Python files in backend/, plugins/, scripts/ using AST."""
    parsed = {}
    for pf in discovered_files:
        if pf.suffix.lower() != ".py":
            continue
        rel = pf.relative_to(repo_root).as_posix()
        if not (rel.startswith("backend/") or rel.startswith("plugins/") or rel.startswith("scripts/")):
            continue
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


def parse_fastapi_routes(router_paths: list[Path], repo_root: Path = REPO_ROOT):
    """Parse route handlers from FastAPI router modules."""
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
                                    "file": p.relative_to(repo_root).as_posix(),
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
        if "radius" in k:
            category = "Shape / Radius"
        elif "bg" in k or "panel" in k:
            category = "Surface / Background"
        elif "line" in k or "border" in k or "grid" in k:
            category = "Border / Divider"
        elif "glow" in k:
            category = "Glow / Shadow"
        elif "text" in k or "muted" in k or "dim" in k:
            category = "Typography"
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


def parse_frontend(repo_root: Path = REPO_ROOT):
    """Index frontend HTML IDs, JS functions, API invocations, and CSS stylesheets."""
    # 1. Parse HTML IDs from frontend/index.html
    html_ids: list[dict[str, Any]] = []
    html_path = repo_root / "frontend" / "index.html"
    if html_path.exists():
        html_text = html_path.read_text(encoding="utf-8")
        lines = html_text.splitlines()
        seen = set()
        for idx, line in enumerate(lines, 1):
            for m in re.finditer(r'<([a-zA-Z0-9\-]+)[^>]*\bid=[\x22\x27]([^\x22\x27]+)[\x22\x27]', line):
                tag = m.group(1)
                el_id = m.group(2)
                if (el_id, idx) not in seen:
                    seen.add((el_id, idx))
                    html_ids.append({"id": el_id, "tag": tag, "line": idx})
            for m in re.finditer(r'\bid=[\x22\x27]([^\x22\x27]+)[\x22\x27]', line):
                el_id = m.group(1)
                if not any(x["id"] == el_id and x["line"] == idx for x in html_ids):
                    seen.add((el_id, idx))
                    html_ids.append({"id": el_id, "tag": "element", "line": idx})

    # 2. Parse functions in frontend/app.js, charts.js, hermes_ui.js
    pattern_func = re.compile(r'^(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)')
    pattern_arrow = re.compile(r'^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:\(([^)]*)\)|([a-zA-Z0-9_$]+))\s*=>')
    pattern_expr = re.compile(r'^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\)')

    target_js_files = ["app.js", "charts.js", "hermes_ui.js"]
    js_funcs: list[dict[str, Any]] = []
    js_endpoints = set()

    for js_name in target_js_files:
        js_file = repo_root / "frontend" / js_name
        if not js_file.exists():
            continue
        js_text = js_file.read_text(encoding="utf-8")
        for ep in re.findall(r'api\(\s*["\']([^"\']+)["\']', js_text):
            js_endpoints.add(ep)
        lines = js_text.splitlines()
        for idx, line in enumerate(lines, 1):
            sline = line.strip()
            name_match = None
            args_str = ""

            m = pattern_func.match(sline)
            if m:
                name_match = m.group(1)
                args_str = m.group(2)
            else:
                m = pattern_arrow.match(sline)
                if m:
                    name_match = m.group(1)
                    args_str = m.group(2) or m.group(3) or ""
                else:
                    m = pattern_expr.match(sline)
                    if m:
                        name_match = m.group(1)
                        args_str = m.group(2)

            if name_match:
                role = "UI Controller"
                low = name_match.lower()
                if "render" in low:
                    role = "DOM Renderer"
                elif "format" in low:
                    role = "Formatter / Utility"
                elif "api" in low or "fetch" in low or "load" in low:
                    role = "API Client / Ingestion"
                elif "chart" in low or "curve" in low or "sparkline" in low or "treemap" in low or "bezier" in low or "squarify" in low:
                    role = "Canvas / Chart Geometry"
                elif "chat" in low or "message" in low or "preview" in low or "hermes" in low:
                    role = "Hermes Copilot / Chat UI"
                elif "toggle" in low or "switch" in low or "handle" in low or "select" in low or "sync" in low:
                    role = "Event Handler / State Transition"
                elif "set" in low or "update" in low:
                    role = "DOM Updater / State Sync"

                js_funcs.append({
                    "name": name_match,
                    "file": f"frontend/{js_name}",
                    "line": idx,
                    "args": args_str.strip(),
                    "role": role,
                })

    frontend_dir = repo_root / "frontend"
    css_files = []
    for css_file in sorted(frontend_dir.glob("*.css")):
        line_count = len(css_file.read_text(encoding="utf-8").splitlines())
        css_files.append((css_file.name, line_count))

    return html_ids, sorted(list(js_endpoints)), js_funcs, css_files


def parse_plugin_tools(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Parse tools registered in plugins/humming_bird/tools.py using AST."""
    tools_path = repo_root / "plugins" / "humming_bird" / "tools.py"
    if not tools_path.exists():
        return []
    content = tools_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(tools_path))
    tools = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("hb_"):
            doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
            end_line = getattr(node, "end_lineno", node.lineno)
            args = [a.arg for a in node.args.args if a.arg != "self"]

            cat = "Read Tool"
            if "place_order" in node.name or "set_" in node.name or "quarantine" in node.name or "restore_" in node.name or "rollback" in node.name:
                cat = "Write / Order Tool"
            elif "automation" in node.name or "scheduler" in node.name or "run_cycle" in node.name:
                cat = "Engine / Automation Tool"
            elif "mode" in node.name or "caps" in node.name:
                cat = "Mode & Risk Caps Tool"
            elif "stocknow" in node.name or "sync" in node.name:
                cat = "Broker Session & Sync Tool"

            tools.append({
                "name": node.name,
                "file": "plugins/humming_bird/tools.py",
                "lineno": node.lineno,
                "end_lineno": end_line,
                "args": ", ".join(args),
                "doc": doc or "Hermes agent plugin tool",
                "category": cat,
            })

    return tools


def generate_markdown(repo_root: Path = REPO_ROOT, output_file: Path = OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    pinned_vendor_commit = get_pinned_vendor_commit(repo_root)

    discovered_files = discover_files(repo_root)
    metrics, file_list = collect_file_metrics(discovered_files, repo_root)
    parsed_py = parse_python_files(discovered_files, repo_root)

    routes = parse_fastapi_routes([
        repo_root / "backend" / "main.py",
        repo_root / "backend" / "routes_hermes.py",
        repo_root / "backend" / "routes_auth_settings.py",
        repo_root / "backend" / "routes_stocknow.py",
        repo_root / "backend" / "kernel_api.py",
    ], repo_root)

    html_ids, js_endpoints, js_funcs, css_files = parse_frontend(repo_root)
    plugin_tools = parse_plugin_tools(repo_root)

    css_tokens, css_components = parse_css_design(
        repo_root / "frontend" / "styles.css",
        repo_root / "frontend" / "theme_light_hermes.css",
    )

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    md = []
    md.append("# 🗺️ Codebase AST Map & System Architecture Radar\n")
    md.append(f"> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **{now_iso}**.")
    md.append("> **Excluded Paths:** `vendor/`, `node_modules/`, `.venv/`, `venv/`, `.git/`, `__pycache__/`, `backend/data/`, `.pytest_cache/`, `dist/`, `build/`, `scratch/`")
    md.append(f"> **Pinned Vendor Commit (`vendor/hermes-agent`):** `{pinned_vendor_commit}`\n")
    md.append("---\n")

    # Section 1: Repository Topology & File Metrics
    md.append("## 1. Repository Topology & File Metrics\n")
    md.append("| Extension / Type | File Count | Total Lines of Code | Description |")
    md.append("| :--- | :--- | :--- | :--- |")

    total_files = sum(m["count"] for m in metrics.values())
    total_lines = sum(m["lines"] for m in metrics.values())

    # Sort major extensions first by lines descending, then other
    sorted_exts = sorted(
        [k for k in metrics.keys() if k != "other"],
        key=lambda k: -metrics[k]["lines"]
    )
    if "other" in metrics:
        sorted_exts.append("other")

    for ext in sorted_exts:
        stat = metrics[ext]
        desc = EXTENSION_DESCRIPTIONS.get(ext, "Configuration / Asset")
        ext_label = f"`{ext}`" if ext != "other" else "*other*"
        md.append(f"| {ext_label} | {stat['count']} | {stat['lines']:,} | {desc} |")
    md.append(f"| **TOTAL** | **{total_files}** | **{total_lines:,}** | *Entire Humming Bird Repository* |\n")

    # Section 2: Internal Dependency & Import Graph
    md.append("## 2. Internal Dependency & Import Graph\n")
    md.append("Shows intra-repo module dependencies within `backend/`, `plugins/`, and `scripts/`:\n")
    md.append("| Module File | Imported Internal Dependencies |")
    md.append("| :--- | :--- |")
    for mod_path, visitor in parsed_py.items():
        internal_deps = sorted(list(set(
            imp for imp in visitor.imports
            if imp.startswith("backend") or imp.startswith("scripts") or imp.startswith("plugins")
        )))
        dep_str = ", ".join(f"`{d}`" for d in internal_deps) if internal_deps else "*Independent Core Module*"
        md.append(f"| [`{mod_path}`](/{mod_path}) | {dep_str} |")
    md.append("\n---\n")

    # Section 3: Python AST X-Ray & Class/Function Registry
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

    # Section 4: Database Schema X-Ray
    md.append("## 4. Database Schema X-Ray (`backend/database.py`)\n")
    md.append("SQLAlchemy ORM Entities backing the deterministic ledger and state store:\n")
    db_visitor = parsed_py.get("backend/database.py")
    if db_visitor:
        md.append("| Model Entity | Line Range | Base | Purpose & Managed Ledger State |")
        md.append("| :--- | :--- | :--- | :--- |")
        for c in db_visitor.classes:
            if "Base" in c["bases"]:
                md.append(f"| `{c['name']}` | `L{c['lineno']}–L{c['end_lineno']}` | `Base` | {c['doc'] or 'Durable transactional entity'} |")
    md.append("\n---\n")

    # Section 5: FastAPI Route Registry
    md.append("## 5. FastAPI Route Registry (All Sub-Routers & Endpoints)\n")
    md.append("| Method | Route Path | Module File | Line | Handler Function | Description |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in routes:
        md.append(f"| `{r['method']}` | `{r['path']}` | [`{r['file']}`](/{r['file']}#L{r['lineno']}) | `L{r['lineno']}` | `{r['func_name']}()` | {r['doc']} |")
    md.append("\n---\n")

    # Section 6: Frontend DOM, JS Controller, CSS Design & UI Tool Integration
    md.append("## 6. Frontend DOM, JS Controller, CSS Design & UI Tool Integration\n")

    # 6.1 Theme Color & Layout Tokens
    md.append("### 6.1 Theme Color & Layout Tokens Table (`:root` Dark vs Light Mode)\n")
    md.append("| CSS Custom Property | Category | Dark Mode (`:root`) | Light Mode (`[data-theme=\"light\"]`) |")
    md.append("| :--- | :--- | :--- | :--- |")
    for t in css_tokens:
        md.append(f"| `{t['token']}` | {t['category']} | `{t['dark']}` | `{t['light']}` |")
    md.append("\n")

    # 6.2 Component CSS Selector Map
    md.append("### 6.2 Component CSS Selector Map\n")
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

    # 6.3 DOM Identifiers in frontend/index.html
    md.append("### 6.3 DOM Identifiers Index (`frontend/index.html`)\n")
    md.append(f"Complete catalog of all **{len(html_ids)}** distinct element IDs in `frontend/index.html` for UI element location:\n")
    md.append("| DOM Element ID (`id=\"...\"`) | HTML Tag | Line Number |")
    md.append("| :--- | :--- | :--- |")
    for el in html_ids:
        md.append(f"| `#{el['id']}` | `<{el['tag']}>` | [`frontend/index.html#L{el['line']}`](/frontend/index.html#L{el['line']}) |")
    md.append("\n")

    # 6.4 Core JavaScript Controllers in frontend/app.js, charts.js, hermes_ui.js
    md.append("### 6.4 JavaScript Controllers & UI Functions (`frontend/app.js`, `charts.js`, `hermes_ui.js`)\n")
    md.append(f"Complete index of all **{len(js_funcs)}** JavaScript controller and rendering functions:\n")
    md.append("| Function | Module File | Line | Role / Category |")
    md.append("| :--- | :--- | :--- | :--- |")
    for fn in js_funcs:
        md.append(f"| `{fn['name']}()` | [`{fn['file']}`](/{fn['file']}#L{fn['line']}) | `L{fn['line']}` | {fn['role']} |")
    md.append("\n")

    # 6.5 Hermes Agent Plugin Tool Registry
    md.append("### 6.5 Hermes Agent Plugin Tool Registry (`plugins/humming_bird/tools.py`)\n")
    md.append(f"Complete catalog of all **{len(plugin_tools)}** registered Hermes tools powering chat commands and UI interactions:\n")
    md.append("| Tool Name | Category | Line Range | Purpose / Description |")
    md.append("| :--- | :--- | :--- | :--- |")
    for t in plugin_tools:
        md.append(f"| `{t['name']}` | {t['category']} | [`plugins/humming_bird/tools.py#L{t['lineno']}`](/plugins/humming_bird/tools.py#L{t['lineno']}-L{t['end_lineno']}) | {t['doc']} |")
    md.append("\n")

    # 6.6 Frontend Stylesheets
    md.append("### 6.6 Frontend Stylesheets (`frontend/*.css`)\n")
    md.append("| Stylesheet File | Lines | Purpose |")
    md.append("| :--- | :--- | :--- |")
    for css_name, count in css_files:
        desc = "Daylight overrides & Hermes IDE sidebar" if "light" in css_name or "hermes" in css_name else "Core design tokens, layout & widgets"
        md.append(f"| `{css_name}` | {count} | {desc} |")
    md.append("\n")

    # 6.7 Frontend API Invocations
    md.append("### 6.7 Frontend API Contract Invocations (`frontend/*.js`)\n")
    md.append("| Endpoint Invocated | Direction | Purpose |")
    md.append("| :--- | :--- | :--- |")
    for ep in js_endpoints:
        md.append(f"| `{ep}` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |")
    md.append("\n---\n")

    # Section 7: Code Health & Complexity Radar
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
    md.append(f"> **Audit Summary:** {len(parsed_py)} Python modules inspected, {len(routes)} FastAPI endpoints registered, {len(js_funcs)} JS functions mapped, {len(html_ids)} DOM IDs indexed, {len(plugin_tools)} Hermes tools registered, {total_lines:,} total LOC indexed across {total_files} repository files.")

    output_file.write_text("\n".join(md), encoding="utf-8")
    print(f"Generated {output_file} ({len(md)} sections, {total_lines:,} LOC mapped across {total_files} files).")


if __name__ == "__main__":
    generate_markdown()
