"""Split long audio at silence boundaries so Whisper never cuts mid-word."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

WHISPER_SIZE_LIMIT_BYTES = 24 * 1024 * 1024  # keep 1 MB safety margin under 25 MB
TARGET_CHUNK_MS = 10 * 60 * 1000  # 10-minute target chunks
MAX_CHUNK_MS = 15 * 60 * 1000     # hard ceiling per chunk


@dataclass
class AudioChunk:
    path: str
    start_ms: int
    end_ms: int


def _find_cut_points(audio: AudioSegment, target_ms: int, max_ms: int) -> list[int]:
    """Return cut points (ms) that fall inside silent gaps when possible."""
    total = len(audio)
    if total <= max_ms:
        return [total]

    nonsilent = detect_nonsilent(
        audio,
        min_silence_len=700,
        silence_thresh=audio.dBFS - 16,
        seek_step=50,
    )
    silence_mids: list[int] = []
    prev_end = 0
    for start, end in nonsilent:
        if start > prev_end:
            silence_mids.append((prev_end + start) // 2)
        prev_end = end
    if prev_end < total:
        silence_mids.append((prev_end + total) // 2)

    cuts: list[int] = []
    cursor = 0
    while total - cursor > max_ms:
        window_lo = cursor + target_ms - 60_000
        window_hi = cursor + max_ms
        candidates = [s for s in silence_mids if window_lo <= s <= window_hi]
        cut = candidates[len(candidates) // 2] if candidates else cursor + target_ms
        cut = min(cut, window_hi)
        cuts.append(cut)
        cursor = cut
    cuts.append(total)
    return cuts


def chunk_audio(input_path: str, work_dir: str | None = None) -> list[AudioChunk]:
    """Return a list of chunk files that each fit under Whisper's size limit."""
    work_dir = work_dir or tempfile.mkdtemp(prefix="persian_stt_chunks_")
    os.makedirs(work_dir, exist_ok=True)

    src_size = os.path.getsize(input_path)
    audio = AudioSegment.from_file(input_path)

    # Normalise to 16 kHz mono — Whisper downsamples anyway, and this
    # shrinks bitrate so we stay under 25 MB even for long lectures.
    audio = audio.set_frame_rate(16_000).set_channels(1)

    if src_size <= WHISPER_SIZE_LIMIT_BYTES and len(audio) <= MAX_CHUNK_MS:
        out = str(Path(work_dir) / "chunk_00.mp3")
        audio.export(out, format="mp3", bitrate="64k")
        return [AudioChunk(path=out, start_ms=0, end_ms=len(audio))]

    cut_points = _find_cut_points(audio, TARGET_CHUNK_MS, MAX_CHUNK_MS)
    chunks: list[AudioChunk] = []
    start = 0
    for i, end in enumerate(cut_points):
        segment = audio[start:end]
        out = str(Path(work_dir) / f"chunk_{i:02d}.mp3")
        segment.export(out, format="mp3", bitrate="64k")
        # If a chunk still exceeds the size limit, re-encode at lower bitrate.
        if os.path.getsize(out) > WHISPER_SIZE_LIMIT_BYTES:
            segment.export(out, format="mp3", bitrate="48k")
        chunks.append(AudioChunk(path=out, start_ms=start, end_ms=end))
        start = end
    return chunks
