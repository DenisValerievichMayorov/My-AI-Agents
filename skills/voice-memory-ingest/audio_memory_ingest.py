import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_WHISPER = Path(__file__).resolve().parent / "whisper-cublas-12.4.0-bin-x64" / "Release" / "whisper-cli.exe"
DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "ggml-large-v3-turbo.bin"
DEFAULT_MEMORY_ROOT = Path.home() / "Sync" / "Data" / "PersonalMemory"


SUMMARY_PROMPT = """Ты помощник по созданию долговременной памяти пользователя Дениса.

Ниже распознанная русская стенограмма аудио. Это может быть бытовой разговор,
конфликт, монолог или заметка. Нельзя выдавать обвинения и спорные утверждения
как установленные факты.

Сделай строго JSON без markdown:
{
  "summary": "краткое содержание 3-6 предложений",
  "memory_candidates": [
    {
      "type": "preference|fact|relationship|project|routine|concern|quote|other",
      "text": "короткая формулировка для памяти агента",
      "confidence": "high|medium|low",
      "source_note": "почему это можно/нельзя считать надежным"
    }
  ],
  "sensitive_or_conflict_notes": [
    "спорные места, обвинения, эмоциональные высказывания, которые нельзя сохранять как факт"
  ],
  "follow_up_questions": [
    "что стоит уточнить у пользователя перед сохранением в постоянную память"
  ]
}

Правила отбора memory_candidates:
- Сохраняй только долговременные сведения о Денисе: устойчивые предпочтения,
  цели, проекты, привычки, важные отношения, рабочие процессы, явно сказанные
  факты о нем.
- Не сохраняй общие истины вроде "курение оставляет запах" или "важно мыть".
- Не сохраняй обвинения участников конфликта как память о Денисе.
- Если запись не содержит надежной личной памяти о Денисе, верни пустой массив.
- Для конфликтных бытовых сцен лучше заполни `sensitive_or_conflict_notes`,
  а `memory_candidates` оставь пустым или low-confidence.

СТЕНОГРАММА:
__TRANSCRIPT__
"""


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_whisper(args: argparse.Namespace, out_base: Path) -> None:
    command = [
        str(args.whisper),
        "-m",
        str(args.model),
        "-f",
        str(args.audio),
        "-l",
        args.language,
        "-t",
        str(args.threads),
        "-fa",
        "-oj",
        "-otxt",
        "-of",
        str(out_base),
    ]
    if args.duration_minutes:
        command.extend(["-d", str(int(args.duration_minutes * 60 * 1000))])
    if args.no_gpu:
        command.append("-ng")

    subprocess.run(command, cwd=str(args.whisper.parent), check=True)


def prepare_audio_for_whisper(source: Path, target_dir: Path, duration_minutes: float | None) -> Path:
    """Copy or trim WAV locally so whisper-cli does not depend on removable-drive access."""
    target = target_dir / "input.wav"
    if source.suffix.lower() == ".wav":
        with wave.open(str(source), "rb") as src:
            params = src.getparams()
            if duration_minutes:
                frames_to_copy = min(src.getnframes(), int(src.getframerate() * 60 * duration_minutes))
            else:
                frames_to_copy = src.getnframes()
            with wave.open(str(target), "wb") as dst:
                dst.setparams(params)
                remaining = frames_to_copy
                while remaining > 0:
                    chunk = min(remaining, src.getframerate() * 30)
                    data = src.readframes(chunk)
                    if not data:
                        break
                    dst.writeframes(data)
                    remaining -= chunk
        return target

    copied = target_dir / source.name
    shutil.copy2(source, copied)
    return copied


def llm_summarize(model: str, prompt: str) -> str:
    """Post-process transcript via OpenRouter (local Ollama removed 2026-08-02)."""
    try:
        import sys
        scripts = Path(r"C:/Users/anton/Sync/Scripts")
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        import reasoning_engine as re  # type: ignore
        mid = model if "/" in model else "openrouter/free"
        out = re.query_openrouter(
            prompt,
            system_prompt="You extract memory candidates as JSON.",
            model=mid,
        )
        if out:
            return out
    except Exception as e:
        print(f"[voice-memory] OpenRouter failed: {e}")
    return json.dumps(
        {
            "summary": "LLM summary unavailable (local Ollama removed; OpenRouter failed). See transcript.",
            "memory_candidates": [],
            "sensitive_or_conflict_notes": ["llm_summary_skipped"],
            "follow_up_questions": [],
        },
        ensure_ascii=False,
    )


def parse_summary(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def append_jsonl(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_index(memory_root: Path) -> None:
    index = memory_root / "README.md"
    content = """# Personal Memory Store

Единый локально-синхронизируемый источник памяти пользователя для агентов.

## Правило чтения
- Сначала читать `core/profile.md`.
- Затем читать `memories/memory_candidates.jsonl`.
- Для первоисточников смотреть `sources/audio/`.

## Правило записи
- Новые данные из аудио сначала попадают в `memory_candidates.jsonl`.
- Конфликтные или чувствительные утверждения сохраняются только как `со слов участников`.
- Агент не должен превращать обвинение из записи в установленный факт без подтверждения пользователя.

## Pipeline
`WAV -> whisper.cpp CUDA large-v3-turbo -> transcript txt/json -> OpenRouter summary -> memory candidates`
"""
    if not index.exists():
        index.write_text(content, encoding="utf-8")


def ensure_profile(memory_root: Path) -> None:
    profile = memory_root / "core" / "profile.md"
    profile.parent.mkdir(parents=True, exist_ok=True)
    if not profile.exists():
        profile.write_text(
            """# Core Profile

Краткий профиль пользователя. Обновлять только проверенными фактами.

- Основной язык общения: русский.
- Новые сведения из аудио добавлять сначала в `memories/memory_candidates.jsonl`.
""",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest recorder audio into shared personal memory.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--memory-root", type=Path, default=DEFAULT_MEMORY_ROOT)
    parser.add_argument("--whisper", type=Path, default=DEFAULT_WHISPER)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--ollama-model", default="openrouter/free", help="legacy flag; OpenRouter model id")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--duration-minutes", type=float, default=None)
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("--copy-audio", action="store_true")
    args = parser.parse_args()

    args.audio = args.audio.resolve()
    args.memory_root = args.memory_root.resolve()
    if not args.audio.exists():
        raise FileNotFoundError(args.audio)

    stamp = now_stamp()
    audio_hash = file_sha256(args.audio)[:16]
    run_id = f"{stamp}_{args.audio.stem}_{audio_hash}"
    source_dir = args.memory_root / "sources" / "audio" / run_id
    source_dir.mkdir(parents=True, exist_ok=True)

    local_audio = prepare_audio_for_whisper(args.audio, source_dir, args.duration_minutes)
    whisper_args = argparse.Namespace(**vars(args))
    whisper_args.audio = local_audio
    whisper_args.duration_minutes = None

    out_base = source_dir / "transcript"
    run_whisper(whisper_args, out_base)

    transcript_path = out_base.with_suffix(".txt")
    json_path = out_base.with_suffix(".json")
    transcript = transcript_path.read_text(encoding="utf-8")
    raw_summary = llm_summarize(args.ollama_model, SUMMARY_PROMPT.replace("__TRANSCRIPT__", transcript))
    (source_dir / "summary_raw.txt").write_text(raw_summary, encoding="utf-8")

    try:
        summary = parse_summary(raw_summary)
    except Exception as exc:
        summary = {
            "summary": "LLM не вернула валидный JSON; см. summary_raw.txt.",
            "memory_candidates": [],
            "sensitive_or_conflict_notes": [str(exc)],
            "follow_up_questions": ["Повторить постобработку другой моделью или вручную проверить стенограмму."],
        }

    metadata = {
        "run_id": run_id,
        "created_at": stamp,
        "audio_path": str(args.audio),
        "audio_sha256": file_sha256(args.audio),
        "local_audio": str(local_audio),
        "duration_minutes_limit": args.duration_minutes,
        "whisper": str(args.whisper),
        "model": str(args.model),
        "language": args.language,
        "summary_model": args.ollama_model,
        "transcript": str(transcript_path),
        "transcript_json": str(json_path),
    }
    if args.copy_audio:
        copied = source_dir / args.audio.name
        shutil.copy2(args.audio, copied)
        metadata["copied_audio"] = str(copied)

    (source_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (source_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    ensure_profile(args.memory_root)
    write_index(args.memory_root)
    append_jsonl(args.memory_root / "memories" / "ingest_log.jsonl", metadata)

    for candidate in summary.get("memory_candidates", []):
        append_jsonl(
            args.memory_root / "memories" / "memory_candidates.jsonl",
            {
                "run_id": run_id,
                "created_at": stamp,
                "source": str(transcript_path),
                "candidate": candidate,
                "status": "candidate",
            },
        )

    print(source_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
