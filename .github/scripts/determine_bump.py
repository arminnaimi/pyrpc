#!/usr/bin/env python3

import re
import sys


def analyze_commits(commits_str: str) -> tuple[str, bool]:
    """
    Analyze commit messages to determine the type of version bump needed.
    Returns (bump_type, should_bump)

    Conventional Commits Format:
    - fix: patch bump
    - feat: minor bump
    - BREAKING CHANGE or feat!: major bump
    """
    commits = commits_str.strip().split("\n")
    should_bump = False
    bump_type = "patch"  # default to patch

    breaking_pattern = re.compile(r"BREAKING\s+CHANGE:|!:")

    for commit in commits:
        commit = commit.strip()
        if not commit:
            continue

        should_bump = True

        # Check for breaking changes
        if breaking_pattern.search(commit):
            return "major", True

        # Check commit type
        match = re.match(
            r"^(fix|feat|chore|docs|style|refactor|perf|test|build|ci|revert)(\(.*?\))?: ",
            commit,
        )
        if match:
            commit_type = match.group(1)
            if commit_type == "feat":
                bump_type = "minor"

    return bump_type, should_bump


def main():
    if len(sys.argv) != 2:
        print("Usage: determine_bump.py <commits>")
        sys.exit(1)

    commits = sys.argv[1]
    bump_type, should_bump = analyze_commits(commits)

    # Set GitHub Actions output variables
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"bump_type={bump_type}\n")
        f.write(f"should_bump={'true' if should_bump else 'false'}\n")

    print(f"Determined bump type: {bump_type}")
    print(f"Should bump: {should_bump}")


if __name__ == "__main__":
    import os

    main()
