# distill: a case study

2026-10-22. The shareable version with the pipeline diagram is a Claude Doc; this is the same text for the repo.

## The problem

An hour of talk holds about 9,000 words, and until now the only way to get at them was to spend the hour. More and more of what is worth knowing arrives as video and audio: conference talks, podcasts, lectures, recorded meetings, interviews. It is the slowest format there is to search, to quote, or to hand to a model as context.

For a person the cost is the hour itself, spent to find out whether the hour was worth spending. Skipping ahead loses the argument; a written summary from someone else cannot be checked without watching.

For an LLM agent the video is opaque. Claude Code or any other agent gets a title, maybe YouTube's auto-captions with no punctuation and no reliable timing, and a model-written summary whose quotation marks cannot be trusted, because models paraphrase inside them. Nothing in that chain can be verified, and a summary that cannot be verified cannot be used as context for anything that matters.

The existing options each miss. Cloud transcription uploads the recording (a non-starter for meetings), costs per minute, and still returns a wall of text. Reading YouTube's captions is free and unreadable. Asking a chat model to summarize a link yields a confident page with invented quotes and timestamps that point nowhere.

## What we set out to solve

The goal is to expand the knowledge a person or an agent can actually use, faster: an hour of video becomes a five-minute read that can be trusted, and the full transcript behind it becomes context any LLM can take. Better context produces better decisions, better tools and better products, so the bottleneck we attacked is the distance between what has been said and what can be read, searched and quoted.

That goal set five requirements before any code was written.

1. **Local and free.** Transcription runs on the Mac, nothing is uploaded, and the marginal cost of one more hour of video is electricity. Meetings and unreleased material qualify.
2. **Verifiable.** Anything inside quotation marks is word for word what was said, and every timestamp lands inside the video. A program proves it, not a reviewer.
3. **Agent first.** Most users will be LLM agents (Claude Code today, others later), so the product is a folder of plain files with word-level timing, not an app. People get a page rendered from the same folder.
4. **Deterministic where it can be.** Cleanup, sectioning and verification are code, because a transcript that changes each run cannot be quoted from. The model is used only where judgment is needed: deciding what matters.
5. **Five minutes.** The notes say the point, the argument with links into the video, the quotes worth keeping, the numbers and decisions said aloud, and what is worth watching versus safe to skip.

## What was built

Two chained Claude Code skills and a dozen small scripts, all in one repo, built in one day.

```
URL or file → yt-dlp → ffmpeg 16 kHz WAV → whisper.cpp (large-v3-turbo, Metal) → cleanup (code) → folder
folder → Claude writes the notes → verify-quotes (exit 1 on any failure) → render → Claude Artifact / MCP clients
```

The top line is deterministic and runs without a model; the bottom line is where Claude writes, and the verifier sends it back until every quote is real. Plain files are the handoff from code to model.

- **transcribe**: URL or file to a folder of `transcript.md` (sections, `[mm:ss]` markers), `transcript.json` (every word with its time and confidence), `chunks.jsonl` (one section per line, for retrieval) and `source.json` (metadata, timings, cleanup stats). Playlists, chapter marks as section titles, optional 720p video for frame grabs.
- **Cleanup rules in code**: fillers, doubled words and phrases, hallucinated subtitle credits on silent intros, phrases looped over applause, inline `[Music]`, and a glossary of preferred spellings (`wrong → right`) that can be per project. Every rule has a regression test.
- **cliffnotes**: the skill that writes the five-minute read, with `verify-quotes` holding it to the transcript. A long talk is first summarized section by section with a one-line "what this is about" per section (Contextual Retrieval applied to a transcript). Meetings get decisions, action items and a timeline instead.
- **Speaker labels**: local diarization (sherpa-onnx, pyannote segmentation plus TitaNet embeddings), numbered speakers, minor voices folded into their neighbours.
- **Languages**: Whisper identifies the language; the prompt, the cleanup tables and the captions follow it. Notes come out in English with quotes kept in the original language and verified; translations sit beside them in italics.
- **The page**: `render` puts the notes beside the full transcript with search, section jumps, timestamp links into the video, frame grabs, and a "copy selection for Claude" button. Published as a private Claude Artifact; the markdown folder stays the source of truth.
- **Library and search**: an index of everything transcribed, and `where --all` to find who said a phrase and when.
- **Unattended**: a queue file and `distill-batch`, which runs Claude Code headlessly per item and rejects notes that fail verification.
- **MCP server**: `distill-mcp` exposes the library, search, transcription jobs and a `write_notes` tool that verifies on save, so Claude Desktop or any MCP client is held to the same rule.

## Results

An hour of video becomes a verified five-minute read in about four minutes of machine time on an M1 Max, and every quote in every set of notes produced so far passed the verifier.

| Source | Length | Words | Whisper | Whole pipeline | Outcome |
| --- | --- | --- | --- | --- | --- |
| TED talk, one speaker | 9:58 | 1,661 | 22.6 s | 29.7 s | 8 quotes verified, 0 failed; published page |
| Karpathy, Intro to Large Language Models | 59:48 | 11,751 | 170.4 s | 180.6 s | 20 chapter-titled sections, section summaries first, 7 quotes verified; published page |
| TEDx talk in Spanish | 9:07 | 1,328 | 21.2 s | 31.2 s | language detected (p = 1.00), English notes, 7 Spanish quotes verified; published page |
| Interview clip, two voices | 9:01 | 1,817 | 24.9 s | 74.3 s (41.9 s diarization) | 16 raw voices folded to 3; clean 2-way split with `--speakers 2` |
| Synthetic stand-up, two voices | 0:43 | 143 | 5.4 s | 8.8 s | 5 turns labelled exactly; meeting notes, 3 quotes verified |

Whisper runs at 2.3 to 2.9 seconds per minute of audio; diarization on CPU adds about a tenth of real time. A rerun after a glossary edit takes under 3 seconds, because every step is cached, so fixing a misheard name is cheap. The unattended path (queue, headless Claude Code, verifier) turned a 10-minute talk into verified notes in about four minutes end to end. The cleanup rules carry 30 regression checks, all passing; the whole thing is about 3,000 lines of Python, shell and skill text across 16 commits in one day.

## What we learned

Every real video taught the pipeline a rule that the synthetic tests could not, and every rule became code with a regression check rather than an instruction to the model.

| Surprise | Where it showed | The fix |
| --- | --- | --- |
| Whisper invents subtitle credits on silent intros ("Reviewer: …", "Revisor: …"), learned from captioned training data | TED talk at 0:00 (low confidence); Spanish TEDx at 0:00 (confident) | Drop a first or last segment isolated by 5 s of silence when its confidence is under 0.15 or it reads like a credit |
| Whisper loops one phrase over applause: the same sentence 15 times in 15 seconds | Spanish TEDx, the final applause | A phrase of 2 to 12 words repeated 3 or more times is kept once; at the very end of a file it is dropped entirely |
| Whisper drops into lowercase, unpunctuated output for a whole file, which destroys sentences, sections and quotes | Two-voice interview clip | A short punctuated prompt in the spoken language, and a warning when a transcript has almost no sentence ends |
| Diarization split two people into 16 voices on crosstalk | Interview clip | Fold any voice under 5 s or 3% of speech into its neighbour; raise the clustering threshold to 0.6; `--speakers N` when the count is known |
| Glossary rules did not chain ("Lama" was fixed before "Llama 270b" could match) | Karpathy talk | Apply the glossary in up to three passes |
| A caption wildcard fetched dozens of auto-translations and YouTube rate-limited the audio download | Interview clip | Exact language codes only, captions fetched separately and best effort, a clear error naming the yt-dlp upgrade |
| The model paraphrased inside quotation marks, once by me while writing notes | TED talk notes | The verifier caught it; the rule "quotation marks mean verbatim" moved from the skill text into a program that exits 1 |
| large-v3-turbo returns the source language when asked to translate | Reading, before building the language layer | Translation is an LLM job in the notes step; quotes stay in the original language and verified, translations beside them in italics |
| Headless Claude Code has no Artifact tool and, correctly, refused to invent a URL | First unattended run | Finished folders queue in a pending file; an interactive session publishes them on request |
| Word-level timing is about a second off because flash attention disables Whisper's alignment | Setup | Accepted: a one-second error is invisible behind a timestamp link, and the verifier allows 20 s |

The general lesson: a transcript is a product the rest of the system depends on, so every change to it has to be deterministic and tested. The model is good at deciding what matters and bad at copying exactly, so the design gives it the first job and takes the second away from it.

## Design decisions

Each decision below was made once and then held, which is why the pieces built later (speakers, languages, batch, MCP) slotted in without changing the earlier ones.

- **Files, not a database.** A transcript is a folder of markdown and JSON. Any agent can read it with no client, grep works, git works, and the library index is regenerated from the folders. A database would have added a server and removed the ability to just open the file.
- **Code where determinism matters, the model only for judgment.** Cleanup never involves a model, so the same audio yields the same transcript every time and the verifier can be strict. The model reads and decides; it does not copy.
- **Verification is a program with an exit code.** "Quotation marks mean verbatim" is a rule in the skill text, but what enforces it is `verify-quotes` returning 1. The headless batch and the MCP server both call it, so every path to a finished set of notes goes through the same gate.
- **Markdown is the source of truth; the page is a view.** `render` produces the page from the folder and the Artifact is republished from it. Edits happen in the markdown, never on the page.
- **The Artifact is the human surface, the folder is the agent surface.** Artifacts are private by default, shareable with a link, and a comment on one reaches the session that published it. For an agent, the folder path plus the "copy selection for Claude" button closes the loop from reading back into a conversation.
- **Cache every step.** Download, audio, Whisper and diarization are reused on rerun, so changing a glossary line or a section rule costs seconds. This is what made tuning on real videos affordable.
- **No names in commits, nothing uploaded.** The repo holds code and glossaries; outputs are ignored by git. The only thing that leaves the Mac is a page the user chooses to publish.
- **No Electron, no app.** A browser page and a terminal were enough, and most users will be agents anyway.

## What is next

1. **Real meetings with three or more voices.** Diarization was tuned on one two-person clip. A panel or a phone recording may need `--speakers N` every time; the next real meeting is the test.
2. **Very long sources.** A three-hour podcast is about 36,000 words. Transcription and sectioning are fine; the notes pass becomes slow and expensive, so cache the per-section one-liners and make `sections.md` the deliverable for anything over two hours.
3. **More languages with tables.** Seven languages have filler and doubled-word tables; the rest get no filler removal. Japanese and Chinese have no spaces, so word-level timing there is per segment until a tokenizer is added.
4. **A full translation that is cheap.** `captions-md` gives YouTube's English captions in seconds; a model-written `translation.md` exists as a skill step but costs a full pass. A local translation model would make it free.
5. **yt-dlp drift.** YouTube changes a few times a year. The error message says what to do; a scheduled upgrade in the batch script would remove the surprise.
6. **Library growth.** At a few hundred transcripts the index page and the phrase search still work; tags by uploader and a title search are the first things to add, still as files.
7. **MCP in daily use.** The server works against a stdio client; the next step is a week of use from Claude Desktop to see which tools are actually called and which are never touched.
