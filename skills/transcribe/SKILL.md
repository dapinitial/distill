---
name: transcribe
description: Turn a video or audio file, or a URL (YouTube and anything yt-dlp handles, playlists too), into an LLM-ready transcript with word-level timestamps and optional speaker labels, using local Whisper (whisper.cpp large-v3-turbo on Metal). Use when the user says "transcribe this", "get me the transcript", "what did they say in this video", or hands you a media file, meeting recording or video link. Output is a folder with transcript.md, transcript.json, chunks.jsonl and source.json. Nothing is uploaded.
---

# /transcribe — file or link → transcript folder

Everything is done by one script; your job is to run it, read what it reports, and hand back
the folder. Do not transcribe, clean up or "fix" wording yourself: the transcript must stay a
deterministic product of Whisper plus the rules in `bin/transcribe`, so quotes drawn from it can
be verified mechanically later.

## Run it

```bash
transcribe <file-or-url>                 # prints the output folder on stdout, progress on stderr
transcribe <url> --slug my-name          # choose the folder name
transcribe <file> --lang auto            # default is English
transcribe <file> --glossary names.txt   # extra glossary for this run (repeatable)
transcribe <url> --force                 # redo download, audio and Whisper (otherwise cached)
transcribe <playlist-url> --playlist     # every entry becomes its own folder
transcribe <url> --video                 # also keep 720p video so render can grab frames
transcribe <file> --no-chapters          # ignore chapter marks, cut at pauses only
transcribe <file> --speakers             # label speakers (numbered); --speakers 3 if you know the count
```

`transcribe` lives in this repo's `bin/`. From another project it is on PATH only if direnv has
loaded distill's `.envrc`; otherwise call it as `~/Sites/distill/bin/transcribe` (the skill
folder symlink resolves to `~/Sites/distill/skills/transcribe`, so `$(dirname "$(readlink -f
~/.claude/skills/transcribe)")/../bin/transcribe` also works). Output goes under `$DISTILL_OUT`
(default `~/Sites/distill/out`), one folder per source, named from the title.

Expect about 3 s of Whisper per minute of audio on an M1 Max (10-minute video ≈ 35 s all in,
1 hour ≈ 3–4 min). Reruns skip every cached step and finish in seconds, so changing the glossary
and rerunning is cheap.

## What the pipeline does

1. **Fetch**: URLs go through `yt-dlp` (audio only, best quality); local files are used as is.
2. **Audio**: `ffmpeg` → 16 kHz mono WAV.
3. **Whisper**: `whisper-cli` with `ggml-large-v3-turbo`, full JSON with per-token times,
   flash attention on Metal. Words are rebuilt from tokens, so every word has start and end.
4. **Deterministic cleanup** (code, never an LLM):
   - whitespace and stray punctuation;
   - fillers (`um`, `uh`) and stutters: doubled words and doubled 2–3 word phrases
     (`I I I think`, `you know you know`) collapse to one, except emphasis that Whisper
     punctuated (`No. No.`) and legitimate doubles (`that that`, `had had`, `very very`);
   - Whisper hallucinations on silence: an isolated first or last segment (≥ 5 s of silence
     around it) containing a word Whisper gave < 15 % probability is dropped and recorded in
     `source.json → cleanup.dropped_suspect_segments` (typical: subtitle credits before a talk,
     "thanks for watching" after it);
   - glossary: `glossary.txt` in the current directory and in the distill repo are merged.
     One preferred spelling per line (`ChatGPT`, `whisper.cpp`, `Claude Code`), or
     `wrong → right` for words Whisper mishears (`chat GPT → ChatGPT`). Matching is
     case-insensitive and can span several words.
5. **Sentences and sections**: sentences end at `.?!` or a pause over 2 s. When the source has
   chapter marks (YouTube chapters), sections follow them, snapped to sentence ends, with the
   chapter title on each section. Otherwise sections are cut at the longest pause between 90 s
   and 5 min, aiming for about 3 min. YouTube's own captions are saved in `media/` as a second
   opinion for `glossary-suggest`.
6. **Write** the folder:

| file | what |
| --- | --- |
| `transcript.md` | readable: title, source, duration; `## n. [start–end]` per section; a `[mm:ss]` marker at the start of each paragraph (`[h:mm:ss]` for sources over an hour) |
| `transcript.json` | `words`: every word with `start`/`end` in seconds; `sections` with times |
| `chunks.jsonl` | one section per line: `index, start, end, start_hms, end_hms, text, word_count` |
| `source.json` | title, url or path, duration, model, language, word and section counts, `cleanup` stats (incl. low-confidence words), `timings_seconds` per step |

Also left in the folder, gitignored: `media/` (download), `audio.wav`, `whisper.json`, `whisper.log`.

## Report back

After it finishes, tell the user:
- the folder path, duration, word and section counts, and the per-step timings
  (`source.json → timings_seconds`);
- anything dropped as a suspected hallucination, and the count of low-confidence words
  (`cleanup.low_confidence_words`, with times) so they can spot-check;
- names or terms that look misspelled. Run `glossary-suggest <folder>`: it prints candidate
  `wrong → right` lines from spelling clusters, caption disagreements and low-confidence words.
  Read them critically (captions are noisy), add the ones that are right to `glossary.txt` (the
  repo one for general terms, a `glossary.txt` in the user's project for its own names), and
  rerun transcribe (seconds, since Whisper is cached). Never edit the transcript files by hand.

## Speakers

Off by default. `--speakers` runs local diarization (sherpa-onnx; `bin/setup --speakers` once)
and writes `**Speaker N:**` at every change of voice in `transcript.md`, the same labels inline
in `chunks.jsonl`, and `speaker` on each word in `transcript.json`. Speakers are numbered by
first appearance, never named; if the user tells you who is who, say so in the notes rather than
editing the transcript. Use it for meetings, interviews and podcasts; a single-speaker talk gains
nothing. Expect a word or two to sit on the wrong side of a turn boundary.

## Limits

- Without `--speakers`, dialogue is one stream; say so if the user asks who said what.
- English by default; `--lang auto` works but the cleanup rules are tuned for English, and the
  word-splitting assumes spaces between words.
- Word times are Whisper's token offsets (DTW timing is off because flash attention is on);
  they are reliable to about a second, which is all the downstream link needs.
- Music, overlapping speech and heavy accents degrade like any Whisper run. The
  low-confidence list in `source.json` is the honest signal.
