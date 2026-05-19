"""Idempotent demo seed: subjects + questions + answer options.

Run inside the running backend/bot container:
    docker compose exec backend python -m apps.testing.cli.seed
"""
import asyncio
from dataclasses import dataclass

from sqlalchemy import select

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
        name="Математика",
        questions=[
            QuestionSeed(
                text="Сколько будет 2 + 2 * 2?",
                options=[_opt("4"), _opt("6", True), _opt("8"), _opt("10")],
            ),
            QuestionSeed(
                text="Чему равен квадрат числа 9?",
                options=[_opt("18"), _opt("72"), _opt("81", True), _opt("99")],
            ),
            QuestionSeed(
                text="Сколько градусов в прямом угле?",
                options=[_opt("45°"), _opt("60°"), _opt("90°", True), _opt("180°")],
            ),
            QuestionSeed(
                text="Чему равен 0! (факториал нуля)?",
                options=[_opt("0"), _opt("1", True), _opt("Не определён"), _opt("∞")],
            ),
            QuestionSeed(
                text="Сколько простых чисел между 1 и 10?",
                options=[_opt("3"), _opt("4", True), _opt("5"), _opt("6")],
            ),
        ],
    ),
    SubjectSeed(
        name="Python",
        questions=[
            QuestionSeed(
                text="Какой тип данных у выражения 3 / 2 в Python 3?",
                options=[_opt("int"), _opt("float", True), _opt("decimal"), _opt("str")],
            ),
            QuestionSeed(
                text="Что выведет: print(len('hello'))?",
                options=[_opt("4"), _opt("5", True), _opt("6"), _opt("Ошибка")],
            ),
            QuestionSeed(
                text="Какой оператор используется для возведения в степень?",
                options=[_opt("^"), _opt("**", True), _opt("//"), _opt("%%")],
            ),
            QuestionSeed(
                text="Что не является изменяемым (mutable) типом?",
                options=[_opt("list"), _opt("dict"), _opt("set"), _opt("tuple", True)],
            ),
            QuestionSeed(
                text="Какое ключевое слово определяет асинхронную функцию?",
                options=[_opt("def"), _opt("async def", True), _opt("await"), _opt("function")],
            ),
        ],
    ),
    SubjectSeed(
        name="История",
        questions=[
            QuestionSeed(
                text="В каком году произошла Октябрьская революция?",
                options=[_opt("1905"), _opt("1914"), _opt("1917", True), _opt("1922")],
            ),
            QuestionSeed(
                text="Кто был первым президентом США?",
                options=[
                    _opt("Авраам Линкольн"),
                    _opt("Томас Джефферсон"),
                    _opt("Джордж Вашингтон", True),
                    _opt("Бенджамин Франклин"),
                ],
            ),
            QuestionSeed(
                text="В каком году пал Константинополь?",
                options=[_opt("1453", True), _opt("1492"), _opt("1517"), _opt("1389")],
            ),
            QuestionSeed(
                text="Кто основал государство Тимуридов?",
                options=[
                    _opt("Чингисхан"),
                    _opt("Бабур"),
                    _opt("Амир Темур", True),
                    _opt("Улугбек"),
                ],
            ),
        ],
    ),
    SubjectSeed(
        name="География",
        questions=[
            QuestionSeed(
                text="Самая длинная река мира?",
                options=[_opt("Янцзы"), _opt("Амазонка", True), _opt("Нил"), _opt("Миссисипи")],
            ),
            QuestionSeed(
                text="Столица Узбекистана?",
                options=[_opt("Самарканд"), _opt("Бухара"), _opt("Ташкент", True), _opt("Наманган")],
            ),
            QuestionSeed(
                text="На каком материке расположена Сахара?",
                options=[
                    _opt("Азия"),
                    _opt("Африка", True),
                    _opt("Австралия"),
                    _opt("Южная Америка"),
                ],
            ),
            QuestionSeed(
                text="Самое глубокое озеро в мире?",
                options=[_opt("Каспийское"), _opt("Виктория"), _opt("Байкал", True), _opt("Танганьика")],
            ),
        ],
    ),
]


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


def main() -> None:
    subjects, questions, options = asyncio.run(run())
    print(
        f"Seed done: +{subjects} subjects, +{questions} questions, +{options} options"
    )


if __name__ == "__main__":
    main()
