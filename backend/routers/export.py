# backend/routers/export.py
from fastapi import APIRouter, HTTPException
import os, json, re
from typing import Optional

router = APIRouter()

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "outputs"))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")

# ---------- helpers ----------
def _pick_unicode_font() -> Optional[str]:
    """Return a path to a Unicode TTF font if we can find one locally."""
    candidates = [
        # project font (drop your own TTF here if you like)
        os.path.join(OUTPUT_DIR, "DejaVuSans.ttf"),
        os.path.join(os.path.dirname(HERE), "assets", "fonts", "DejaVuSans.ttf"),
        # common Windows fonts
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\arialuni.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\seguisym.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

# replace the most common “smart punctuation” with ASCII, as a last resort
SMART_MAP = {
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2018": "'",
    "\u2019": "'",
    "\u201C": '"',
    "\u201D": '"',
    "\u2026": "...",
    "\u00A0": " ",  # nbsp
}
def _ascii_sanitize(s: str) -> str:
    return "".join(SMART_MAP.get(ch, ch) for ch in s)

def _ff_path(p: str) -> str:
    """ffmpeg likes forward slashes even on Windows; also quote via concat file."""
    return p.replace("\\", "/")

# ---------- PDF EXPORT ----------
@router.post("/pdf")
def export_pdf(session_id: str):
    try:
        # fpdf2 supports add_font(..., uni=True)
        from fpdf import FPDF  # type: ignore
    except ImportError:
        raise HTTPException(status_code=503, detail="fpdf2 not installed. Run: pip install fpdf2")

    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "session not found")

    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)

    images = session.get("images", [])
    beats = session.get("beats", [])

    pdf_dir = os.path.join(OUTPUT_DIR, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{session_id}.pdf")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Try to register a Unicode font
    font_path = _pick_unicode_font()
    use_unicode = False
    if font_path:
        try:
            pdf.add_font("Uni", "", font_path, uni=True)
            pdf.set_font("Uni", size=14)
            use_unicode = True
        except Exception:
            # if add_font isn't supported (old PyFPDF), we’ll sanitize later
            pass

    if not use_unicode:
        # fall back to core font (Latin-1 only) and sanitize text below
        pdf.set_font("Arial", size=14)

    for i, beat in enumerate(beats, start=1):
        text = beat.get("text", "")
        if not use_unicode:
            text = _ascii_sanitize(text)

        pdf.add_page()
        pdf.multi_cell(0, 8, text)

        if i - 1 < len(images):
            img = images[i - 1]
            if os.path.exists(img):
                try:
                    pdf.ln(6)
                    pdf.image(img, w=170)
                except RuntimeError:
                    pass

    try:
        pdf.output(pdf_path)
    except UnicodeEncodeError as e:
        if use_unicode:
            raise HTTPException(500, f"PDF write failed unexpectedly: {e}")
        # sanitize everything and retry
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=14)
        for i, beat in enumerate(beats, start=1):
            pdf.add_page()
            pdf.multi_cell(0, 8, _ascii_sanitize(beat.get("text", "")))
            if i - 1 < len(images):
                img = images[i - 1]
                if os.path.exists(img):
                    try:
                        pdf.ln(6)
                        pdf.image(img, w=170)
                    except RuntimeError:
                        pass
        pdf.output(pdf_path)

    return {"pdf": pdf_path}

# ---------- VIDEO EXPORT (ffmpeg-python) ----------
@router.post("/video")
def export_video(session_id: str, fps: int = 24, per_scene_sec: float = 5.0):
    # lazy imports so app still boots if these aren't installed yet
    try:
        from gtts import gTTS
    except ImportError:
        raise HTTPException(status_code=503, detail="gTTS not installed. Run: pip install gTTS")

    try:
        import ffmpeg  # type: ignore
    except ImportError:
        raise HTTPException(status_code=503, detail="ffmpeg-python not installed. Run: pip install ffmpeg-python")

    # system ffmpeg must be on PATH
    def _check_ffmpeg_binary():
        import shutil
        if shutil.which("ffmpeg") is None:
            raise HTTPException(
                status_code=503,
                detail="FFmpeg binary not found on PATH. Install it (e.g., choco install ffmpeg) and restart the shell.",
            )
    _check_ffmpeg_binary()

    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "session not found")

    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)

    images = session.get("images", [])
    beats = session.get("beats", [])
    if not images:
        raise HTTPException(400, "no images available; render first")

    # 1) TTS narration
    narration_text = "\n".join([b.get("text", "") for b in beats])
    video_dir = os.path.join(OUTPUT_DIR, "video")
    os.makedirs(video_dir, exist_ok=True)
    audio_path = os.path.join(video_dir, f"{session_id}.mp3")
    tts = gTTS(narration_text)
    tts.save(audio_path)

    # 2) Build concat list file for images (with per-scene duration)
    #    Note: concat demuxer ignores 'duration' for the LAST entry, so repeat last file without duration.
    list_path = os.path.join(video_dir, f"{session_id}_inputs.txt")
    with open(list_path, "w", encoding="utf-8", newline="\n") as f:
        for img in images:
            if not os.path.exists(img):
                continue
            f.write(f"file '{_ff_path(img)}'\n")
            f.write(f"duration {per_scene_sec}\n")
        # repeat last file once to apply its duration
        if images:
            last = images[-1]
            if os.path.exists(last):
                f.write(f"file '{_ff_path(last)}'\n")

    # 3) Use ffmpeg to mux video+audio
    out_path = os.path.join(video_dir, f"{session_id}.mp4")
    try:
        video_in = ffmpeg.input(list_path, format="concat", safe=0)
        audio_in = ffmpeg.input(audio_path)

        # shortest=1 trims to the shorter of audio/video if they mismatch slightly
        stream = ffmpeg.output(
            video_in,
            audio_in,
            out_path,
            vcodec="libx264",
            acodec="aac",
            pix_fmt="yuv420p",
            r=fps,
            shortest=None,
            movflags="faststart",
        )
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"ffmpeg failed: {e.stderr.decode('utf-8', 'ignore') if hasattr(e, 'stderr') else str(e)}",
        )

    return {"video": out_path}
