"""Bound shell regexes to Markdown command examples, preserving positions."""
from __future__ import annotations

import re
from ..models import SourceFile

_SHELL_LANGUAGES = {'sh', 'bash', 'zsh', 'shell', 'shellscript', 'console', 'powershell', 'pwsh', 'ps1', 'cmd', 'bat', 'batch'}
_COMMAND = re.compile(
    r'^(?:(?:chmod|export|source|where|set|echo|printf|python3?|node|npm|npx|pnpm|yarn|bun|git|pip3?|uv|bash|sh|zsh|pwsh|grep|sed|awk|find|which|rm|cp|mv|touch|cat|head|tail|xargs|chown)\s+'
    r'|\$env:[A-Za-z_][A-Za-z0-9_]*\s*='
    r'|[A-Za-z_][A-Za-z0-9_]*=[^\s]+(?:\s|$)'
    r'|\.\s+\S|\./\S|%[A-Za-z_][A-Za-z0-9_]*%)'
)


def shell_examples(source: SourceFile) -> SourceFile:
    """Mask prose, Markdown delimiters and explicitly non-shell code fences.

    This is conservative example extraction, not a Markdown or shell parser.
    Unknown unfenced commands may be missed; path/runtime rules are unaffected.
    """
    if source.path.suffix.lower() != '.md':
        return source
    lines = []
    fence = None
    language = ''
    for line in source.lines:
        masked = [' '] * len(line)
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})([^\s`]*)\s*$', line)
        if match and fence is None:
            fence, language = match[1], match[2].lower()
        elif fence is not None:
            if re.match(r'^\s{0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            elif language in _SHELL_LANGUAGES or (not language and _COMMAND.match(line.lstrip())):
                masked = list(line)
        else:
            for span in re.finditer(r'(`+)(.+?)\1', line):
                if _COMMAND.match(span[2].lstrip()):
                    masked[span.start(2):span.end(2)] = span[2]
            if '`' not in line and _COMMAND.match(line.lstrip()):
                masked = list(line)
        lines.append(''.join(masked))
    return SourceFile(source.path, source.relative_path, '\n'.join(lines), source.size, source.mode, source.is_crlf)
