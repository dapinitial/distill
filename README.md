# distill

An hour of video, distilled to five minutes of the good part.

Two Claude Code skills that chain:

- **transcribe**: a file or a link → an LLM-ready transcript. Local Whisper (whisper.cpp, large-v3-turbo on Metal), word-level timestamps, deterministic cleanup with a glossary, sections split at natural pauses.
- **cliffnotes**: a transcript (or a file or link, which it transcribes first) → a five-minute read: the point, the meat with timestamps that jump into the video, exact quotes verified against the transcript, decisions and numbers, what's worth watching and what's safe to skip.

Transcription and cleanup run on this Mac. The only thing that leaves it is the rendered page, if you choose to publish it as a private Claude Artifact.

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
transcribe "<playlist or channel url>" --playlist    # every entry, one folder each
transcribe "<url>" --video                           # keep 720p video so the page gets frame grabs
transcribe "<url>" --lang auto                       # any language Whisper knows; notes come out in English
captions-md out/<slug> --write                       # YouTube's English captions as timestamped markdown
glossary-suggest out/<slug>                          # names Whisper likely misheard, as glossary lines
render out/<slug> --open                             # the page, with an embedded player
library --open                                       # index of everything under out/
where --all "phrase"                                 # which talks said it, and when
```

Or in Claude Code: `/transcribe <link>` then `/cliffnotes <folder>`, or just `/cliffnotes <link>`.

### Unattended

Put links in `queue.txt` (one per line, playlists allowed) and run `distill-batch`. It transcribes
each item, runs the cliffnotes skill headlessly in Claude Code (`claude -p`), checks the result with
`verify-quotes`, refreshes the library and moves finished lines to `queue.done.txt`. Add `--publish`
to queue each finished page in `out/publish-pending.txt`; say "publish pending" in an interactive
Claude Code session to publish them as Artifacts (the Artifact tool is not available headless). Schedule it with cron, launchd, or a Claude Code routine:

```
0 6 * * *  cd ~/Sites/distill && direnv exec . bin/distill-batch >> out/cron.log 2>&1
```

Each transcript folder holds:

| file | what |
| --- | --- |
| `transcript.md` | readable, `[mm:ss]` markers, sections of a few minutes with start and end |
| `transcript.json` | every word with its start and end time |
| `chunks.jsonl` | one section per line, for section-by-section summarizing |
| `source.json` | title, URL, duration, model, cleanup stats, step timings |
| `cliffnotes.md` | written by the cliffnotes skill |
| `sections.md` | per-section notes written first for long videos |
| `index.html` / `local.html` | the rendered page (`render`); `index.html` is what gets published as a Claude Artifact |

## Scripts (`bin/`)

| script | job |
| --- | --- |
| `setup` | install tools, fetch and checksum the model, GPU load test |
| `transcribe` | the whole pipeline: yt-dlp → ffmpeg → whisper-cli → cleanup → sections → files. Caches every step; reruns take seconds |
| `verify-quotes` | proves every quoted span in `cliffnotes.md` is verbatim and every timestamp is inside the video; exit 1 on any failure, with a hint on how to fix each |
| `where` | find when a phrase was said, printed as a timestamp link |
| `stamp` | turn `7:49` or `469` into the `[07:49](…&t=469)` marker |
| `render` | one self-contained HTML page per transcript: notes beside the transcript, search, timestamp links, frame grabs when the video is present. `--open` adds an embedded player (YouTube or the local audio) that seeks from any timestamp and highlights the paragraph being spoken |
| `library` | `out/index.md` and `out/index.html`: every transcript with its date, length, the point, and links |
| `glossary-suggest` | three deterministic signals for misheard names: spelling clusters, disagreements with YouTube's captions, low-confidence words |
| `captions-md` | a captions track as timestamped markdown; the no-model way to read a foreign-language talk in English |
| `distill-batch` | queue runner for unattended transcribe → cliffnotes → verify → library |
| `test` | regression checks for the cleanup rules, sectioning, speakers and verify-quotes |
| `diarize` | who spoke when, as JSON; used by `transcribe --speakers` |
| `prune` | delete regenerable media and Whisper caches older than N days; text outputs stay |

## Sections

When the creator published chapter marks, those become the sections (snapped to sentence ends,
tiny chapters merged, huge ones split at pauses) and each section carries its chapter title.
Otherwise sections are cut at the longest pause between 90 seconds and 5 minutes, aiming for 3.

## Whisper settings that matter

Whisper is given a short punctuated initial prompt (`--prompt`), because without one it sometimes drops into lowercase, unpunctuated output for a whole file, which ruins sentence and section boundaries. transcribe warns when a transcript comes back with almost no sentence ends. The prompt is also the place to put names Whisper should expect.

## Cleanup is code, not a model

Whitespace, fillers (`um`, `uh`), doubled words and phrases, and Whisper's hallucinated credits on silent intros are handled by fixed rules in `bin/transcribe`. Names and jargon come from `glossary.txt`: one preferred spelling per line, or `wrong → right`. The repo glossary is merged with a `glossary.txt` in the current directory, so each project can keep its own. Because the transcript is a deterministic product, `verify-quotes` can hold the cliff notes to it word for word.

## Speaker labels

```bash
bin/setup --speakers                 # once: sherpa-onnx in .venv (needs cmake), two small ONNX models
transcribe meeting.m4a --speakers    # or --speakers 3 when you know the count
```

Speakers are detected locally (pyannote segmentation + TitaNet embeddings via sherpa-onnx, CPU, about a tenth of real time) and numbered in order of first appearance, never named. Crosstalk makes the clustering invent extra voices; anyone with under 5 seconds or 3% of the speech is folded into the neighbouring speaker, and `--speaker-threshold` (default 0.6; higher merges more) or `--speakers N` tunes the rest. Once a folder has `speakers.json`, reruns keep the labels. Paragraphs break on every speaker change and carry `**Speaker N:**`; `chunks.jsonl` text has the same labels inline. Words right at a turn boundary can land on the wrong side by a word or two, since Whisper's word times are only accurate to about a second. For meetings, the cliffnotes skill writes `meeting.md` (decisions, action items, open questions, timeline) instead of cliff notes.

## Other languages

`--lang auto` lets Whisper identify the language (about a second), and the rest of the pipeline follows: the punctuated prompt is given in that language, the filler and doubled-word tables switch (English, Spanish, French, German, Italian, Portuguese and Dutch have tables; anything else gets no filler removal rather than a wrong one), and the captions fetched are the spoken language's plus YouTube's English track. Translation happens in the cliffnotes step, because it is an LLM job: the notes come out in English (or whatever you ask for), while every quote stays in the original language, verbatim and verified, with the translation beside it in italics. `captions-md` turns the English captions into a timestamped read of the whole talk without any model. Whisper's own translate mode is not used: large-v3-turbo was fine-tuned for transcription only and returns the source language when asked to translate.

## Limits

Word times are Whisper's token offsets, accurate to about a second. Japanese and Chinese have no spaces, so they get one "word" per Whisper segment. Speaker detection is not run unless you ask for it.
