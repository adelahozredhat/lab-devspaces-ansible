#!/usr/bin/env python3
"""Parse info-lab-users.txt into JSON for playbook-start-workspaces.yaml."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _field(block: str, name: str) -> str:
    m = re.search(rf"^{re.escape(name)}:\s*(.*)$", block, re.MULTILINE)
    if not m:
        raise ValueError(f"missing field {name!r}")
    return m.group(1).strip()


def parse(text: str) -> dict:
    header, _, rest = text.partition("Usuarios:")
    api_url = _field(header, "API URL")
    admin_password = _field(header, "Admin Password")
    cluster_domain = _field(header, "Cluster_domain")

    users = []
    chunks = re.split(r"\n(?=DevSpaces URL:)", rest)
    for chunk in chunks:
        if "DevSpaces User:" not in chunk:
            continue
        user = _field(chunk, "DevSpaces User")
        users.append(
            {
                "user": user,
                "password": _field(chunk, "DevSpaces Password"),
                "devspaces_url": _field(chunk, "DevSpaces URL").rstrip("/"),
                "gitea_url": _field(chunk, "Gitea URL").rstrip("/"),
                "gitea_user": _field(chunk, "Gitea User"),
                "gitea_password": _field(chunk, "Gitea Password"),
                "namespace": f"{user}-devspaces",
            }
        )

    if not users:
        raise ValueError("no DevSpaces users found in info-lab-users.txt")

    return {
        "api_url": api_url,
        "admin_password": admin_password,
        "cluster_domain": cluster_domain,
        "devspaces_url": users[0]["devspaces_url"],
        "gitea_url": users[0]["gitea_url"],
        "users": users,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_info_lab_users.py INFO_LAB_USERS_TXT", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    print(json.dumps(parse(path.read_text()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
