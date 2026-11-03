"""
ماژول اختصاصی تدوین ویدیوی ریلز آژانس دستیار ویرا
شامل متحرک‌سازی تصاویر (Ken Burns / Zoom-Pan)، موتور صوتی دو مرحله‌ای
و مسترینگ استودیویی صدای گوینده فارسی با فیلترهای اکولایزر و کمپرسور FFmpeg
"""
import asyncio
import base64
import json
import logging
import os
import subprocess
import shutil
import urllib.request
import urllib.error

log = logging.getLogger(__name__)


def _resolve_ffmpeg_path() -> str:
    """پیدا کردن مسیر اجرایی FFmpeg روی سیستم یا کتابخانه imageio_ffmpeg"""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FFMPEG = _resolve_ffmpeg_path()


async def _synth_gemini_audio(text: str, api_key: str, out_path: str) -> bool:
    """تلاش اول: تولید صدای نریشن با مدل صوتی Gemini در صورت پشتیبانی"""
    if not api_key:
        return False
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"Read the following Persian text clearly and naturally:\n\n{text}"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Puck"
                        }
                    }
                }
            }
        }
        
        def _call_gemini_tts():
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

        data = await asyncio.to_thread(_call_gemini_tts)
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            for part in parts:
                inline_data = part.get("inlineData") or {}
                if "data" in inline_data:
                    raw_audio = base64.b64decode(inline_data["data"])
                    with open(out_path, "wb") as f:
                        f.write(raw_audio)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                        log.info("Gemini TTS synthesis succeeded for scene.")
                        return True
    except Exception as e:
        log.info("Gemini TTS not available or returned error (%s). Falling back to Edge-TTS.", e)
    return False


async def _synth_edge_audio(text: str, voice: str, out_path: str, rate: str = "-3%", pitch: str = "-2Hz") -> bool:
    """تلاش دوم: تولید صدای باکیفیت و روان با Edge-TTS مایکروسافت"""
    try:
        import edge_tts
        target_voice = voice or "fa-IR-FaridNeural"
        comm = edge_tts.Communicate(text, target_voice, rate=rate, pitch=pitch)
        await asyncio.wait_for(comm.save(out_path), timeout=35)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 800
    except Exception as e:
        log.warning("Edge-TTS synthesis error: %s", e)
        return False


def _apply_studio_audio_mastering(raw_audio_path: str, mastered_audio_path: str) -> bool:
    """
    اعمال فیلترهای استودیویی FFmpeg روی صدای نریشن:
    ۱. highpass=f=85: حذف پاپ‌ها و نویزهای باد و فرکانس‌های زائد پایین
    ۲. equalizer: تقویت گرمای صدای گوینده در فرکانس‌های ۱۸۰ و ۲۵۰۰ هرتز
    ۳. lowpass=f=10500: حذف زبری و رباتیک بودن صدا
    ۴. acompressor: یکنواخت‌سازی بلندی کلمات
    ۵. loudnorm: استانداردسازی حجم صدا برای ریلز اینستاگرام
    """
    if not os.path.exists(raw_audio_path) or os.path.getsize(raw_audio_path) < 500:
        return False

    af_chain = (
        "highpass=f=85,"
        "equalizer=f=180:t=q:w=1.2:g=2.5,"
        "equalizer=f=2600:t=q:w=1.0:g=1.8,"
        "lowpass=f=10500,"
        "acompressor=threshold=-18dB:ratio=3:attack=15:release=120:makeup=2.5dB,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    cmd = [
        FFMPEG, "-y", "-i", raw_audio_path,
        "-af", af_chain,
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        mastered_audio_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(mastered_audio_path) and os.path.getsize(mastered_audio_path) > 500:
        return True
    
    # در صورت عدم اجرای فیلتر، از همان فایل خام استفاده می‌شود
    try:
        shutil.copyfile(raw_audio_path, mastered_audio_path)
        return True
    except Exception:
        return False


async def synth(text: str, voice: str, path: str, gemini_api_key: str = "", rate: str = "-3%", pitch: str = "-2Hz") -> bool:
    """
    موتور نریشن دو مرحله‌ای:
    ابتدا جمینای، در صورت عدم پاسخ‌دهی Edge-TTS + فیلترهای گرم‌کننده و مسترینگ صدا
    """
    if not text or len(text.strip()) < 2:
        return False

    raw_tmp = path + ".raw.mp3"

    # اولویت اول: جمینای
    ok = False
    if gemini_api_key:
        ok = await _synth_gemini_audio(text, gemini_api_key, raw_tmp)

    # اولویت دوم: Edge-TTS
    if not ok:
        ok = await _synth_edge_audio(text, voice, raw_tmp, rate=rate, pitch=pitch)

    if ok and os.path.exists(raw_tmp):
        mastered_ok = _apply_studio_audio_mastering(raw_tmp, path)
        try:
            if os.path.exists(raw_tmp):
                os.remove(raw_tmp)
        except Exception:
            pass
        return mastered_ok

    return False


def _get_audio_duration(audio_path: str) -> float:
    """محاسبه دقیق مدت‌زمان فایل صوتی با FFprobe/FFmpeg"""
    if not audio_path or not os.path.exists(audio_path):
        return 3.5
    try:
        cmd = [
            FFMPEG, "-i", audio_path,
            "-show_entries", "format=duration",
            "-v", "quiet", "-of", "csv=p=0"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        dur = float(res.stdout.strip())
        return max(2.5, min(dur + 0.4, 8.0))
    except Exception:
        return 3.5


def _render_single_scene_clip(img_path: str, audio_path: str | None, out_clip: str, fps: int = 24):
    """رندر یک سکانس ریلز با زوم متحرک نرم و هماهنگی دقیق صدا با تصویر"""
    duration = _get_audio_duration(audio_path) if audio_path else 3.5
    frames = max(1, int(duration * fps))

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(iw/zoom/2)':d={frames}:s=1080x1920:fps={fps},"
        "format=yuv420p"
    )

    src_audio = ["-i", audio_path] if (audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 500) else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]

    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", img_path, *src_audio,
        "-t", f"{duration:.2f}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-shortest",
        out_clip,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log.warning("FFmpeg clip render fallback: %s", res.stderr[:200] if res.stderr else "unknown error")
        simple_cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", img_path, *src_audio,
            "-t", f"{duration:.2f}",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_clip,
        ]
        subprocess.run(simple_cmd, capture_output=True, text=True)


def build_reel(frames: list[str], audios: list[str | None], texts: list[str], out_path: str, tail: float = 0.35) -> str:
    """چسباندن سکانس‌های ۵ گانه به همراه نریشن مستر شده به یک ویدیوی ریلز نهایی"""
    work_dir = os.path.dirname(out_path)
    os.makedirs(work_dir, exist_ok=True)
    clips = []

    for i, img in enumerate(frames):
        if not os.path.exists(img):
            continue
        au = audios[i] if (audios and i < len(audios)) else None
        clip_path = os.path.join(work_dir, f"clip_{i:02d}.mp4")
        _render_single_scene_clip(img, au, clip_path)
        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1000:
            clips.append(clip_path)

    if not clips:
        raise RuntimeError("No valid scene clips were generated.")

    list_file = os.path.join(work_dir, "clips.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(c)}'\n" for c in clips)

    concat_cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", "-movflags", "+faststart", out_path
    ]
    subprocess.run(concat_cmd, capture_output=True, text=True)

    for c in clips + [list_file]:
        try:
            if os.path.exists(c):
                os.remove(c)
        except Exception:
            pass

    return out_path
