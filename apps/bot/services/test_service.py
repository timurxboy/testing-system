from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.bot.models.test_attempt import TestAttempt
from apps.testing.models.answer_option import AnswerOption
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject


class TestService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active_subjects(self) -> list[Subject]:
        result = await self.session.execute(
            select(Subject)
            .where(Subject.is_active.is_(True))
            .order_by(Subject.name)
        )
        return list(result.scalars().all())

    async def get_subject(self, subject_id: int) -> Subject | None:
        return await self.session.get(Subject, subject_id)

    async def list_question_ids_for_subject(self, subject_id: int) -> list[int]:
        result = await self.session.execute(
            select(Question.id)
            .where(
                Question.subject_id == subject_id,
                Question.is_active.is_(True),
            )
            .order_by(Question.id)
        )
        return list(result.scalars().all())

    async def get_question_with_options(self, question_id: int) -> Question | None:
        result = await self.session.execute(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def get_option(self, option_id: int) -> AnswerOption | None:
        return await self.session.get(AnswerOption, option_id)

    async def record_attempt(
        self,
        *,
        bot_user_id: int,
        subject_id: int,
        question_id: int,
        selected_option_id: int,
        is_correct: bool,
        attempt_session_id: int | None = None,
    ) -> TestAttempt:
        attempt = TestAttempt(
            bot_user_id=bot_user_id,
            subject_id=subject_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            attempt_session_id=attempt_session_id,
        )
        self.session.add(attempt)
        await self.session.commit()
        return attempt
