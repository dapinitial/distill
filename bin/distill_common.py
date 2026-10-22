"""Shared helpers for the distill scripts (stdlib only)."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path


def hms(seconds: float, hours: bool | None = None) -> str:
    """0 -> '00:00', 3725 -> '1:02:05'. Pass hours=True to force h:mm:ss."""
    s = max(0, int(round(seconds)))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if hours or h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def parse_hms(text: str) -> float:
    parts = [int(p) for p in text.strip().split(":")]
    total = 0
    for p in parts:
        total = total * 60 + p
    return float(total)


_QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "…": "..."}


def ascii_punct(text: str) -> str:
    for k, v in _QUOTES.items():
        text = text.replace(k, v)
    return text


_TOKEN_STRIP = re.compile(r"^[^\w$%]+|[^\w%]+$", re.UNICODE)


def norm_token(word: str) -> str:
    """Lowercase, straighten quotes, strip surrounding punctuation. Keeps inner apostrophes/hyphens."""
    w = ascii_punct(word).lower()
    w = _TOKEN_STRIP.sub("", w)
    return w


def norm_tokens(text: str) -> list[str]:
    out = []
    for raw in ascii_punct(text).split():
        t = norm_token(raw)
        if t:
            out.append(t)
    return out


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    if len(text) > max_len:
        text = text[:max_len].rsplit("-", 1)[0]
    return text or "untitled"


def find_transcript_dir(arg: str | os.PathLike) -> Path:
    """Accept a transcript folder, or any file inside one."""
    p = Path(arg).expanduser().resolve()
    if p.is_file():
        p = p.parent
    if not (p / "transcript.json").exists():
        raise FileNotFoundError(f"no transcript.json in {p}")
    return p


def load_transcript(folder: Path) -> dict:
    data = json.loads((folder / "transcript.json").read_text())
    src_path = folder / "source.json"
    if src_path.exists():
        data["source"] = json.loads(src_path.read_text())
    return data


def youtube_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def stamp(seconds: float, source: dict | None) -> str:
    """'[mm:ss]' or a markdown link that jumps to that second on YouTube."""
    label = hms(seconds)
    vid = youtube_id((source or {}).get("url"))
    if vid:
        return f"[{label}](https://www.youtube.com/watch?v={vid}&t={int(seconds)})"
    return f"[{label}]"
