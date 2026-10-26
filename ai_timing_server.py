"""Loopback-only Beat This! timing service for Mania Studio."""

from __future__ import annotations

import json
import io
import os
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


HOST = "127.0.0.1"
PORT = 8765
MAX_AUDIO_BYTES = 500 * 1024 * 1024
MODEL_NAME = "Beat This! small0"

_model = None
_model_state = "loading"
_model_error = ""
_model_lock = threading.Lock()
_inference_lock = threading.Lock()


def _load_model() -> None:
    global _model, _model_state, _model_error
    try:
        import torch
        from beat_this.inference import Audio2Beats

        torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
        _model = Audio2Beats(checkpoint_path="small0", device="cpu", dbn=False)
        _model_state = "ready"
    except Exception as exc:  # Report setup/model download failures to the UI.
        _model_error = f"{type(exc).__name__}: {exc}"
        _model_state = "error"


def _origin_allowed(origin: str) -> bool:
    if not origin or origin == "null":
        return True
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def _decode_pcm_wav(audio_bytes: bytes):
    """Decode browser-generated PCM WAV without relying on torchaudio backends."""
    import numpy as np

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
        if wav.getcomptype() != "NONE" or sample_width != 2:
            raise ValueError("需要未壓縮的 16-bit PCM WAV 音訊。")
        raw_samples = wav.readframes(frame_count)
    expected_bytes = frame_count * channels * sample_width
    if channels < 1 or frame_count < 1 or len(raw_samples) != expected_bytes:
        raise ValueError("WAV 音訊標頭或取樣資料不完整。")
    samples = np.frombuffer(raw_samples, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples, sample_rate


class Handler(BaseHTTPRequestHandler):
    server_version = "ManiaStudioTiming/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print("[Mania Studio AI] " + (fmt % args))

    def _cors(self) -> bool:
        origin = self.headers.get("Origin", "")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")
        return True

    def _json(self, status: int, data: dict[str, object]) -> None:
        if not _origin_allowed(self.headers.get("Origin", "")):
            self.send_error(403, "Only local Mania Studio pages are allowed")
            return
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not _origin_allowed(self.headers.get("Origin", "")):
            self.send_error(403, "Only local Mania Studio pages are allowed")
            return
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not _origin_allowed(self.headers.get("Origin", "")):
            self.send_error(403, "Only local Mania Studio pages are allowed")
            return
        if self.path != "/api/status":
            self._json(404, {"error": "Not found"})
            return
        self._json(
            200,
            {
                "state": _model_state,
                "model": MODEL_NAME,
                "error": _model_error,
                "audioStaysLocal": True,
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        if not _origin_allowed(self.headers.get("Origin", "")):
            self.send_error(403, "Only local Mania Studio pages are allowed")
            return
        if self.path != "/api/timing-ai":
            self._json(404, {"error": "Not found"})
            return
        if _model_state == "loading":
            self._json(503, {"error": "AI 模型仍在載入，請稍候再試。", "state": _model_state})
            return
        if _model_state != "ready" or _model is None:
            self._json(
                503,
                {
                    "error": "AI 模型尚未就緒。請檢查安裝，或重新啟動本機服務。",
                    "state": _model_state,
                    "detail": _model_error,
                },
            )
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 44 or length > MAX_AUDIO_BYTES:
            self._json(413, {"error": "音訊資料大小無效（限制為 500 MiB）。"})
            return
        audio_bytes = self.rfile.read(length)
        if len(audio_bytes) != length or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
            self._json(400, {"error": "收到的資料不是有效 WAV 音訊。"})
            return

        try:
            samples, sample_rate = _decode_pcm_wav(audio_bytes)
            with _inference_lock:
                beat_times, downbeat_times = _model(samples, sample_rate)
            beats = [float(x) for x in beat_times if float(x) >= 0]
            downbeats = [float(x) for x in downbeat_times if float(x) >= 0]
            if len(beats) < 4:
                raise ValueError("模型找到的拍點太少，無法穩定估算 BPM。")
            self._json(
                200,
                {
                    "model": MODEL_NAME,
                    "beats": beats,
                    "downbeats": downbeats,
                    "audioStaysLocal": True,
                },
            )
        except Exception as exc:
            self._json(500, {"error": f"AI 音訊分析失敗：{type(exc).__name__}: {exc}"})


def main() -> None:
    threading.Thread(target=_load_model, name="beat-this-loader", daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"Mania Studio AI timing service: http://{HOST}:{PORT}")
    print("Loading Beat This! small0 on CPU. The first run downloads the official model weights (~8.1 MB).")
    print("Audio analysis is handled locally; press Ctrl+C to stop the service.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Mania Studio AI timing service.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
