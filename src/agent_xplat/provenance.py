"""Read-only source identity for static reports; no target code is executed."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def source_identity(root: Path, sources) -> dict:
    digest = hashlib.sha256()
    for source in sources:
        digest.update(source.relative_path.encode('utf-8') + b'\0')
        digest.update(source.text.encode('utf-8') + b'\0')
    identity = {'git_commit': None, 'worktree': 'unknown',
                'scanned_text_sha256': digest.hexdigest(), 'method': 'static-inference'}
    if not (root / '.git').exists():
        return identity
    try:
        def git(*args):
            return subprocess.run(['git', '-c', 'core.fsmonitor=false', *args], cwd=root,
                                  capture_output=True, text=True, timeout=10, check=False)
        head = git('rev-parse', '--verify', 'HEAD')
        if head.returncode == 0:
            identity['git_commit'] = head.stdout.strip()
        status = git('status', '--porcelain', '--untracked-files=normal')
        if status.returncode == 0:
            identity['worktree'] = 'dirty' if status.stdout.strip() else 'clean'
    except (OSError, subprocess.TimeoutExpired):
        pass
    return identity
