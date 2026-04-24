"""Claude-based cleanup: remove student questions, structure paragraphs,
preserve Arabic legal phrases, apply Persian punctuation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable

from anthropic import Anthropic

# Feed the model segment-by-segment text with coarse timestamps. This lets
# Claude reason about speaker turns (lecturer vs. student Q&A) without trying
# to guess diarization from raw prose.
SYSTEM_PROMPT = """You are a meticulous Persian-language legal editor preparing clean transcripts of university law lectures (tort / civil liability / ضمان قهری).

Your job on each chunk:
1. Treat the input as a raw Whisper transcript of one speaker primarily (the lecturer), but interrupted occasionally by students asking questions or making comments.
2. Identify student turns. Heuristics: short second-person or first-person questions ("استاد ببخشید…", "یک سوال دارم…", "یعنی اگر…؟"), requests for repetition, off-topic remarks, back-channel utterances. The lecturer's own rhetorical questions are NOT student turns — they are followed by the lecturer answering themselves.
3. Produce TWO outputs, delimited exactly by the tags shown below:
   <MARKED>…</MARKED>  — the full content with student turns wrapped like [سؤال دانشجو: …] and the lecturer's reply continuing normally.
   <CLEAN>…</CLEAN>   — lecturer-only prose, with ALL student turns removed (and the lecturer's words stitched smoothly around the gaps — no "as I was saying" filler).

Rules for BOTH outputs:
- Write right-to-left Persian. Use correct Persian punctuation: ، ؛ ؟ ! « » and the Persian comma/semicolon (not ASCII).
- Preserve EVERY Arabic phrase verbatim: Qur'anic verses, hadith, fiqh maxims (e.g. «المباشر ضامن و ان لم یتعمد»، «السبب اقوی من المباشر»، «لا ضرر و لا ضرار فی الاسلام»). Keep their original Arabic orthography and any diacritics Whisper captured. Do NOT transliterate Arabic into Persian spelling.
- Fix obvious Whisper spelling errors in Persian legal terminology (اتلاف، تسبیب، مباشرت، ید ضمانی، ضمان قهری، رابطه سببیت، قاعده لاضرر، etc.). Do not paraphrase — only correct.
- Break the lecturer's speech into well-structured paragraphs by topic shift. Each paragraph 3–8 sentences. No bullet lists unless the lecturer explicitly enumerates.
- Do NOT summarise, shorten, or add content the lecturer did not say.
- Do NOT invent citations, case names, or article numbers. If Whisper's output is garbled for a citation, keep it as-is and wrap in [نامفهوم: …] so the user can verify.
- Keep the lecturer's voice (first-person, teaching register). Don't convert to third-person.

Output ONLY the two tagged sections, nothing else. No preamble, no explanation."""


USER_TEMPLATE_FIRST = """این، بخش {idx} از {total} رونویسی خام یک سخنرانی حقوقی است. طبق دستور سیستم، دو خروجی <MARKED> و <CLEAN> تولید کن.

رونویسی خام (با برچسب زمانی هر جمله):
<TRANSCRIPT>
{body}
</TRANSCRIPT>"""


USER_TEMPLATE_CONT = """این، بخش {idx} از {total} است. برای حفظ پیوستگی، چند جمله پایانی بخش قبلی را می‌بینی (فقط جهت زمینه — دوباره تولید نکن):

<PREV_TAIL>
{prev_tail}
</PREV_TAIL>

رونویسی خام بخش جدید:
<TRANSCRIPT>
{body}
</TRANSCRIPT>"""


@dataclass
class CleanedOutput:
    marked: str   # lecturer + [سؤال دانشجو: …] tags
    clean: str    # lecturer only


def _client() -> Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. In PowerShell run:\n"
            "  $env:ANTHROPIC_API_KEY = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY','User')"
        )
    return Anthropic(api_key=key)


_TAG_RE = re.compile(
    r"<MARKED>\s*(?P<marked>.*?)\s*</MARKED>\s*<CLEAN>\s*(?P<clean>.*?)\s*</CLEAN>",
    re.DOTALL,
)


def _parse(response_text: str) -> tuple[str, str]:
    m = _TAG_RE.search(response_text)
    if not m:
        # Fallback: treat whole response as clean output so we don't lose work.
        return response_text.strip(), response_text.strip()
    return m.group("marked").strip(), m.group("clean").strip()


def _split_into_chunks(dialogue: str, max_chars: int = 18_000) -> list[str]:
    """Split timestamped dialogue by line, packing up to max_chars per chunk
    without breaking a line. 18k chars ≈ comfortably within Claude's window
    while leaving room for the generated output."""
    lines = dialogue.splitlines()
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        add = len(line) + 1
        if size + add > max_chars and buf:
            chunks.append("\n".join(buf))
            buf = [line]
            size = add
        else:
            buf.append(line)
            size += add
    if buf:
        chunks.append("\n".join(buf))
    return chunks or [""]


def clean_transcript(
    dialogue: str,
    model: str | None = None,
    max_tokens_per_call: int = 16_000,
    progress_cb: Callable[[float, str], None] | None = None,
) -> CleanedOutput:
    """Run the Claude cleanup pass over a (possibly long) timestamped transcript.

    Returns both the marked and clean versions as single strings.
    """
    model = model or os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
    client = _client()

    chunks = _split_into_chunks(dialogue)
    marked_parts: list[str] = []
    clean_parts: list[str] = []
    prev_tail = ""

    for i, body in enumerate(chunks, start=1):
        if progress_cb:
            progress_cb((i - 1) / len(chunks), f"ویرایش هوشمند بخش {i}/{len(chunks)} با Claude…")

        if i == 1:
            user = USER_TEMPLATE_FIRST.format(idx=i, total=len(chunks), body=body)
        else:
            user = USER_TEMPLATE_CONT.format(
                idx=i, total=len(chunks), prev_tail=prev_tail, body=body
            )

        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens_per_call,
            temperature=0.0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
        marked, clean = _parse(text)
        marked_parts.append(marked)
        clean_parts.append(clean)
        prev_tail = clean[-600:]

    if progress_cb:
        progress_cb(1.0, "ویرایش هوشمند کامل شد.")

    return CleanedOutput(
        marked="\n\n".join(p for p in marked_parts if p),
        clean="\n\n".join(p for p in clean_parts if p),
    )
