"""Demo seed: subjects + questions + answer options (Uzbek, Latin script).

Run inside the running backend/bot container:
    docker compose exec backend python -m apps.testing.cli.seed            # idempotent
    docker compose exec backend python -m apps.testing.cli.seed --reset    # wipe & reseed
"""
import argparse
import asyncio
from dataclasses import dataclass

from sqlalchemy import delete, select

from apps.testing.models.answer_option import AnswerOption
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject
from core.db import SessionLocal


@dataclass(slots=True)
class OptionSeed:
    text: str
    is_correct: bool


@dataclass(slots=True)
class QuestionSeed:
    text: str
    options: list[OptionSeed]


@dataclass(slots=True)
class SubjectSeed:
    name: str
    questions: list[QuestionSeed]


def _opt(text: str, correct: bool = False) -> OptionSeed:
    return OptionSeed(text=text, is_correct=correct)


SEED: list[SubjectSeed] = [
    SubjectSeed(
        name="Matematika",
        questions=[
            QuestionSeed(
                text="2 + 2 * 2 nechaga teng?",
                options=[_opt("4"), _opt("6", True), _opt("8"), _opt("10")],
            ),
            QuestionSeed(
                text="9 sonining kvadrati nechaga teng?",
                options=[_opt("18"), _opt("72"), _opt("81", True), _opt("99")],
            ),
            QuestionSeed(
                text="To'g'ri burchakda necha gradus bor?",
                options=[_opt("45°"), _opt("60°"), _opt("90°", True), _opt("180°")],
            ),
            QuestionSeed(
                text="0! (nol faktorial) nechaga teng?",
                options=[_opt("0"), _opt("1", True), _opt("Aniqlanmagan"), _opt("∞")],
            ),
            QuestionSeed(
                text="1 dan 10 gacha nechta tub son bor?",
                options=[_opt("3"), _opt("4", True), _opt("5"), _opt("6")],
            ),
        ],
    ),
    SubjectSeed(
        name="Python",
        questions=[
            QuestionSeed(
                text="Python 3 da 3 / 2 ifodaning turi qanday?",
                options=[_opt("int"), _opt("float", True), _opt("decimal"), _opt("str")],
            ),
            QuestionSeed(
                text="print(len('hello')) nima chiqaradi?",
                options=[_opt("4"), _opt("5", True), _opt("6"), _opt("Xato")],
            ),
            QuestionSeed(
                text="Darajaga ko'tarish operatori qaysi?",
                options=[_opt("^"), _opt("**", True), _opt("//"), _opt("%%")],
            ),
            QuestionSeed(
                text="Qaysi tur o'zgarmas (immutable)?",
                options=[_opt("list"), _opt("dict"), _opt("set"), _opt("tuple", True)],
            ),
            QuestionSeed(
                text="Asinxron funksiyani belgilash uchun qaysi kalit so'z ishlatiladi?",
                options=[_opt("def"), _opt("async def", True), _opt("await"), _opt("function")],
            ),
        ],
    ),
    SubjectSeed(
        name="Tarix",
        questions=[
            QuestionSeed(
                text="Oktabr inqilobi qaysi yilda sodir bo'lgan?",
                options=[_opt("1905"), _opt("1914"), _opt("1917", True), _opt("1922")],
            ),
            QuestionSeed(
                text="AQShning birinchi prezidenti kim bo'lgan?",
                options=[
                    _opt("Avraam Linkoln"),
                    _opt("Tomas Jefferson"),
                    _opt("Jorj Vashington", True),
                    _opt("Benjamin Franklin"),
                ],
            ),
            QuestionSeed(
                text="Konstantinopol qaysi yilda qulagan?",
                options=[_opt("1453", True), _opt("1492"), _opt("1517"), _opt("1389")],
            ),
            QuestionSeed(
                text="Temuriylar davlatining asoschisi kim?",
                options=[
                    _opt("Chingizxon"),
                    _opt("Bobur"),
                    _opt("Amir Temur", True),
                    _opt("Ulug'bek"),
                ],
            ),
        ],
    ),
    SubjectSeed(
        name="Geografiya",
        questions=[
            QuestionSeed(
                text="Dunyodagi eng uzun daryo qaysi?",
                options=[_opt("Yantszi"), _opt("Amazonka", True), _opt("Nil"), _opt("Mississipi")],
            ),
            QuestionSeed(
                text="O'zbekistonning poytaxti qaysi shahar?",
                options=[
                    _opt("Samarqand"),
                    _opt("Buxoro"),
                    _opt("Toshkent", True),
                    _opt("Namangan"),
                ],
            ),
            QuestionSeed(
                text="Sahroyi Kabir qaysi qit'ada joylashgan?",
                options=[
                    _opt("Osiyo"),
                    _opt("Afrika", True),
                    _opt("Avstraliya"),
                    _opt("Janubiy Amerika"),
                ],
            ),
            QuestionSeed(
                text="Dunyodagi eng chuqur ko'l qaysi?",
                options=[
                    _opt("Kaspiy"),
                    _opt("Viktoriya"),
                    _opt("Baykal", True),
                    _opt("Tanganika"),
                ],
            ),
        ],
    ),
]


async def _reset() -> None:
    """Drop ALL subjects → cascades to questions, answer options, attempts, sessions."""
    async with SessionLocal() as session:
        await session.execute(delete(Subject))
        await session.commit()


async def run() -> tuple[int, int, int]:
    created_subjects = 0
    created_questions = 0
    created_options = 0

    async with SessionLocal() as session:
        for subject_seed in SEED:
            existing = await session.execute(
                select(Subject).where(Subject.name == subject_seed.name)
            )
            subject = existing.scalar_one_or_none()

            if subject is None:
                subject = Subject(name=subject_seed.name, is_active=True)
                session.add(subject)
                await session.flush()
                created_subjects += 1

            for q_seed in subject_seed.questions:
                q_existing = await session.execute(
                    select(Question).where(
                        Question.subject_id == subject.id,
                        Question.text == q_seed.text,
                    )
                )
                if q_existing.scalar_one_or_none() is not None:
                    continue

                question = Question(
                    subject_id=subject.id,
                    text=q_seed.text,
                    is_active=True,
                )
                session.add(question)
                await session.flush()
                created_questions += 1

                for opt in q_seed.options:
                    session.add(
                        AnswerOption(
                            question_id=question.id,
                            text=opt.text,
                            is_correct=opt.is_correct,
                        )
                    )
                    created_options += 1

        await session.commit()

    return created_subjects, created_questions, created_options


async def _main_async(reset: bool) -> None:
    if reset:
        print("⚠️  Wiping all subjects (cascades to questions/options/attempts/sessions)...")
        await _reset()

    subjects, questions, options = await run()
    print(
        f"Seed done: +{subjects} subjects, +{questions} questions, +{options} options"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo subjects/questions/options.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe ALL subjects (and dependent rows) before seeding.",
    )
    args = parser.parse_args()
    asyncio.run(_main_async(reset=args.reset))


if __name__ == "__main__":
    main()
