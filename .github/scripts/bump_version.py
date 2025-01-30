#!/usr/bin/env python3

import sys
from typing import Tuple

import toml


def parse_version(version: str) -> Tuple[int, int, int]:
    major, minor, patch = map(int, version.split("."))
    return major, minor, patch


def bump_version(current_version: str, bump_type: str) -> str:
    major, minor, patch = parse_version(current_version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <major|minor|patch>")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ("major", "minor", "patch"):
        print(f"Invalid bump type: {bump_type}")
        print("Must be one of: major, minor, patch")
        sys.exit(1)

    # Read the current pyproject.toml
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)

    current_version = config["project"]["version"]
    new_version = bump_version(current_version, bump_type)

    # Update the version
    config["project"]["version"] = new_version

    # Write back to pyproject.toml
    with open("pyproject.toml", "w") as f:
        toml.dump(config, f)

    print(f"Version bumped from {current_version} to {new_version}")


if __name__ == "__main__":
    main()
