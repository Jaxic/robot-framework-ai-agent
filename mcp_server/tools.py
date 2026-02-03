"""
MCP Server Tools for Robot Framework AI Agent.

Provides four tools for managing and inspecting Robot Framework test suites:

    1. list_available_tests   — Discover .robot files and their documentation.
    2. execute_test_suite     — Run a suite and return structured results.
    3. get_latest_results     — Parse the most recent output.xml for test outcomes.
    4. search_test_logs       — Search output.xml log messages by keyword and level.

Usage:
    from mcp_server.tools import mcp
    mcp.run(transport="stdio")
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from robot import run as robot_run
from robot.api import ExecutionResult

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure the results directory exists so every tool can rely on it.
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("mcp_server.tools")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_handler)

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="Robot Framework MCP Server",
    instructions=(
        "Provides tools for listing, executing, and inspecting "
        "Robot Framework test suites."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_suite_doc(robot_file: Path) -> str:
    """Parse a .robot file and return the Suite-level Documentation value."""
    doc_lines: list[str] = []
    in_settings = False
    capturing = False

    for raw_line in robot_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line == "*** Settings ***":
            in_settings = True
            continue
        if line.startswith("*** ") and in_settings:
            break  # Left the Settings table

        if not in_settings:
            continue

        # Continuation line while already capturing documentation.
        if capturing and line.startswith("..."):
            doc_lines.append(line[3:].strip())
            continue
        elif capturing:
            # First non-continuation line ends the Documentation value.
            capturing = False

        if line.lower().startswith("documentation"):
            # Everything after the keyword (tab/space separated).
            parts = line.split(None, 1)
            if len(parts) > 1:
                doc_lines.append(parts[1])
            capturing = True

    return " ".join(doc_lines).strip()


def _result_to_dict(result: object) -> dict:
    """Convert an ExecutionResult into a JSON-serialisable dict."""
    suite = result.suite
    stats = suite.statistics
    elapsed = suite.elapsed_time.total_seconds()

    tests: list[dict] = []
    for test in suite.tests:
        tests.append(
            {
                "name": test.name,
                "status": test.status,
                "message": test.message or "",
                "duration_s": round(test.elapsed_time.total_seconds(), 3),
                "tags": list(test.tags),
            }
        )

    return {
        "suite": suite.name,
        "status": suite.status,
        "total": stats.total,
        "passed": stats.passed,
        "failed": stats.failed,
        "skipped": stats.skipped,
        "elapsed_s": round(elapsed, 3),
        "tests": tests,
    }


def _find_latest_output(suite_name: Optional[str] = None) -> Optional[Path]:
    """Return the most-recently modified output XML in results/."""
    if suite_name:
        target = RESULTS_DIR / suite_name / "output.xml"
        return target if target.is_file() else None

    # Scan all sub-dirs for the newest output.xml.
    candidates = sorted(
        RESULTS_DIR.glob("*/output.xml"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# Tool 1: list_available_tests
# ---------------------------------------------------------------------------

@mcp.tool()
def list_available_tests() -> str:
    """Scan the tests/ directory for .robot files and return a JSON array.

    Each element contains:
      - name:        Suite name derived from the filename.
      - file:        Relative path to the .robot file.
      - description: The Suite Documentation string (if any).
    """
    logger.info("list_available_tests called")

    if not TESTS_DIR.is_dir():
        return json.dumps({"error": f"Tests directory not found: {TESTS_DIR}"})

    suites: list[dict] = []
    for robot_file in sorted(TESTS_DIR.glob("*.robot")):
        suites.append(
            {
                "name": robot_file.stem,
                "file": str(robot_file.relative_to(PROJECT_ROOT)),
                "description": _extract_suite_doc(robot_file),
            }
        )

    logger.info("Found %d test suite(s)", len(suites))
    return json.dumps(suites, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: execute_test_suite
# ---------------------------------------------------------------------------

@mcp.tool()
def execute_test_suite(suite_name: str) -> str:
    """Execute a Robot Framework test suite by name and return results as JSON.

    Args:
        suite_name: Stem of the .robot file (e.g. ``bitlocker_compliance``).

    Returns JSON with:
      - status, total, passed, failed, skipped, elapsed_s, timestamp
      - tests: list of per-test results with name, status, message, duration_s
    """
    logger.info("execute_test_suite called with suite_name=%r", suite_name)

    robot_file = TESTS_DIR / f"{suite_name}.robot"
    if not robot_file.is_file():
        available = [f.stem for f in TESTS_DIR.glob("*.robot")]
        return json.dumps(
            {
                "error": f"Suite '{suite_name}' not found",
                "available_suites": available,
            }
        )

    # Each suite gets its own results sub-directory.
    suite_results = RESULTS_DIR / suite_name
    suite_results.mkdir(exist_ok=True)

    output_xml = suite_results / "output.xml"
    log_html = suite_results / "log.html"
    report_html = suite_results / "report.html"

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        rc = robot_run(
            str(robot_file),
            output=str(output_xml),
            log=str(log_html),
            report=str(report_html),
        )
        logger.info("robot.run returned rc=%d", rc)
    except Exception as exc:
        logger.exception("robot.run raised an exception")
        return json.dumps({"error": f"Execution failed: {exc}", "timestamp": timestamp})

    # Parse output.xml for structured results.
    if not output_xml.is_file():
        return json.dumps(
            {
                "error": "output.xml was not created — execution may have crashed",
                "return_code": rc,
                "timestamp": timestamp,
            }
        )

    try:
        result = ExecutionResult(str(output_xml))
        payload = _result_to_dict(result)
        payload["return_code"] = rc
        payload["timestamp"] = timestamp
        return json.dumps(payload, indent=2)
    except Exception as exc:
        logger.exception("Failed to parse output.xml")
        return json.dumps(
            {"error": f"Result parsing failed: {exc}", "return_code": rc, "timestamp": timestamp}
        )


# ---------------------------------------------------------------------------
# Tool 3: get_latest_results
# ---------------------------------------------------------------------------

@mcp.tool()
def get_latest_results(suite_name: str = "") -> str:
    """Read the most recent output.xml and return structured test results.

    Args:
        suite_name: Optional suite name to filter to.  When empty, the most
                    recent output.xml across all suites is used.

    Returns JSON with per-test name, status, message, duration, and tags.
    """
    name = suite_name or None
    logger.info("get_latest_results called with suite_name=%r", name)

    output_xml = _find_latest_output(name)
    if output_xml is None:
        return json.dumps(
            {
                "error": "No output.xml found"
                + (f" for suite '{name}'" if name else "")
                + ". Run execute_test_suite first.",
            }
        )

    try:
        result = ExecutionResult(str(output_xml))
        payload = _result_to_dict(result)
        payload["source"] = str(output_xml.relative_to(PROJECT_ROOT))
        return json.dumps(payload, indent=2)
    except Exception as exc:
        logger.exception("Failed to parse %s", output_xml)
        return json.dumps({"error": f"Result parsing failed: {exc}"})


# ---------------------------------------------------------------------------
# Tool 4: search_test_logs
# ---------------------------------------------------------------------------

_VALID_LEVELS = {"FAIL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"}


@mcp.tool()
def search_test_logs(keyword: str, log_level: str = "FAIL") -> str:
    """Search output.xml log messages for a keyword at a given severity.

    Args:
        keyword:   Text to search for (case-insensitive substring match).
        log_level: Minimum severity to include. One of
                   FAIL, ERROR, WARN, INFO, DEBUG, TRACE.  Defaults to FAIL.

    Returns JSON array of matching entries with test context, timestamp,
    level, and the full message text.
    """
    level = log_level.upper()
    logger.info("search_test_logs called keyword=%r level=%r", keyword, level)

    if level not in _VALID_LEVELS:
        return json.dumps(
            {"error": f"Invalid log_level '{log_level}'. Must be one of: {sorted(_VALID_LEVELS)}"}
        )

    # Collect all output.xml files.
    xml_files = sorted(RESULTS_DIR.glob("*/output.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not xml_files:
        return json.dumps({"error": "No output.xml files found. Run execute_test_suite first."})

    # Severity ordering for filtering.
    severity_order = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FAIL"]
    min_index = severity_order.index(level)
    allowed_levels = set(severity_order[min_index:])

    keyword_lower = keyword.lower()
    matches: list[dict] = []

    for xml_path in xml_files:
        suite_name = xml_path.parent.name
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            logger.warning("Skipping malformed XML: %s", xml_path)
            continue

        # Walk <msg> elements anywhere in the tree.
        for msg_el in tree.iter("msg"):
            msg_level = (msg_el.get("level") or "").upper()
            if msg_level not in allowed_levels:
                continue

            text = msg_el.text or ""
            if keyword_lower not in text.lower():
                continue

            # Walk up to find the enclosing <test> for context.
            test_name = _find_ancestor_test_name(tree, msg_el)

            matches.append(
                {
                    "suite": suite_name,
                    "test": test_name,
                    "level": msg_level,
                    "timestamp": msg_el.get("timestamp", ""),
                    "message": text.strip(),
                }
            )

    logger.info("search_test_logs found %d match(es)", len(matches))
    return json.dumps(matches, indent=2)


def _find_ancestor_test_name(tree: ET.ElementTree, target: ET.Element) -> str:
    """Walk the tree to find the <test name='...'> ancestor of *target*.

    ElementTree elements don't have parent references, so we build a
    child-to-parent map on the fly.
    """
    parent_map = {child: parent for parent in tree.iter() for child in parent}
    node = target
    while node is not None:
        if node.tag == "test":
            return node.get("name", "(unknown)")
        node = parent_map.get(node)
    return "(suite-level)"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
