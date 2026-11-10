"""Unit tests for scripts/generate_code_map.py discovery, exclusion, and indexing logic."""

from pathlib import Path
import pytest

from scripts.generate_code_map import (
    REPO_ROOT,
    is_excluded,
    discover_files,
    collect_file_metrics,
    get_pinned_vendor_commit,
    parse_frontend,
    parse_plugin_tools,
    MAJOR_EXTENSIONS,
)


def test_is_excluded_directory_rules():
    """Verify is_excluded accurately blocks all specified blacklisted directories."""
    # Excluded directories
    assert is_excluded(REPO_ROOT / "vendor" / "hermes-agent" / "README.md") is True
    assert is_excluded(REPO_ROOT / "vendor" / "some_tool.py") is True
    assert is_excluded(REPO_ROOT / "node_modules" / "package" / "index.js") is True
    assert is_excluded(REPO_ROOT / ".venv" / "Lib" / "site-packages" / "fastapi.py") is True
    assert is_excluded(REPO_ROOT / "venv" / "bin" / "python") is True
    assert is_excluded(REPO_ROOT / ".git" / "config") is True
    assert is_excluded(REPO_ROOT / ".git" / "HEAD") is True
    assert is_excluded(REPO_ROOT / "backend" / "__pycache__" / "database.cpython-312.pyc") is True
    assert is_excluded(REPO_ROOT / "backend" / "data" / "hummingbird.db") is True
    assert is_excluded(REPO_ROOT / "backend" / "data" / "backups" / "hummingbird_backup.db") is True
    assert is_excluded(REPO_ROOT / ".pytest_cache" / "v" / "cache" / "lastfailed") is True
    assert is_excluded(REPO_ROOT / "dist" / "bundle.js") is True
    assert is_excluded(REPO_ROOT / "build" / "lib" / "module.py") is True
    assert is_excluded(REPO_ROOT / "scratch" / "test_scratch.py") is True


def test_is_excluded_valid_repo_files():
    """Verify is_excluded preserves legitimate repository source and config files."""
    assert is_excluded(REPO_ROOT / "README.md") is False
    assert is_excluded(REPO_ROOT / "AGENTS.md") is False
    assert is_excluded(REPO_ROOT / "pyproject.toml") is False
    assert is_excluded(REPO_ROOT / ".gitignore") is False
    assert is_excluded(REPO_ROOT / ".agentignore") is False
    assert is_excluded(REPO_ROOT / ".cursorignore") is False
    assert is_excluded(REPO_ROOT / ".opencodeignore") is False
    assert is_excluded(REPO_ROOT / "backend" / "kernel_api.py") is False
    assert is_excluded(REPO_ROOT / "frontend" / "app.js") is False
    assert is_excluded(REPO_ROOT / "frontend" / "index.html") is False
    assert is_excluded(REPO_ROOT / "plugins" / "humming_bird" / "tools.py") is False
    assert is_excluded(REPO_ROOT / "scripts" / "generate_code_map.py") is False
    assert is_excluded(REPO_ROOT / "tests" / "test_api.py") is False


def test_discover_files_sanity():
    """Verify discovered files list contains only non-excluded real repository files."""
    files = discover_files(REPO_ROOT)
    assert len(files) > 50

    rel_paths = [f.relative_to(REPO_ROOT).as_posix() for f in files]

    # 1. No vendor paths
    for p in rel_paths:
        assert not p.startswith("vendor/"), f"Discovered vendor path: {p}"
        assert not p.startswith("node_modules/"), f"Discovered node_modules path: {p}"
        assert not p.startswith(".venv/"), f"Discovered .venv path: {p}"
        assert not p.startswith("backend/data/"), f"Discovered backend/data path: {p}"
        assert "__pycache__" not in p, f"Discovered __pycache__ path: {p}"
        assert not p.startswith("scratch/"), f"Discovered scratch path: {p}"

    # 2. .png count is 0
    png_files = [p for p in rel_paths if p.lower().endswith(".png")]
    assert len(png_files) == 0, f"Found unexpected .png files: {png_files}"

    # 3. .py file count is in the low hundreds (< 150, typically ~77)
    py_files = [p for p in rel_paths if p.endswith(".py")]
    assert 50 <= len(py_files) <= 150, f"Unexpected .py file count: {len(py_files)}"

    # 4. .md file count matches tracked markdown only (typically 10-12)
    md_files = [p for p in rel_paths if p.endswith(".md")]
    assert 10 <= len(md_files) <= 15, f"Expected tracked markdown files, found: {len(md_files)}"


def test_collect_file_metrics_grouping():
    """Verify extension metrics derive from real pathlib suffixes and group tail as 'other'."""
    files = discover_files(REPO_ROOT)
    metrics, file_list = collect_file_metrics(files, REPO_ROOT)

    # Check that nonsense extensions do not exist
    nonsense_extensions = {".be", ".win", "hermes-agent@localhost", "@localhost"}
    for ext in metrics.keys():
        assert ext not in nonsense_extensions, f"Nonsense extension found: {ext}"

    # All grouped keys must either be in MAJOR_EXTENSIONS or be 'other'
    for ext in metrics.keys():
        assert ext in MAJOR_EXTENSIONS or ext == "other", f"Unexpected extension key: {ext}"

    # Python count matches exactly
    py_files = [f for f in files if f.suffix.lower() == ".py"]
    assert metrics[".py"]["count"] == len(py_files)


def test_frontend_indexing():
    """Verify JS functions and index.html IDs are thoroughly indexed."""
    html_ids, js_endpoints, js_funcs, css_files = parse_frontend(REPO_ROOT)

    # HTML IDs
    assert len(html_ids) >= 200
    id_names = {item["id"] for item in html_ids}
    assert "topbar-clock-widget" in id_names
    assert "run-cycle" in id_names
    assert "overview" in id_names

    # JS Functions
    assert len(js_funcs) >= 80
    func_names = {item["name"] for item in js_funcs}
    assert "formatTimestamp" in func_names
    assert "renderMainChart" in func_names
    assert "renderOrderPreviewCard" in func_names


def test_plugin_tools_indexing():
    """Verify all 22 registered tools in plugins/humming_bird/tools.py are indexed."""
    tools = parse_plugin_tools(REPO_ROOT)
    assert len(tools) == 22

    tool_names = {t["name"] for t in tools}
    assert "hb_portfolio" in tool_names
    assert "hb_place_order" in tool_names
    assert "hb_run_cycle" in tool_names
    assert "hb_sync" in tool_names
    assert "hb_caps_set" in tool_names


def test_pinned_vendor_commit():
    """Verify pinned vendor commit returns a valid 40-character SHA."""
    sha = get_pinned_vendor_commit(REPO_ROOT)
    assert len(sha) == 40
    assert sha == "b777adb7918713e5786cc9d95ad5b854074f2cb6"

