"""Import subjects/questions/options from JSON files.

JSON format (one subject per file):
{
  "subject": "Matematika",
  "is_active": true,                 // optional, default true
  "questions": [
    {
      "text": "Question text?",
      "options": [
        { "text": "Option A", "correct": false },
        { "text": "Option B", "correct": true }
      ]
    }
  ]
}

Idempotent: subjects matched by name, questions by (subject, text). Existing
rows are not duplicated; new questions/options are appended.

Run inside the running backend container:
    docker compose exec backend poetry run python -m apps.testing.cli.import_json
    docker compose exec backend poetry run python -m apps.testing.cli.import_json testing/matematika.json
    docker compose exec backend poetry run python -m apps.testing.cli.import_json testing/
"""
import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.testing.models.answer_option import AnswerOption
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject
from core.db import SessionLocal

DEFAULT_DIR = Path("testing")


@dataclass(slots=True)
class ImportStats:
    subjects: int = 0
    questions: int = 0
    options: int = 0
    skipped_questions: int = 0


async def _import_subject(session: AsyncSession, payload: dict) -> ImportStats:
    stats = ImportStats()

    subject_name = payload["subject"]
    is_active = bool(payload.get("is_active", True))

    res = await session.execute(select(Subject).where(Subject.name == subject_name))
    subject = res.scalar_one_or_none()

    if subject is None:
        subject = Subject(name=subject_name, is_active=is_active)
        session.add(subject)
        await session.flush()
        stats.subjects = 1
    elif "is_active" in payload:
        subject.is_active = is_active

    for q_payload in payload.get("questions", []):
        q_text = q_payload["text"]
        existing_q = await session.execute(
            select(Question).where(
                Question.subject_id == subject.id,
                Question.text == q_text,
            )
        )
        if existing_q.scalar_one_or_none() is not None:
            stats.skipped_questions += 1
            continue

        question = Question(subject_id=subject.id, text=q_text, is_active=True)
        session.add(question)
        await session.flush()
        stats.questions += 1

        for opt in q_payload.get("options", []):
            session.add(
                AnswerOption(
                    question_id=question.id,
                    text=opt["text"],
                    is_correct=bool(opt.get("correct", False)),
                )
            )
            stats.options += 1

    return stats


def _resolve_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.glob("*.json")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"⚠️  Not found: {p}")
    return files


async def _main_async(paths: list[Path]) -> None:
    files = _resolve_files(paths)
    if not files:
        print("No JSON files to import.")
        return

    total = ImportStats()
    async with SessionLocal() as session:
        for f in files:
            print(f"→ {f}")
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON error: {e}")
                continue
            try:
                stats = await _import_subject(session, payload)
            except KeyError as e:
                print(f"   ❌ Missing field: {e}")
                continue

            print(
                f"   +{stats.subjects} subject, "
                f"+{stats.questions} questions, "
                f"+{stats.options} options, "
                f"{stats.skipped_questions} skipped"
            )
            total.subjects += stats.subjects
            total.questions += stats.questions
            total.options += stats.options
            total.skipped_questions += stats.skipped_questions

        await session.commit()

    print(
        f"Done: +{total.subjects} subjects, "
        f"+{total.questions} questions, "
        f"+{total.options} options, "
        f"{total.skipped_questions} skipped"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import subjects/questions/options from JSON files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="JSON files or directories with .json files (default: ./testing/)",
    )
    args = parser.parse_args()
    paths = args.paths or [DEFAULT_DIR]
    asyncio.run(_main_async(paths))


if __name__ == "__main__":
    main()
