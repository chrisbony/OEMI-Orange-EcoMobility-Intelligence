#!/usr/bin/env python3
"""
OEMI E2E Test Suite Runner.

Executes end-to-end tests across all 4 tiers (Tier 1 Features, Tier 2 Boundaries,
Tier 3 Combinations, Tier 4 Scenarios) using Pytest and Standalone Unittest.
Supports colorized terminal output, JSON artifact reports, and standalone execution.

Usage:
    python tests_e2e/test_runner.py
    python tests_e2e/test_runner.py --tier 1
    python tests_e2e/test_runner.py --tier 2
    python tests_e2e/test_runner.py --json-report test_report.json
"""

import sys
import os
import argparse
import subprocess
import json
import time
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ANSI terminal colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

TIER_FILES = {
    "1": os.path.join(PROJECT_ROOT, "tests_e2e", "test_tier1_features.py"),
    "2": os.path.join(PROJECT_ROOT, "tests_e2e", "test_tier2_boundaries.py"),
    "3": os.path.join(PROJECT_ROOT, "tests_e2e", "test_tier3_combinations.py"),
    "4": os.path.join(PROJECT_ROOT, "tests_e2e", "test_tier4_scenarios.py"),
}


def run_tests(tier: Optional[str] = None, json_report: Optional[str] = None) -> int:
    """Runs tests via pytest CLI subprocess, captures output and produces structured summaries."""
    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{CYAN}  Orange EcoMobility Intelligence (OEMI) — E2E Suite  {RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}")
    print(f"Filter: Tier={tier or 'All (Tiers 1-4)'}")
    print(f"Project Root: {PROJECT_ROOT}\n")

    cmd = [sys.executable, "-m", "pytest"]

    if tier and str(tier) in TIER_FILES:
        cmd.append(TIER_FILES[str(tier)])
    else:
        for t_path in TIER_FILES.values():
            cmd.append(t_path)

    cmd.extend(["-v", "--tb=short"])

    start_wall = time.time()
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    elapsed_total = time.time() - start_wall

    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    exit_code = proc.returncode

    if json_report:
        report_data = {
            "project": "Orange EcoMobility Intelligence (OEMI)",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tier_filter": tier or "ALL",
            "duration_sec": round(elapsed_total, 3),
            "exit_code": exit_code,
            "status": "PASSED" if exit_code == 0 else "FAILED",
            "stdout": proc.stdout
        }
        with open(json_report, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"\nSaved execution report to: {json_report}")

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OEMI E2E Test Suite Runner")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "all"], default=None, help="Filter by test tier")
    parser.add_argument("--json-report", default=None, help="File path to write JSON test report")
    args = parser.parse_args()

    exit_code = run_tests(tier=args.tier, json_report=args.json_report)
    sys.exit(exit_code)
