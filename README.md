# distill

An hour of video, distilled to five minutes of the good part.

Two Claude Code skills that chain:

- **transcribe**: a file or a link → an LLM-ready transcript. Local Whisper (whisper.cpp, large-v3-turbo on Metal), word-level timestamps, deterministic cleanup with a glossary, sections split at natural pauses.
- **cliffnotes**: a transcript (or a file or link, which it transcribes first) → a five-minute read: the point, the meat with timestamps that jump into the video, exact quotes verified against the transcript, decisions and numbers, what's worth watching and what's safe to skip.

Everything runs on this Mac. Nothing is uploaded.

## Setup

```bash
cd ~/Sites/distill
direnv allow          # puts bin/ on PATH, sets DISTILL_MODEL, DISTILL_MODELS, DISTILL_OUT
bin/setup             # brew ffmpeg + whisper.cpp + yt-dlp, download the 1.6 GB model, prove it loads on the GPU
```

The model lives in `models/` (gitignored). Outputs land in `out/<slug>/` (gitignored). Override either with `.env`.

## Install the skills

Symlink both skill folders into `~/.claude/skills/` so `/transcribe` and `/cliffnotes` work from any project:

```bash
ln -sfn ~/Sites/distill/skills/transcribe ~/.claude/skills/transcribe
ln -sfn ~/Sites/distill/skills/cliffnotes ~/.claude/skills/cliffnotes
```

Symlinks, not copies, so editing `skills/*/SKILL.md` here updates them everywhere. The scripts in `bin/` are on PATH when direnv has loaded this repo; from elsewhere, call them by path (`~/Sites/distill/bin/transcribe`).

## Use

```bash
transcribe "https://www.youtube.com/watch?v=..."     # or a local .mp4/.m4a/.wav
transcribe talk.mp4 --glossary names.txt --slug talk
```

Or in Claude Code: `/transcribe <link>` then `/cliffnotes <folder>`, or just `/cliffnotes <link>`.

Each transcript folder holds:

| file | what |
| --- | --- |
| `transcript.md` | readable, `[mm:ss]` markers, sections of a few minutes with start and end |
| `transcript.json` | every word with its start and end time |
| `chunks.jsonl` | one section per line, for section-by-section summarizing |
| `source.json` | title, URL, duration, model, cleanup stats, step timings |
| `cliffnotes.md` | written by the cliffnotes skill |

## Scripts (`bin/`)

| script | job |
| --- | --- |
| `setup` | install tools, fetch and checksum the model, GPU load test |
| `transcribe` | the whole pipeline: yt-dlp → ffmpeg → whisper-cli → cleanup → sections → files. Caches every step; reruns take seconds |
| `verify-quotes` | proves every quoted span in `cliffnotes.md` is verbatim and every timestamp is inside the video; exit 1 on any failure, with a hint on how to fix each |
| `where` | find when a phrase was said, printed as a timestamp link |
| `stamp` | turn `7:49` or `469` into the `[07:49](…&t=469)` marker |

## Cleanup is code, not a model

Whitespace, fillers (`um`, `uh`), doubled words and phrases, and Whisper's hallucinated credits on silent intros are handled by fixed rules in `bin/transcribe`. Names and jargon come from `glossary.txt`: one preferred spelling per line, or `wrong → right`. The repo glossary is merged with a `glossary.txt` in the current directory, so each project can keep its own. Because the transcript is a deterministic product, `verify-quotes` can hold the cliff notes to it word for word.

## v1 limits

No speaker labels. English by default (`--lang auto` works, cleanup rules are tuned for English). Word times are Whisper's token offsets, accurate to about a second.
