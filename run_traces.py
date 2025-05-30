#!/usr/bin/env python3
"""
run_traces.py - Collect several curl traces through *trace.sh* and overlay them
on one cumulative-bytes-vs-time plot.

The companion *trace.sh* must accept **two positional arguments** exactly:

    trace.sh <download-file> <logfile>

Where *download-file* is one of a small, fixed set of test objects
and *logfile* ends in ``.log``.

---------------------------------------------------------------------------
Usage
---------------------------------------------------------------------------

    python run_traces.py <FILE> <N> [outfile.png]

  <FILE>        - which object to download (must be allowed by trace.sh)
  <N>           - positive integer: how many consecutive traces to collect
  [outfile.png] - optional path to save the finished figure instead of
                  opening a window.

Example
-------

    python run_traces.py 1M.bin 5  overlay.png

Dependencies: Python 3.8+, matplotlib.
"""

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

# Keep this in sync with the list printed by trace.sh
ALLOWED_FILES = {
    "1K.bin",
    "1M.bin",
    "1G.bin",
}

TRACE_DIR = Path("traces")
TRACE_SH = Path("trace.sh")

RECV_DATA = re.compile(
    r"^(?P<ts>\d{2}:\d{2}:\d{2}\.\d{6})\s+<=\s+Recv data,\s+(?P<bytes>\d+)\s+bytes"
)
ANY_TS = re.compile(r"^(?P<ts>\d{2}:\d{2}:\d{2}\.\d{6})")


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def parse_log(path: Path):
    """Return (times_seconds, cumulative_bytes) parsed from a curl trace."""
    times, totals = [], []
    t0, cum = None, 0

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if t0 is None:
                m0 = ANY_TS.match(line)
                if m0:
                    t0 = datetime.strptime(m0.group("ts"), "%H:%M:%S.%f")
                    # Start at the first timestamp we see (not necessarily Recv data)
            m = RECV_DATA.match(line)
            if not m:
                continue
            ts = datetime.strptime(m.group("ts"), "%H:%M:%S.%f")
            times.append((ts - t0).total_seconds())
            cum += int(m.group("bytes"))
            totals.append(cum)
    return times, totals


def run_trace(file_name: str, run_idx: int) -> Path:
    """Invoke trace.sh for one run and return the resulting log path."""
    log_path = TRACE_DIR / f"{file_name}_{run_idx}.log"
    log_path.parent.mkdir(exist_ok=True)

    print(f"[run_traces] Collecting run {run_idx}: {file_name} → {log_path}")
    subprocess.run(
        ["bash", str(TRACE_SH), file_name, str(log_path)],
        check=True,
    )
    return log_path


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python run_traces.py <FILE> <N> [outfile.png]")
    file_name = sys.argv[1]
    try:
        n_runs = int(sys.argv[2])
        assert n_runs > 0
    except (ValueError, AssertionError):
        sys.exit("<N> must be a positive integer")

    if file_name not in ALLOWED_FILES:
        sys.exit(
            f"File '{file_name}' is not in ALLOWED_FILES (\n  " + ", ".join(sorted(ALLOWED_FILES)) + ")"
        )

    out_png = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not TRACE_SH.exists():
        sys.exit(f"Cannot find {TRACE_SH}. Expected it next to this script.")

    # Collect logs
    logs = [run_trace(file_name, i + 1) for i in range(n_runs)]

    # Build the overlay plot
    for idx, log in enumerate(logs, 1):
        t, b = parse_log(log)
        label = f"trace {idx}"
        plt.step(t, b, where="post", alpha=0.75, label=label)

    plt.xlabel("Time since first byte (s)")
    plt.ylabel("Cumulative bytes received")
    plt.title(f"{file_name} - {n_runs} consecutive traces")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()

    if out_png:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_png, dpi=150, bbox_inches="tight")
        print(f"[run_traces] Plot written to {out_png}")
    else:
        plt.show()


if __name__ == "__main__":  # pragma: no cover
    main()
