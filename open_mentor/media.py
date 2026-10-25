"""Collect published captions; all acquired transcripts remain pending review."""
from __future__ import annotations

import json
import hashlib
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .library import Library
from .updates import normalize, timestamp


def _write_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def _audio_duration(path: Path) -> float:
    probe = shutil.which("ffprobe")
    if not probe:
        raise ValueError("Install FFmpeg (including ffprobe) for local transcription")
    result = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True)
    if result.returncode:
        raise ValueError("ffprobe could not read this audio")
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Audio duration must be positive and finite")
    return duration


def _recognizer(engine: str, model: str, model_dir: Path):
    if engine == "mlx":
        try:
            import mlx_whisper
        except ImportError as exc:
            raise ValueError("Install Apple Silicon ASR support: pip install -e '.[asr-mlx]'") from exc
        return lambda audio, language: mlx_whisper.transcribe(
            audio, path_or_hf_repo=model, language=language, verbose=None,
            condition_on_previous_text=False, temperature=0,
        )["segments"]
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ValueError("Install local ASR support: pip install -e '.[asr]'") from exc
    asr = WhisperModel(model, device="cpu", compute_type="int8", download_root=str(model_dir))

    def run(audio, language):
        segments, _ = asr.transcribe(audio, language=language, beam_size=5, condition_on_previous_text=False)
        return [dict(start=s.start, end=s.end, text=s.text, avg_logprob=s.avg_logprob,
                     compression_ratio=s.compression_ratio, no_speech_prob=s.no_speech_prob) for s in segments]
    return run


def _cue_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    return f"{milliseconds // 3600000:02}:{milliseconds // 60000 % 60:02}:{milliseconds // 1000 % 60:02}.{milliseconds % 1000:03}"


def _yt_dlp():
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise ValueError("Install media support: pip install -e '.[media]'") from exc
    return YoutubeDL


def _js_runtime() -> dict:
    node = shutil.which("node")
    return {"js_runtimes": {"node": {"path": node}}} if node else {}


def _seconds(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) not in {2, 3}:
        raise ValueError("Invalid subtitle timestamp: " + value)
    return sum(float(v) * 60 ** i for i, v in enumerate(reversed(parts)))


def parse_captions(path: Path) -> list[dict]:
    if path.suffix.lower() not in {".vtt", ".srt", ".json", ".json3"}:
        raise ValueError("Unsupported caption format: " + path.suffix)
    text = path.read_text(encoding="utf-8-sig")
    segments = []
    if path.suffix in {".json", ".json3"}:
        payload = json.loads(text)
        if "body" in payload:  # Bilibili public subtitle JSON
            segments = [{"start": float(e["from"]), "end": float(e["to"]), "text": e["content"]} for e in payload["body"]]
        elif "events" in payload:  # YouTube json3
            for event in payload["events"]:
                content = "".join(s.get("utf8", "") for s in event.get("segs", []))
                if content.strip():
                    start = event["tStartMs"] / 1000
                    segments.append({"start": start, "end": start + event.get("dDurationMs", 0) / 1000, "text": content})
        else:
            raise ValueError("Unknown caption JSON format")
    else:
        for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
            lines = block.splitlines()
            for i, line in enumerate(lines):
                match = re.match(r"\s*([\d:.,]+)\s+-->\s+([\d:.,]+)", line)
                if match:
                    segments.append({"start": _seconds(match[1]), "end": _seconds(match[2]), "text": " ".join(lines[i + 1:])})
                    break
    cleaned = []
    for segment in segments:
        segment["text"] = normalize(re.sub(r"<[^>]+>", "", segment["text"]))
        if segment["start"] < 0 or segment["end"] < segment["start"]:
            raise ValueError("Invalid caption time range")
        if segment["text"] and (not cleaned or segment["text"] != cleaned[-1]["text"]):
            cleaned.append({**segment, "speaker": None, "verification": "pending"})
    return cleaned


class Media:
    def __init__(self, library: Library):
        self.library = library

    def _source(self, source_id: str, url: str | None):
        source = self.library.source(source_id)
        allowed = {source["url"], source.get("origin_url")}
        selected = url or source.get("origin_url") or source["url"]
        if selected not in allowed:
            raise ValueError("Register this video's URL as source.url or source.origin_url first")
        root = self.library.state_dir / "media" / source_id
        root.mkdir(parents=True, exist_ok=True)
        return source, selected, root

    def fetch_subtitles(self, source_id: str, url: str | None = None) -> dict:
        _, selected, root = self._source(source_id, url)
        opts = {**_js_runtime(), "skip_download": True, "writesubtitles": True, "writeautomaticsub": True,
                "subtitleslangs": ["zh.*", "en.*"], "subtitlesformat": "vtt/srt/json3/json/best",
                "outtmpl": str(root / "%(id)s.%(ext)s"), "noplaylist": True, "playlist_items": "1",
                "socket_timeout": 20, "retries": 1, "extractor_retries": 1, "quiet": True, "noprogress": True}
        try:
            with _yt_dlp()(opts) as downloader:
                info = downloader.extract_info(selected, download=True)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"yt-dlp could not retrieve captions: {exc}") from exc
        if info and info.get("entries"):
            info = next((e for e in info["entries"] if e), None)
        if not info:
            raise ValueError("yt-dlp returned no video information")
        transcripts = []
        for language, subtitle in (info.get("requested_subtitles") or {}).items():
            filepath = subtitle.get("filepath")
            if not filepath or not Path(filepath).is_file():
                continue
            path = Path(filepath)
            # yt-dlp reports the path it wrote. Do not import unrelated local files.
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("Subtitle path is outside this source's media directory")
            segments = parse_captions(path)
            if not segments:
                raise ValueError("Caption file contains no timed text segments: " + path.name)
            kind = "publisher_caption" if language in (info.get("subtitles") or {}) else "platform_automatic_caption"
            document = {"source_id": source_id, "video_url": selected, "video_id": info.get("id"),
                        "language": language, "transcript_kind": kind, "verification": "pending", "segments": segments}
            target = path.with_suffix(".transcript.json")
            target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
            transcripts.append({"language": language, "kind": kind, "segments": len(segments), "path": str(target.resolve())})
        result = {"source_id": source_id, "video_url": selected, "video_id": info.get("id"), "title": info.get("title"),
                  "uploader": info.get("uploader"), "upload_date": info.get("upload_date"), "duration": info.get("duration"),
                  "acquired_at": timestamp(), "status": "downloaded_pending_review" if transcripts else "no_subtitles",
                  "transcripts": transcripts, "note": "下载或自动转写均不确认说话人、原话和事实；核对后再贡献知识条目。"}
        (root / "acquisition.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result

    def fetch_audio(self, source_id: str, url: str | None = None) -> dict:
        _, selected, root = self._source(source_id, url)
        opts = {**_js_runtime(), "format": "bestaudio", "outtmpl": str(root / "audio.%(ext)s"), "noplaylist": True,
                "playlist_items": "1", "socket_timeout": 20, "retries": 1, "max_filesize": 512 * 1024 * 1024,
                "quiet": True, "noprogress": True}
        try:
            with _yt_dlp()(opts) as downloader:
                info = downloader.extract_info(selected, download=True)
                if info and info.get("entries"):
                    info = next((e for e in info["entries"] if e), None)
                if not info:
                    raise ValueError("yt-dlp returned no audio information")
                path = downloader.prepare_filename(info)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"yt-dlp could not retrieve audio: {exc}") from exc
        if not Path(path).is_file():
            raise ValueError("Audio was not downloaded")
        result = {"source_id": source_id, "video_url": selected, "path": str(Path(path).resolve()),
                  "status": "audio_only", "acquired_at": timestamp()}
        (root / "audio-acquisition.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result

    def transcribe(self, source_id: str, path: Path, model: str = "small", language: str = "zh",
                   engine: str = "faster-whisper", chunk_seconds: int = 600,
                   source_offset: float | None = None) -> dict:
        self.library.source(source_id)
        if not path.is_file():
            raise ValueError("Audio file does not exist")
        if engine not in {"faster-whisper", "mlx"}:
            raise ValueError("Unknown ASR engine")
        if not 30 <= chunk_seconds <= 3600 or (source_offset is not None and (not math.isfinite(source_offset) or source_offset < 0)):
            raise ValueError("Use chunks of 30–3600 seconds and a nonnegative source offset")
        try:
            import numpy as np
        except ImportError as exc:
            raise ValueError("Install local ASR support: pip install -e '.[asr]' or '.[asr-mlx]'") from exc
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise ValueError("Install FFmpeg to decode interview audio before local transcription")
        duration = _audio_duration(path)
        digest = hashlib.sha256()
        with path.open("rb") as input_file:
            for block in iter(lambda: input_file.read(1024 * 1024), b""):
                digest.update(block)
        signature = {"input_sha256": digest.hexdigest(), "engine": engine, "model": model,
                     "language": language, "chunk_seconds": chunk_seconds, "source_offset_seconds": source_offset}
        run_hash = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:12]
        model_name = re.sub(r"[^a-zA-Z0-9-]", "-", model.rstrip("/").split("/")[-1])[:60]
        root = self.library.state_dir / "media" / source_id / f"asr-{engine}-{model_name}-{run_hash}"
        root.mkdir(parents=True, exist_ok=True)
        result = {"source_id": source_id, "transcript_kind": "local_machine_transcription", **signature,
                  "verification": "pending", "input_audio": path.name, "input_duration_seconds": duration,
                  "coverage": "input_audio_only", "source_complete_verified": False,
                  "input_coverage_complete": False, "chunks": [], "segments": [],
                  "note": "整段解码完成不等于逐句正确。说话人未确认；分块边界、低置信片段和数字须回听复核。"}
        recognize = None
        offset = source_offset or 0.0
        for index, start in enumerate(range(0, math.ceil(duration), chunk_seconds)):
            end = min(start + chunk_seconds, duration)
            checkpoint = root / f"chunk-{index:04}.json"
            if checkpoint.exists():
                chunk = json.loads(checkpoint.read_text())
                if chunk.get("signature") != signature or chunk.get("input_start") != start or chunk.get("input_end") != end:
                    raise ValueError("Checkpoint does not match this input and ASR configuration")
            else:
                # Decode bounded windows, avoiding PyAV-version coupling and four-hour waveforms in memory.
                decoded = subprocess.run(
                    [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-ss", str(start), "-i", str(path),
                     "-t", str(end - start), "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "pipe:1"],
                    capture_output=True,
                )
                if decoded.returncode or not decoded.stdout:
                    raise ValueError("FFmpeg could not decode this audio window: " + decoded.stderr.decode(errors="replace")[-1000:])
                decoded_seconds = len(decoded.stdout) / 32000
                if abs(decoded_seconds - (end - start)) > 1:
                    raise ValueError("Decoded audio duration differs from the requested window; refusing to mark complete")
                audio = np.frombuffer(decoded.stdout, dtype="<i2").astype(np.float32) / 32768.0
                if recognize is None:
                    recognize = _recognizer(engine, model, self.library.state_dir / "models")
                rows = []
                for segment in recognize(audio, language):
                    a, b = float(segment["start"]), float(segment["end"])
                    if not (math.isfinite(a) and math.isfinite(b) and 0 <= a <= b <= end - start + 1):
                        raise ValueError("ASR returned an invalid time range")
                    text = segment["text"].strip()
                    if not text:
                        continue
                    scores = {k: float(segment[k]) for k in ("avg_logprob", "compression_ratio", "no_speech_prob") if k in segment}
                    flags = []
                    if scores.get("avg_logprob", 0) < -1 or scores.get("compression_ratio", 0) > 2.4 or scores.get("no_speech_prob", 0) > .6:
                        flags.append("asr_low_confidence")
                    if (start > 0 and a < 3) or (end < duration and b > end - start - 3):
                        flags.append("chunk_boundary")
                    rows.append({"start": round(start + offset + a, 3), "end": round(start + offset + min(b, end - start), 3),
                                 "text": text, "speaker": None, "verification": "pending", "scores": scores, "review_flags": flags})
                chunk = {"signature": signature, "input_start": start, "input_end": end,
                         "decoded_seconds": decoded_seconds, "completed_at": timestamp(), "segments": rows}
                _write_json(checkpoint, chunk)
            result["chunks"].append({"path": checkpoint.name, "input_start": start, "input_end": end,
                                     "segments": len(chunk["segments"])})
            result["segments"].extend(chunk["segments"])
            result["processed_input_seconds"] = end
            _write_json(root / "progress.json", {k: v for k, v in result.items() if k != "segments"})
            print(f"{source_id}: {end:.1f}/{duration:.1f} seconds decoded and transcribed (pending review)", file=sys.stderr, flush=True)
        result["input_coverage_complete"] = True
        result["completed_at"] = timestamp()
        _write_json(root / "transcript.json", result)
        (root / "transcript.vtt").write_text("WEBVTT\n\n" + "\n\n".join(
            f"{_cue_time(s['start'])} --> {_cue_time(s['end'])}\n{s['text']}" for s in result["segments"]) + "\n")
        (root / "transcript.txt").write_text("\n".join(
            f"[{_cue_time(s['start'])}–{_cue_time(s['end'])}] {s['text']}" for s in result["segments"]) + "\n")
        return {"status": "transcribed_pending_review", "path": str((root / "transcript.json").resolve()),
                "segments": len(result["segments"]), "input_duration_seconds": duration, "input_coverage_complete": True}
