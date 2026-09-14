#!/usr/bin/env python3
"""Build a Che/Dev Spaces DevWorkspace CR from a user Devfile + che-code editor."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return data


def merge_editor(devfile: dict, editor: dict) -> dict:
    template: dict = {
        "attributes": {
            "controller.devfile.io/devworkspace-config": {
                "name": "devworkspace-config",
                "namespace": "openshift-devspaces",
            },
            "controller.devfile.io/scc": "container-build",
            "controller.devfile.io/storage-type": "per-user",
        }
    }
    for key, value in devfile.items():
        if key in ("schemaVersion", "metadata"):
            continue
        if key == "attributes" and isinstance(value, dict):
            template["attributes"].update(value)
        else:
            template[key] = value

    template.setdefault("components", [])
    names = {c.get("name") for c in template["components"] if isinstance(c, dict)}
    for component in editor.get("components") or []:
        if component.get("name") not in names:
            template["components"].append(component)

    template.setdefault("commands", [])
    ids = {c.get("id") for c in template["commands"] if isinstance(c, dict)}
    for command in editor.get("commands") or []:
        if command.get("id") not in ids:
            template["commands"].append(command)

    events = template.setdefault("events", {})
    for phase, commands in (editor.get("events") or {}).items():
        current = events.setdefault(phase, [])
        for cmd in commands:
            if cmd not in current:
                current.append(cmd)
    return template


def build(devfile: dict, editor: dict, namespace: str, name: str) -> dict:
    return {
        "apiVersion": "workspace.devfile.io/v1alpha2",
        "kind": "DevWorkspace",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "annotations": {
                "che.eclipse.org/che-editor": "che-incubator/che-code/latest",
            },
        },
        "spec": {
            "routingClass": "che",
            "started": True,
            "template": merge_editor(devfile, editor),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--devfile", required=True, type=Path)
    parser.add_argument("--editor", required=True, type=Path)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--name", default="ansible-demo")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    dw = build(
        _load_yaml(args.devfile),
        _load_yaml(args.editor),
        args.namespace,
        args.name,
    )
    args.output.write_text(
        yaml.dump(dw, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
