#!/usr/bin/env python3
"""Exit 0 when every listed namespace has the Molecule VM in Running."""
from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: wait_molecule_vms.py KUBECONFIG VM_NAME NAMESPACES_JSON",
            file=sys.stderr,
        )
        return 2

    kubeconfig, name, namespaces_json = sys.argv[1], sys.argv[2], sys.argv[3]
    namespaces = json.loads(namespaces_json)
    env = os.environ.copy()
    env["KUBECONFIG"] = kubeconfig

    raw = subprocess.check_output(
        ["oc", "get", "vm", "-A", "-o", "json"],
        env=env,
        text=True,
    )
    items = json.loads(raw).get("items") or []
    statuses = {}
    for item in items:
        md = item.get("metadata") or {}
        if md.get("name") != name:
            continue
        ns = md.get("namespace") or ""
        if ns in namespaces:
            statuses[ns] = (item.get("status") or {}).get("printableStatus") or "Unknown"

    missing = [ns for ns in namespaces if ns not in statuses]
    not_running = [
        f"{ns}={statuses[ns]}"
        for ns in namespaces
        if statuses.get(ns) != "Running"
    ]
    running = len(namespaces) - len(missing) - len(
        [ns for ns in namespaces if ns in statuses and statuses[ns] != "Running"]
    )
    print(f"{running}/{len(namespaces)} Running")
    if missing:
        print("missing: " + ", ".join(missing))
    if not_running:
        print("not Running: " + ", ".join(not_running))

    if missing or not_running:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
