import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.attempt_session import AttemptSession, AttemptSessionStatus
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject


class AttemptStartError(StrEnum):
    NO_QUESTIONS = "no_questions"
    INACTIVE_SUBJECT = "inactive_subject"


@dataclass(slots=True)
class AttemptStartResult:
    session: AttemptSession | None
    error: AttemptStartError | None
    resumed: bool
    new_round: bool
    attempt_number: int


class AttemptService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_session(
        self, *, bot_user_id: int, subject_id: int
    ) -> AttemptSession | None:
        result = await self.session.execute(
            select(AttemptSession).where(
                AttemptSession.bot_user_id == bot_user_id,
                AttemptSession.subject_id == subject_id,
                AttemptSession.status == AttemptSessionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def get_session(self, session_id: int) -> AttemptSession | None:
        return await self.session.get(AttemptSession, session_id)

    async def _count_attempts(self, *, bot_user_id: int, subject_id: int) -> int:
        result = await self.session.execute(
            select(func.count(AttemptSession.id)).where(
                AttemptSession.bot_user_id == bot_user_id,
                AttemptSession.subject_id == subject_id,
            )
        )
        return int(result.scalar_one())

    async def _used_question_ids(
        self,
        *,
        bot_user_id: int,
        subject_id: int,
        round_number: int,
    ) -> set[int]:
        result = await self.session.execute(
            select(AttemptSession.question_ids).where(
                AttemptSession.bot_user_id == bot_user_id,
                AttemptSession.subject_id == subject_id,
                AttemptSession.round_number == round_number,
            )
        )
        used: set[int] = set()
        for (ids,) in result.all():
            if ids:
                used.update(int(i) for i in ids)
        return used

    async def _current_round_number(
        self, *, bot_user_id: int, subject_id: int
    ) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(AttemptSession.round_number), 1)).where(
                AttemptSession.bot_user_id == bot_user_id,
                AttemptSession.subject_id == subject_id,
            )
        )
        return int(result.scalar_one())

    async def _all_active_question_ids(self, subject_id: int) -> list[int]:
        result = await self.session.execute(
            select(Question.id).where(
                Question.subject_id == subject_id,
                Question.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def start_or_resume(
        self,
        *,
        bot_user_id: int,
        subject: Subject,
    ) -> AttemptStartResult:
        if not subject.is_active:
            return AttemptStartResult(
                session=None,
                error=AttemptStartError.INACTIVE_SUBJECT,
                resumed=False,
                new_round=False,
                attempt_number=0,
            )

        existing = await self.get_active_session(
            bot_user_id=bot_user_id, subject_id=subject.id
        )
        if existing is not None:
            return AttemptStartResult(
                session=existing,
                error=None,
                resumed=True,
                new_round=False,
                attempt_number=existing.attempt_number,
            )

        all_ids = await self._all_active_question_ids(subject.id)
        if not all_ids:
            return AttemptStartResult(
                session=None,
                error=AttemptStartError.NO_QUESTIONS,
                resumed=False,
                new_round=False,
                attempt_number=0,
            )

        round_number = await self._current_round_number(
            bot_user_id=bot_user_id, subject_id=subject.id
        )
        used = await self._used_question_ids(
            bot_user_id=bot_user_id,
            subject_id=subject.id,
            round_number=round_number,
        )
        pool = [qid for qid in all_ids if qid not in used]
        new_round = False
        if not pool:
            # Все вопросы текущего круга разобраны — стартуем новый круг.
            round_number += 1
            pool = list(all_ids)
            new_round = True

        take = min(subject.questions_per_attempt, len(pool))
        question_ids = random.sample(pool, take)

        attempts_count = await self._count_attempts(
            bot_user_id=bot_user_id, subject_id=subject.id
        )
        attempt_number = attempts_count + 1

        attempt = AttemptSession(
            bot_user_id=bot_user_id,
            subject_id=subject.id,
            status=AttemptSessionStatus.ACTIVE,
            attempt_number=attempt_number,
            round_number=round_number,
            question_ids=question_ids,
            current_index=0,
            correct_count=0,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)

        return AttemptStartResult(
            session=attempt,
            error=None,
            resumed=False,
            new_round=new_round,
            attempt_number=attempt_number,
        )

    async def advance(self, session: AttemptSession, *, is_correct: bool) -> AttemptSession:
        session.current_index += 1
        if is_correct:
            session.correct_count += 1
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def finish(self, session: AttemptSession) -> AttemptSession:
        session.status = AttemptSessionStatus.COMPLETED
        session.ended_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def abort(self, session: AttemptSession) -> AttemptSession:
        session.status = AttemptSessionStatus.ABORTED
        session.ended_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    def next_question_id(self, session: AttemptSession) -> int | None:
        if session.current_index >= len(session.question_ids):
            return None
        return int(session.question_ids[session.current_index])
