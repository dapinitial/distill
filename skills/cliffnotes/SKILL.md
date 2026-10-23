---
name: cliffnotes
description: Turn a long video, podcast, talk or meeting recording into a five-minute read — the point, the argument with timestamped links, verbatim quotes verified against the transcript, decisions and numbers, and what's worth watching vs. safe to skip. Takes a transcript folder from /transcribe, or a file or link (it transcribes first). Use when the user says "cliff notes", "summarize this video", "TL;DW", "what's the gist of this talk", "do I need to watch this".
---

# /cliffnotes — transcript (or file or link) → cliffnotes.md

An hour of video becomes a five-minute read, and nothing in quotation marks is invented.

## 1. Get a transcript folder

- Input is a folder containing `transcript.json` → use it.
- Input is a file or URL → run `transcribe <input>` first (see the transcribe skill; it prints
  the folder). Pass along `--glossary` or `--slug` if the user gave names or a folder name.

Read `source.json` (title, url, duration, `low_confidence_words`, `dropped_suspect_segments`)
and `chunks.jsonl` (one section per line, each a few minutes with `start_hms`/`end_hms`, and a
`title` when the creator published chapter marks; use those titles, they are the speaker's own
structure).
`transcript.md` is the same text with `[mm:ss]` markers every paragraph; use it when you need a
time for a specific line.

## 2. Long transcripts: section by section first

If the video is over about 25 minutes or the transcript over about 6,000 words, do not try to
write the notes in one pass. First write `sections.md` in the transcript folder, one block per
chunk, in this shape (this is Contextual Retrieval applied to a transcript: the one-line header
situates each section in the whole):

```
## 3. [07:49–11:02] — About: the six vocal warm-ups he does before every talk
- [07:49] asks the audience to stand; frames warm-ups as owed to yourself before anything important
- [08:40] exercise list: arms up + sigh, lips "bop", "brrr", tongue "la", rolled R, the siren
- Quote candidates (copied exactly from the chunk text):
  - [08:46] "if I can only do one, the pros call this the siren"
- Numbers/decisions/to-dos: six exercises; do them before every talk
```

Work through every chunk in order (read the chunk text, write its block, move on). Then write
the cliff notes from `sections.md`, going back to `chunks.jsonl` only to copy quotes exactly.
For short videos, read all chunks and go straight to step 3.

## 3. Write `cliffnotes.md` in the transcript folder

Target 600–900 words, never more than 1,100 (`verify-quotes` warns). Format:

```markdown
# <Title>

<Source line: speaker/channel if known · duration · YouTube link or file path> · <N>-minute read

## The point
Three sentences. What is being argued or shown, why it matters, what the speaker wants you to do or believe.

## The meat
The argument as an outline, in the order it is made. Every item starts with a timestamp.
- [02:17](https://www.youtube.com/watch?v=ID&t=137) Claim or step, in your words.
  - sub-points only when the structure needs them

## Exact quotes
The 3–6 lines worth repeating, each a blockquote, each verbatim:
> "quote exactly as transcribed" — [05:05](...&t=305)

## Decisions, numbers, to-dos
- Only things said out loud: figures, dates, commitments, recommendations, "go do X". With timestamps.
- Write "None stated." if there are none. Do not infer.

## Worth watching
- [07:49–09:05](...&t=469) Why seeing this beats reading it (demo, live exercise, chart, tone that text loses).
(2–3 stretches)

## Safe to skip
- [00:00–00:14] intro / housekeeping / sponsor read / repeated recap, with a reason.

---
Transcribed locally (whisper.cpp large-v3-turbo, no speaker labels). Quotes verified word for word with verify-quotes.
```

Rules:
- **Timestamps** come from the chunk/paragraph markers or from `transcript.json` word times.
  For YouTube sources every timestamp is a link that jumps to that second:
  `[mm:ss](https://www.youtube.com/watch?v=<id>&t=<seconds>)`. Use `stamp <folder> 7:49`
  to print the marker rather than doing the arithmetic in your head. Non-YouTube sources get
  plain `[mm:ss]`.
- **Quotation marks mean verbatim.** Copy from the transcript text; never tidy, never
  paraphrase, never merge two sentences into one quote. Elide with `...` if you must skip words.
  Anything you reword goes outside quotes. This holds in every section, not only Exact quotes.
- Prefer the speaker's structure over yours. Keep the order they made the argument in.
- Treat `low_confidence_words` and anything in the first/last 20 seconds with suspicion;
  don't build a quote on them.
- Speaker labels exist only when transcribe ran with `--speakers` (numbered, not named). Without
  them, if two people talk, say "the host" / "the guest" from context and note that attribution
  is inferred. For meetings, ask for `--speakers` (or run `transcribe <file> --speakers`).
- The footer names what was and was not done: `with N speaker labels` or `no speaker labels`,
  and `transcript in <language>, notes in <language>` when they differ.

## 3a. Other languages

`source.json → language` is the spoken language. Write the notes in the language the user asked
for, or English when they did not say; a Spanish talk gets English notes by default, and an
English talk gets Spanish notes if asked. Only the quotes are different:

- **Quotes stay in the original language**, verbatim, inside straight double quotes, so
  `verify-quotes` can hold them to the transcript. Put the translation right after, in italics
  and outside the quotes: `> "No hay zombies en la escuela." *(There are no zombies at school.)* — [04:12](…)`.
  Never put a translation inside quotation marks; never translate inside a blockquote's quotes.
- Section titles, the point, the meat, decisions: translate freely, they are your words.
- The user wants to read the whole talk, not notes: write `translation.md` section by section
  from `chunks.jsonl`, keeping the `## n. [start–end] Title` structure and a `[mm:ss]` marker
  per paragraph, with a first line saying it is a translation and quotes cannot be verified
  against it. For a long talk, offer `captions-md <folder> --write` first: YouTube's English
  captions as timestamped markdown, no model involved, seconds instead of a long pass.

## 3b. Meeting mode

For a recording of a meeting, call, interview or voice memo (a local file, or the user says it is
a meeting), write `meeting.md` instead of `cliffnotes.md`, same verification rules:

```markdown
# <Title or "Meeting, <date>">
<source · duration · N-minute read>

## In one paragraph
What the meeting was for and what came out of it.

## Decisions
- [mm:ss] Decision as stated. Who stated it if the transcript makes that clear.

## Action items
- [mm:ss] Owner (or "unassigned") — what — by when (only if a date was said)

## Open questions
- [mm:ss] Question that was raised and not settled.

## Timeline
- [mm:ss] Topic, one line each, in order.

## Exact quotes
> "verbatim" — [mm:ss]
```

Attribution: without speaker labels, name people only when the transcript names them ("as Sam
said"); otherwise say "one participant". When `transcript.md` has `**Speaker 1:**` labels (the
`--speakers` option of transcribe), use them and say in the header that speakers were detected
automatically and numbered, not named, unless the user supplies names.

## 4. Verify, fix, repeat

```bash
verify-quotes <folder>/cliffnotes.md
```

It checks every double-quoted span of 4+ words against the transcript (in whatever language;
accents and guillemets are normalised), every `[mm:ss]` and `&t=` against the video length, that a quote's timestamp is within 20 s of where it was said,
that `[mm:ss]` and `t=` on the same line agree, and that links point at the right video.
For each FAIL it prints what to do (the real time, or the closest wording it found). Fix the
line or drop it, rerun, and only report the notes when it exits 0. Paste the final summary line
(`N quotes verified, 0 failed`) in your reply.

## 5. Render and publish the page

```bash
render <folder>            # <folder>/index.html, an Artifact-ready fragment
render <folder> --open     # local.html with an embedded player; opens in the browser
```

The page puts the cliff notes beside the full transcript: section jump list, search, every
timestamp a link into the video, and a "Copy selection for Claude" button that copies the
highlighted text as a quote with its timestamp and folder path, ready to paste into Claude Code.

Publish `index.html` with the Artifact tool (`file_path` = the folder's index.html, `icon`
"transcript", a one-sentence `description`). The artifact is private to the user's account and
becomes the shareable, navigable view; the markdown folder stays the source of truth. Leave a
comment on the artifact and the publishing session sees it, so a viewer can ask about a passage
from the page itself. Report the artifact link with the notes.

### Publish pending

`distill-batch --publish` cannot publish (no Artifact tool headless), so it lists finished folders in
`$DISTILL_OUT/publish-pending.txt`. When the user says "publish pending" (or you see that file is not
empty while doing other distill work), for each folder: publish `index.html` with the Artifact tool
(or republish with its `url` if `artifact.json` already exists), write `artifact.json`, remove the
line, then run `library`. Report the links.

`library` also writes `out/toc.html` and `out/library.json`. If `out/toc.artifact.json` exists,
republish `toc.html` to that `url` (with `files: {"library.json": "out/library.json"}`) so the
published table of contents lists the new pages; otherwise publish it once (icon "library") and
write `out/toc.artifact.json`. Report that link too.

## 6. Show the notes

Unattended runs: `distill-batch` calls this skill headlessly for each queued item and checks the
result with `verify-quotes`, so the rules above are the contract. Do the verification yourself
too; a run that skips it fails the batch.

Print `cliffnotes.md` in full in your reply (it is short by design), with the folder path and
the step timings from `source.json → timings_seconds` if you ran transcribe.
