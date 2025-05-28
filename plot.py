#!/usr/bin/env python3
"""
plot_rx.py - Plot cumulative bytes received vs. time from a curl trace log.

Usage: python plot_rx.py logfile [outfile.png]
"""
import re
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from functools import reduce

if len(sys.argv) < 2:
    sys.exit("Usage:  python plot_rx.py logfile [outfile.png]")

logfile = sys.argv[1]
save_to = sys.argv[2] if len(sys.argv) > 2 else None

# ----- regexes -----
ts_rx   = re.compile(r'^(?P<ts>\d{2}:\d{2}:\d{2}\.\d{6})')          # any timestamp
data_rx = re.compile(r'^(?P<ts>\d{2}:\d{2}:\d{2}\.\d{6})\s+<=\s+Recv data,\s+(?P<bytes>\d+)\s+bytes')

times, totals = [], []
t0, total_bytes = None, 0

with open(logfile, encoding='utf-8') as f:
    for line in f:
        # 1) Grab the very first timestamp we encounter, whatever the line
        if t0 is None:
            m0 = ts_rx.match(line)
            if m0:
                t0 = datetime.strptime(m0.group('ts'), '%H:%M:%S.%f')
                times.append((t0-t0).total_seconds())
                totals.append(0)

        # 2) Process only the Recv-data lines
        m = data_rx.match(line)
        if not m:
            continue

        ts = datetime.strptime(m.group('ts'), '%H:%M:%S.%f')
        elapsed = (ts - t0).total_seconds()

        total_bytes += int(m.group('bytes'))
        times.append(elapsed)
        totals.append(total_bytes)

        if total_bytes > 12 * 1024 * 1024: break

# ----- plotting -----
plt.step(times, totals, where='post')
plt.xlabel('Time since first timestamp (s)')
plt.ylabel('Cumulative bytes received')
plt.title('Received bytes vs. time')
plt.grid(True, linestyle='--', alpha=0.5)

if save_to:
    plt.savefig(save_to, dpi=150, bbox_inches='tight')
    print(f"Plot written to {save_to}")
else:
    plt.show()
