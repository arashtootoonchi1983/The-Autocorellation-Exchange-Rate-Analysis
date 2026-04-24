"""Whisper transcription with Persian/Arabic legal-domain biasing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

from openai import OpenAI

from .chunking import AudioChunk, chunk_audio

# Prompt biases Whisper toward correct spelling of Persian legal terminology
# and common Arabic juristic phrases encountered in tort / civil-liability
# (ضمان قهری) lectures. Keep under ~224 tokens per OpenAI guidance.
LEGAL_DOMAIN_PROMPT_FA = (
    "این فایل صوتی، سخنرانی درس حقوق مدنی و مسئولیت مدنی (ضمان قهری) است. "
    "اصطلاحات تخصصی شامل: اتلاف، تسبیب، مباشرت، ید ضمانی، ضمان قهری، "
    "مسئولیت مدنی، غصب، استیفا، تقصیر، رابطه سببیت، خسارت، دیه، ارش، "
    "قاعده لاضرر، قاعده اتلاف، قاعده تسبیب، قاعده من له الغنم فعلیه الغرم، "
    "المباشر ضامن و ان لم یتعمد، السبب اقوی من المباشر. "
    "عبارات عربی از قرآن، روایات و متون فقهی نیز در متن وجود دارد و باید "
    "با اعراب و املای صحیح نوشته شوند. علائم نگارشی فارسی (،؛؟!) رعایت شود."
)


@dataclass
class TranscriptSegment:
    start: float  # seconds, absolute (offset-adjusted across chunks)
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    text: str
    segments: list[TranscriptSegment] = field(default_factory=list)


def _client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. In PowerShell run:\n"
            "  $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','User')"
        )
    return OpenAI(api_key=key)


def _transcribe_chunk(
    client: OpenAI,
    chunk: AudioChunk,
    model: str,
    prompt: str,
) -> Transcript:
    with open(chunk.path, "rb") as fh:
        resp = client.audio.transcriptions.create(
            model=model,
            file=fh,
            language="fa",
            prompt=prompt,
            response_format="verbose_json",
            temperature=0.0,
        )
    offset = chunk.start_ms / 1000.0
    segments = [
        TranscriptSegment(
            start=float(s["start"]) + offset,
            end=float(s["end"]) + offset,
            text=s["text"].strip(),
        )
        for s in (resp.segments or [])
    ]
    return Transcript(
        language=resp.language or "fa",
        text=(resp.text or "").strip(),
        segments=segments,
    )


def transcribe_file(
    input_path: str,
    model: str | None = None,
    extra_vocab: str | None = None,
    progress_cb: Callable[[float, str], None] | None = None,
) -> Transcript:
    """Transcribe an MP3/WAV/M4A lecture. Returns a unified Transcript.

    `extra_vocab` is appended to the domain prompt — use it to add
    lecturer-specific names, cited statutes, or book titles.
    `progress_cb(fraction, message)` is invoked after each chunk.
    """
    model = model or os.environ.get("WHISPER_MODEL", "whisper-1")
    prompt = LEGAL_DOMAIN_PROMPT_FA
    if extra_vocab:
        prompt = f"{prompt} {extra_vocab.strip()}"

    client = _client()
    chunks = chunk_audio(input_path)
    if progress_cb:
        progress_cb(0.0, f"تقسیم فایل به {len(chunks)} بخش انجام شد.")

    merged_segments: list[TranscriptSegment] = []
    text_parts: list[str] = []
    rolling_prompt = prompt
    for i, ch in enumerate(chunks):
        if progress_cb:
            progress_cb(i / max(len(chunks), 1), f"در حال رونویسی بخش {i + 1}/{len(chunks)}…")
        tr = _transcribe_chunk(client, ch, model, rolling_prompt)
        merged_segments.extend(tr.segments)
        text_parts.append(tr.text)
        # Feed the tail of the previous transcript as additional context so
        # Whisper keeps spelling/style consistent across chunk boundaries.
        tail = tr.text[-400:]
        rolling_prompt = f"{prompt} {tail}" if tail else prompt

    if progress_cb:
        progress_cb(1.0, "رونویسی تمام بخش‌ها پایان یافت.")

    return Transcript(
        language="fa",
        text="\n".join(p for p in text_parts if p),
        segments=merged_segments,
    )


def segments_as_dialogue(segments: list[TranscriptSegment]) -> str:
    """Render segments as timestamped lines — feeds Claude's speaker-attribution step."""
    lines = []
    for s in segments:
        t = f"[{int(s.start // 60):02d}:{int(s.start % 60):02d}]"
        lines.append(f"{t} {s.text}")
    return "\n".join(lines)
