# distill

An hour of video, distilled to five minutes of the good part.

Two Claude Code skills that chain:

- **transcribe**: a file or a link → an LLM-ready transcript. Local Whisper (whisper.cpp, large-v3-turbo), word-level timestamps, deterministic cleanup with a glossary, sections split at natural pauses.
- **cliffnotes**: a transcript (or a file or link, which it transcribes first) → a five-minute read: the point, the meat with timestamps, exact quotes verified against the transcript, decisions and numbers, what's worth watching and what's safe to skip.

Everything runs on this Mac. Nothing is uploaded.
