"""Line-ending classification independent of the host OS."""

from __future__ import annotations


def line_ending_style(data: bytes) -> str:
    has_crlf = b"\r\n" in data
    remaining = data.replace(b"\r\n", b"")
    has_lf = b"\n" in remaining
    has_cr = b"\r" in remaining
    if has_crlf and (has_lf or has_cr):
        return "MIXED"
    if has_crlf:
        return "CRLF"
    if has_lf:
        return "LF"
    if has_cr:
        return "CR"
    return "NONE"
