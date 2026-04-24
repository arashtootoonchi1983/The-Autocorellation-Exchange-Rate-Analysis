# Persian Lecture Transcriber — رونویس هوشمند سخنرانی حقوق

A standalone desktop/web app that turns a Persian law-lecture MP3 into a clean,
right-to-left Persian transcript with:

- **Whisper** for transcription (Persian language hint + legal-domain prompt bias)
- **Claude Opus 4.7** for removing student questions, structuring paragraphs,
  and preserving Arabic juristic phrases (`المباشر ضامن و ان لم یتعمد`, etc.) verbatim
- **Gradio** for a simple browser UI
- **python-docx** for an RTL Word document output

## Two outputs per lecture

1. **Marked** — every student interruption is wrapped like `[سؤال دانشجو: …]` so you can verify
2. **Clean** — lecturer-only prose, stitched smoothly around the removed questions

Both are produced as `.txt` and RTL `.docx` (Persian font: *B Nazanin*, install on Windows or substitute *Vazirmatn*).

## Setup (Windows / PowerShell)

Prerequisites:

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` (required by `pydub` to decode MP3)

```powershell
cd persian_lecture_transcriber
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your API keys (these commands read them from your persisted Windows user environment):

```powershell
$env:OPENAI_API_KEY    = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','User')
$env:ANTHROPIC_API_KEY = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY','User')
```

If you prefer, copy `.env.example` to `.env` and fill the keys there — `app.py` loads it automatically.

## Run

```powershell
python app.py
```

A browser tab opens at `http://127.0.0.1:7860`. Upload an MP3, optionally type lecturer-specific vocabulary (names, cited statutes), then click **شروع رونویسی**.

## How it works

1. **Chunking** (`persian_stt/chunking.py`) — if the file exceeds 25 MB (Whisper's hard limit) or 15 minutes, it is downsampled to 16 kHz mono and split at the nearest **silence gap** so no word is cut mid-utterance.
2. **Transcription** (`persian_stt/transcribe.py`) — each chunk is sent to `whisper-1` with `language="fa"`, `temperature=0`, and a domain prompt listing tort-law terms (اتلاف، تسبیب، ید ضمانی…) and common fiqh maxims. The previous chunk's tail is rolled into the next chunk's prompt for stylistic continuity.
3. **Cleanup** (`persian_stt/postprocess.py`) — the timestamped transcript is passed to `claude-opus-4-7` with a system prompt that instructs it to (a) identify student turns, (b) produce both marked and clean versions, (c) preserve Arabic phrases verbatim, (d) fix only obvious Persian spelling errors, and (e) not invent citations. For long lectures the transcript is chunked at ~18k chars, with the prior chunk's tail passed as continuity context.
4. **Export** (`persian_stt/docx_writer.py`) — writes RTL paragraphs with `w:bidi` and `w:rtl` set at paragraph and run level so the file opens correctly in Word / LibreOffice.

## Cost notes

- Whisper API: USD $0.006 / minute of audio.
- Claude Opus 4.7: priced per input/output tokens. A 60-minute lecture typically produces ~30k transcript tokens → one Opus pass is usually enough, sometimes two if the speaker is very dense.

## Files

```
persian_lecture_transcriber/
├── app.py                       # Gradio entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── persian_stt/
    ├── __init__.py
    ├── chunking.py              # silence-based MP3 splitter
    ├── transcribe.py            # Whisper wrapper w/ legal-domain prompt
    ├── postprocess.py           # Claude Q&A removal + paragraph formatting
    └── docx_writer.py           # RTL Word exporter
```

## Security

`.env` and all audio files are gitignored. **Never** commit API keys. If a key is accidentally exposed, revoke it immediately at <https://platform.openai.com/api-keys> or <https://console.anthropic.com/settings/keys>.
