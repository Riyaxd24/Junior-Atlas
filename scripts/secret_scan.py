from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"(?i)(discord[_-]?token|bot[_-]?token)\s*=\s*[^\s<]{20,}"),
    re.compile(r"""(?i)(password|api[_-]?key|secret)\s*=\s*["'][A-Za-z0-9+/_.~-]{12,}["']"""),
    re.compile(r"(?i)(postgres(?:ql)?|mysql|redis)://[^:\s]+:[^@\s]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
EXCLUDED = {".git", ".venv", "venv", "htmlcov", "__pycache__", "tests", "docs"}


def scan_worktree() -> list[str]:
    findings: list[str] = []
    root = Path.cwd()
    for path in root.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED for part in path.parts):
            continue
        if path.name.endswith((".example", ".lock")):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(root)))
                break
    return sorted(set(findings))


def scan_tracked_history_names() -> list[str]:
    result = subprocess.run(
        ["git", "rev-list", "--all"],
        check=True,
        capture_output=True,
        text=True,
    )
    suspicious: set[str] = set()
    for revision in result.stdout.splitlines():
        ls = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", revision],
            check=True,
            capture_output=True,
            text=True,
        )
        for name in ls.stdout.splitlines():
            lowered = name.lower()
            if lowered == ".env" or lowered.endswith("/.env"):
                suspicious.add(name)
            if re.search(r"(secret|credential|token|password)", lowered):
                suspicious.add(name)
    return sorted(suspicious)


def main() -> int:
    worktree = scan_worktree()
    history = scan_tracked_history_names()
    if worktree:
        print("Potential secret-bearing worktree files:")
        for name in worktree:
            print(f"- {name}")
    else:
        print("Worktree secret scan: no potential assignments found.")
    if history:
        print("Suspicious secret-like paths in git history:")
        for name in history:
            print(f"- {name}")
    else:
        print("Git history secret-name scan: no .env or secret-like paths found.")
    return 1 if worktree else 0


if __name__ == "__main__":
    sys.exit(main())
