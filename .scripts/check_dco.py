#!/usr/bin/env python3
"""Require one author-matching DCO sign-off on every commit in a range."""

from __future__ import annotations

import re
import subprocess
import sys


TRAILER = re.compile(r"^Signed-off-by: (.+) <([^<>]+)>$")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <base> <head>", file=sys.stderr)
        return 2

    base, head = sys.argv[1:]
    commits = git("rev-list", "--reverse", f"{base}..{head}").splitlines()
    failures: list[str] = []

    for commit in commits:
        fields = git("show", "-s", "--format=%an%x00%ae%x00%B", commit).split("\0", 2)
        author_name, author_email, message = fields
        signoffs = [TRAILER.fullmatch(line) for line in message.splitlines()]
        signoffs = [match.groups() for match in signoffs if match]
        expected = (author_name, author_email)
        if signoffs != [expected]:
            short = git("rev-parse", "--short", commit).strip()
            failures.append(
                f"{short}: expected exactly one 'Signed-off-by: "
                f"{author_name} <{author_email}>' trailer"
            )

    if failures:
        print("DCO check failed:", file=sys.stderr)
        print("\n".join(f"  {failure}" for failure in failures), file=sys.stderr)
        print("\nFix each commit with: git commit --amend --signoff", file=sys.stderr)
        return 1

    print(f"DCO check passed for {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
