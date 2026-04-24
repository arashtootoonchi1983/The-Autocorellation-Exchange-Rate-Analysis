"""Gradio app — upload a Persian law lecture MP3, get back a clean RTL transcript.

Run:
    python app.py

Environment:
    OPENAI_API_KEY       (required — Whisper transcription)
    ANTHROPIC_API_KEY    (required — Claude Q&A removal / formatting)
    WHISPER_MODEL        (optional, default: whisper-1)
    CLAUDE_MODEL         (optional, default: claude-opus-4-7)
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from persian_stt.docx_writer import write_rtl_docx
from persian_stt.postprocess import clean_transcript
from persian_stt.transcribe import (
    segments_as_dialogue,
    transcribe_file,
)

load_dotenv()


OUTPUT_DIR = Path(tempfile.gettempdir()) / "persian_stt_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def _write_text(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return str(path)


def process(
    audio_path: str | None,
    extra_vocab: str,
    skip_claude: bool,
    progress: gr.Progress = gr.Progress(track_tqdm=False),
):
    if not audio_path:
        raise gr.Error("لطفاً یک فایل صوتی (MP3/WAV/M4A) بارگذاری کنید.")
    if not os.environ.get("OPENAI_API_KEY"):
        raise gr.Error("کلید OPENAI_API_KEY تنظیم نشده است. ابتدا آن را در محیط تنظیم کنید.")
    if not skip_claude and not os.environ.get("ANTHROPIC_API_KEY"):
        raise gr.Error("کلید ANTHROPIC_API_KEY تنظیم نشده است. یا آن را تنظیم کنید یا گزینه «فقط رونویسی خام» را فعال کنید.")

    ts = time.strftime("%Y%m%d_%H%M%S")
    base = OUTPUT_DIR / f"lecture_{ts}"

    # ---- Stage 1: Whisper ----
    def whisper_progress(frac: float, msg: str) -> None:
        progress(frac * 0.6, desc=msg)

    tr = transcribe_file(
        audio_path,
        extra_vocab=extra_vocab or None,
        progress_cb=whisper_progress,
    )
    dialogue = segments_as_dialogue(tr.segments) or tr.text

    raw_txt_path = _write_text(Path(f"{base}_raw.txt"), dialogue)

    if skip_claude:
        progress(1.0, desc="پایان — فقط رونویسی خام.")
        raw_docx = write_rtl_docx(dialogue, f"{base}_raw.docx", title="رونویسی خام سخنرانی")
        return (
            dialogue,
            dialogue,
            [raw_txt_path, raw_docx],
        )

    # ---- Stage 2: Claude cleanup ----
    def claude_progress(frac: float, msg: str) -> None:
        progress(0.6 + frac * 0.4, desc=msg)

    cleaned = clean_transcript(dialogue, progress_cb=claude_progress)

    marked_txt = _write_text(Path(f"{base}_marked.txt"), cleaned.marked)
    clean_txt = _write_text(Path(f"{base}_clean.txt"), cleaned.clean)
    marked_docx = write_rtl_docx(
        cleaned.marked,
        f"{base}_marked.docx",
        title="رونویسی سخنرانی — با علامت‌گذاری سؤالات دانشجویان",
    )
    clean_docx = write_rtl_docx(
        cleaned.clean,
        f"{base}_clean.docx",
        title="رونویسی سخنرانی — فقط کلام مدرس",
    )

    progress(1.0, desc="تمام شد.")

    return (
        cleaned.marked,
        cleaned.clean,
        [clean_docx, clean_txt, marked_docx, marked_txt, raw_txt_path],
    )


# ---------- UI ----------

RTL_CSS = """
.rtl textarea, .rtl input, .rtl .prose { direction: rtl !important; text-align: right !important; font-family: "B Nazanin", "Vazirmatn", "Tahoma", serif !important; font-size: 16px !important; line-height: 2 !important; }
.rtl label { direction: rtl !important; text-align: right !important; }
#title { direction: rtl; text-align: right; font-family: "B Nazanin", "Vazirmatn", "Tahoma", serif; }
"""


with gr.Blocks(css=RTL_CSS, title="رونویس هوشمند سخنرانی حقوق") as demo:
    gr.Markdown(
        """
        # رونویس هوشمند سخنرانی‌های حقوق (فارسی + عربی)
        یک فایل صوتی سخنرانی بارگذاری کنید. خروجی شامل دو نسخه است:
        **علامت‌گذاری‌شده** (با برچسب `[سؤال دانشجو: …]`) و **نسخه پاک** (فقط صحبت مدرس).
        اصطلاحات فقهی و حقوقی عربی به صورت دقیق حفظ می‌شوند.
        """,
        elem_id="title",
    )

    with gr.Row():
        with gr.Column(scale=1):
            audio_in = gr.Audio(
                label="فایل سخنرانی (MP3 / WAV / M4A)",
                type="filepath",
                sources=["upload"],
            )
            extra_vocab = gr.Textbox(
                label="واژگان اختصاصی (اختیاری) — نام استاد، کتاب، ماده قانون",
                placeholder="مثال: دکتر کاتوزیان، ماده ۳۲۸ قانون مدنی، الزامات خارج از قرارداد",
                lines=2,
                elem_classes="rtl",
            )
            skip_claude = gr.Checkbox(
                label="فقط رونویسی خام (بدون ویرایش Claude) — سریع‌تر، اما سؤال دانشجویان حذف نمی‌شود",
                value=False,
            )
            run_btn = gr.Button("شروع رونویسی", variant="primary")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("نسخه پاک (فقط مدرس)"):
                    clean_box = gr.Textbox(
                        label="متن نهایی",
                        lines=25,
                        elem_classes="rtl",
                        show_copy_button=True,
                    )
                with gr.Tab("نسخه علامت‌گذاری‌شده"):
                    marked_box = gr.Textbox(
                        label="متن با برچسب سؤالات",
                        lines=25,
                        elem_classes="rtl",
                        show_copy_button=True,
                    )
            files_out = gr.Files(label="دانلود خروجی‌ها (.docx و .txt)")

    run_btn.click(
        process,
        inputs=[audio_in, extra_vocab, skip_claude],
        outputs=[marked_box, clean_box, files_out],
    )


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.environ.get("GRADIO_HOST", "127.0.0.1"),
        server_port=int(os.environ.get("GRADIO_PORT", "7860")),
        inbrowser=True,
    )
