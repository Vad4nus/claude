#!/usr/bin/env python3
"""Print the simulator screen as compact rows: type|label|value|x,y (tap centre, device points).

Usage: screen.py <UDID>
Reads `axe describe-ui` (about 150 KB of JSON per screen) and keeps only elements with a label
or a value, so a screen costs a few hundred tokens instead of a screenshot's ~1,500.
"""
import json
import subprocess
import sys

out = subprocess.run(["axe", "describe-ui", "--udid", sys.argv[1]], capture_output=True, text=True)
try:
    tree = json.loads(out.stdout)
except json.JSONDecodeError:
    sys.exit(f"axe describe-ui failed: {(out.stderr or out.stdout).strip()[:300]}")

seen = set()


def walk(node):
    label, value, f = node.get("AXLabel"), node.get("AXValue"), node.get("frame") or {}
    if label or value:
        x, y = int(f.get("x", 0) + f.get("width", 0) / 2), int(f.get("y", 0) + f.get("height", 0) / 2)
        row = f"{node.get('type')}|{label or ''}|{value or ''}|{x},{y}"
        if row not in seen:
            seen.add(row)
            print(row)
    for child in node.get("children") or []:
        walk(child)


for root in tree:
    walk(root)
