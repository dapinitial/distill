# distill

An hour of video, distilled to five minutes of the good part.

Two Claude Code skills that chain:

- **transcribe**: a file or a link → an LLM-ready transcript. Local Whisper (whisper.cpp, large-v3-turbo on Metal), word-level timestamps, deterministic cleanup with a glossary, sections split at natural pauses.
- **cliffnotes**: a transcript (or a file or link, which it transcribes first) → a five-minute read: the point, the meat with timestamps that jump into the video, exact quotes verified against the transcript, decisions and numbers, what's worth watching and what's safe to skip.

Transcription and cleanup run on this Mac. The only thing that leaves it is the rendered page, if you choose to publish it as a private Claude Artifact.

## What it does

- **Any talk, in minutes, on your own machine.** A YouTube link, a playlist, a channel or a file on disk becomes a transcript with every word timed, then a page you can read in five minutes. An hour of video takes a few minutes on Apple Silicon. Nothing is uploaded to transcribe it.
- **Notes you can check.** Every quote in the notes is the speaker's exact words, proved against the transcript by a script before the page is built, and every timestamp jumps to that moment in the video. If a quote is off by a word, the page does not get made.
- **The whole talk, not just the summary.** The page puts the notes beside the full transcript: search, a section jump list, an embedded player that follows along, frame grabs when the video was kept, and long talks split into pages of about ten minutes' reading.
- **Claims flagged for a person to judge.** On request, the agent scans a talk for checkable claims (numbers, facts, causes, predictions), looks for sources, and suggests whether each one holds up, is disputed, is contradicted, is out of date, or couldn't be checked. The page lists them questionable first, and you make every call. See [Checking claims](#checking-claims).
- **Meetings as well as talks.** With speaker labels, a recording becomes decisions, action items and open questions instead of cliff notes.
- **Other languages.** Whisper hears the original; the notes come out in English with every quote kept in the original language beside its translation.
- **A library that grows.** Every talk lands in one index. `ask` finds which talks cover a question, `where` finds when a phrase was said, and the MCP server hands the whole library to Claude Desktop or any other client.
- **Runs without you.** Put links in a queue, or paste one into `distill-web` from your phone over Tailscale, and the batch transcribes, writes the notes, verifies them and renders the pages unattended.

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
library --serve                                      # toc.html + library.json on localhost, CORS open
where --all "phrase"                                 # which talks said it, and when
```

The library also comes as a table of contents meant for sharing: `out/toc.html` links only to the
published pages and the sources, and `out/library.json` is the same list for anything that fetches.
Publish `toc.html` as an Artifact with `library.json` beside it and you have one link for the whole
library. Private Artifacts cannot be embedded in an iframe or fetched from another site, so for a
page that needs to load the list itself, use `library --serve` (local) or host the two files anywhere.

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
| `ask` | which talks say something about a question, ranked across the library (BM25 over the sections, no model), as markdown with timestamp links ready for Claude Code |
| `distill-web` | a small server on the Mac: paste a link, it is queued and distilled, read the library; reach it from a phone over Tailscale |
| `stamp` | turn `7:49` or `469` into the `[07:49](…&t=469)` marker |
| `check-claims` | holds a fact-check scan (`claims.json`) to the transcript: every claim quotes the speaker word for word near its timestamp, every label but "couldn't check" cites a source, and no claim arrives already reviewed. The agent suggests; the person decides on the page |
| `render` | one self-contained HTML page per transcript: notes beside the transcript, search, timestamp links, a section jump list, frame grabs when the video is present. Talks over 4,000 words read a page at a time (about 2,500 words, never splitting a section); search covers every page, and `#s-N`, `#t-N` and `#p-N` links open the right page. `--open` adds an embedded player (YouTube or the local audio) that seeks from any timestamp and highlights the paragraph being spoken |
| `library` | `out/index.md` and `out/index.html` (every transcript with its date, length, the point, and links), plus `toc.html` and `library.json` for publishing and fetching; `--serve` puts them on localhost |
| `glossary-suggest` | three deterministic signals for misheard names: spelling clusters, disagreements with YouTube's captions, low-confidence words |
| `captions-md` | a captions track as timestamped markdown; the no-model way to read a foreign-language talk in English |
| `distill-batch` | queue runner for unattended transcribe → cliffnotes → verify → library |
| `test` | regression checks for the cleanup rules, sectioning, speakers and verify-quotes |
| `diarize` | who spoke when, as JSON; used by `transcribe --speakers` |
| `prune` | delete regenerable media and Whisper caches older than N days; text outputs stay |
| `distill-mcp` | the library as an MCP server for Claude Desktop and other clients; wraps the scripts above |

## From outside the terminal: MCP

```bash
bin/setup --mcp        # installs the SDK into .venv and prints the Claude Desktop config line
```

`distill-mcp` exposes the library to any MCP client: `library`, `read` (notes, a transcript section, sections, meeting notes, captions), `find` (a phrase across every transcript), `transcribe_start` / `transcribe_status` (the pipeline runs for minutes, so it is a job you poll), `write_notes` (saves cliff notes and runs `verify-quotes` on them, so a client that writes notes is held to the same word-for-word rule), and `render`. Each folder's files are also MCP resources (`distill://<slug>/cliffnotes.md`), and the cliffnotes skill is served as an MCP prompt so a client without the skill follows the same steps. Every tool shells out to the scripts in `bin/`; there is one implementation. Publishing a page as a Claude Artifact still needs Claude Code.

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

## From your phone: distill-web

Transcription runs on this machine on purpose (local Whisper on Metal, nothing uploaded), so the
machine is the server. `distill-web` is the page in front of it: a box for a link, the queue and the
batch's state, and the library with every page readable in place.

```
distill-web                  # http://127.0.0.1:8766/, this machine only
distill-web --tailscale      # the same on your Tailscale address, reachable from your other devices
```

Pasting a link appends it to `queue.txt` and starts `distill-batch --publish` if none is running; the
batch transcribes, writes the notes headlessly in Claude Code, verifies the quotes, renders the page
and queues it in `publish-pending.txt`. Pages are readable right away at `/<slug>/local.html`; say
"publish pending" in Claude Code when you want them as Artifacts too.

There is no login on the page, so bind it only to localhost or to Tailscale, which is the login. For
a link other people can use, put a Cloudflare Tunnel with Access in front of the localhost port.

## Ask the library

```
ask "how does she keep humidity up without a floor drain"
ask "front lever" --top 5 --json
```

`ask` ranks every section across every transcript against the words in the question and prints the
best passages as markdown: the talk, a timestamp link to the first matching word, the section title
and the matching sentence with the hits in bold. It is deterministic (BM25 plus a bonus for the words
appearing together), so it is a map of where to read, not an answer; paste it into Claude Code and
ask the question again with the passages in context, or call `read` on a section through the MCP
server, where `ask` is also a tool.

## Other languages

`--lang auto` lets Whisper identify the language (about a second), and the rest of the pipeline follows: the punctuated prompt is given in that language, the filler and doubled-word tables switch (English, Spanish, French, German, Italian, Portuguese and Dutch have tables; anything else gets no filler removal rather than a wrong one), and the captions fetched are the spoken language's plus YouTube's English track. Translation happens in the cliffnotes step, because it is an LLM job: the notes come out in English (or whatever you ask for), while every quote stays in the original language, verbatim and verified, with the translation beside it in italics. `captions-md` turns the English captions into a timestamped read of the whole talk without any model. Whisper's own translate mode is not used: large-v3-turbo was fine-tuned for transcription only and returns the source language when asked to translate.

## Checking claims

Ask for it in Claude Code ("check the claims in this talk") and the cliffnotes skill does a second pass:

1. The agent reads the transcript for claims a source could settle: a number, a fact, a cause, a prediction. Opinions and jokes are left alone.
2. For each one it looks for evidence, preferring the paper, the dataset or the announcement over write-ups about them, and suggests a label: **supported**, **disputed** (credible sources disagree), **contradicted** (the evidence says otherwise), **outdated** (true when said, not now) or **couldn't check**.
3. It writes `claims.json`: the speaker's exact words, the time they said them, the claim in one line, why it suggests that label, and the sources with what each one says.
4. `check-claims` holds that file to the same standard as the notes. Every quote has to be verbatim in the transcript within 20 seconds of its timestamp, every label but "couldn't check" needs a source, and no claim may arrive already decided. If anything fails, the panel isn't built.
5. `render` adds a **Claims to review** panel to the page, contradicted first and supported last. Each claim links to the moment in the video and the paragraph in the transcript. You choose **Agree**, **Disagree** or **Needs a closer look** and can add a note.

Your decisions save to the published page's own storage (publish it with the `db` and `user` capabilities), and the header counts how many you have reviewed. Claude can read them back to fix the notes where you agreed; it never records a decision for you. The local copy shows the panel but keeps the buttons off, since there is nowhere to save.

The labels are suggestions from a web search on the day it ran. A "contradicted" can be a transcription error rather than the speaker's: a number Whisper misheard looks exactly like a wrong number, so listen at the timestamp before you agree.

## Decisions, and why

**Transcribe locally.** Talks and especially meetings are often private, and a cloud transcription service would see all of it. whisper.cpp on Metal is fast enough that the trade costs nothing: an hour of audio in a few minutes, with no account, no per-minute bill and no upload.

**Cleanup is code, not a model.** A model asked to tidy a transcript also rewords it, quietly. Fixed rules (fillers, doubled words, a glossary for names) give the same transcript every time, and that is what lets a script prove the quotes.

**Quotes are proved, not trusted.** Summaries that misquote are the main way this kind of tool goes wrong, and a reader can't tell a real quote from a plausible one. `verify-quotes` and `check-claims` match every quote word for word against the timed transcript and refuse to pass anything that doesn't match. The model writes; the scripts check.

**The person makes the call.** The claims scan is there to surface what deserves a second look, not to rule on what's true. A model with a web search is confidently wrong often enough, and a talk can be mistranscribed, so nothing is marked false and set aside without someone reviewing it. The agent finds and explains; the person decides, and the decision stays theirs.

**Timestamps everywhere.** Every point in the notes links to the moment it was said, so you can always check the notes against the speaker in one click instead of taking them on faith.

**The whole transcript ships with the notes.** A summary chooses what matters; keeping the full text beside it, searchable, means you can disagree with that choice.

**Two skills that chain, and plain scripts underneath.** `/transcribe` is useful on its own, and so is every script in `bin/`. The skills tell Claude what to do; the scripts do the parts that must come out the same every time. The MCP server and `distill-web` shell out to the same scripts, so there is one implementation.

**Pages are single files, published privately.** A rendered page carries everything it needs, so it works from disk, from the local server or as a private Claude Artifact, and it is shared only if you share it.

**The Mac is the server.** Because transcription is local, the machine doing it serves the pages too. `distill-web` binds to localhost or Tailscale only, since it has no login of its own; nothing listens on the open internet.

**No names in the history.** Commits describe what changed, not who said what in which talk. Outputs in `out/` are gitignored.

## Limits

Word times are Whisper's token offsets, accurate to about a second. Japanese and Chinese have no spaces, so they get one "word" per Whisper segment. Speaker detection is not run unless you ask for it.

## License

MIT. The models it downloads (whisper.cpp ggml, pyannote, TitaNet) carry their own licenses.
