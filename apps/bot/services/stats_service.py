from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.attempt_session import AttemptSession, AttemptSessionStatus
from apps.bot.models.bot_user import BotUser
from apps.testing.models.subject import Subject

PAGE_SIZE = 5


class StatsPeriod(StrEnum):
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


_PERIOD_DAYS: dict[StatsPeriod, int] = {
    StatsPeriod.WEEK: 7,
    StatsPeriod.MONTH: 30,
    StatsPeriod.YEAR: 365,
}


@dataclass(slots=True)
class AttemptStat:
    subject_name: str
    correct: int
    total: int
    attempt_number: int
    status: AttemptSessionStatus
    finished_at: datetime

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total * 100) if self.total else 0.0


@dataclass(slots=True)
class UserStats:
    user_id: int
    telegram_id: int
    telegram_username: str | None
    student_id: str | None
    attempts: list[AttemptStat] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.student_id or self.telegram_username or f"tg:{self.telegram_id}"

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    @property
    def average_accuracy(self) -> float:
        if not self.attempts:
            return 0.0
        return sum(a.accuracy for a in self.attempts) / len(self.attempts)


@dataclass(slots=True)
class StatsPage:
    period: StatsPeriod
    since: datetime
    offset: int
    page_size: int
    total_users: int
    rows: list[UserStats]

    @property
    def page_index(self) -> int:
        return self.offset // self.page_size

    @property
    def total_pages(self) -> int:
        if self.total_users == 0:
            return 1
        return (self.total_users + self.page_size - 1) // self.page_size


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def since_for(period: StatsPeriod) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=_PERIOD_DAYS[period])

    async def fetch_page(
        self,
        period: StatsPeriod,
        *,
        offset: int = 0,
        page_size: int = PAGE_SIZE,
    ) -> StatsPage:
        since = self.since_for(period)
        finished_statuses = (
            AttemptSessionStatus.COMPLETED,
            AttemptSessionStatus.ABORTED,
        )

        base_filter = (
            AttemptSession.status.in_(finished_statuses),
            AttemptSession.ended_at.is_not(None),
            AttemptSession.ended_at >= since,
        )

        total_users_q = await self.session.execute(
            select(func.count(distinct(AttemptSession.bot_user_id))).where(
                *base_filter
            )
        )
        total_users = int(total_users_q.scalar_one() or 0)

        latest_attempt_at = func.max(AttemptSession.ended_at).label("latest_attempt")
        users_q = await self.session.execute(
            select(
                BotUser.id,
                BotUser.telegram_id,
                BotUser.telegram_username,
                BotUser.student_id,
                latest_attempt_at,
            )
            .join(AttemptSession, AttemptSession.bot_user_id == BotUser.id)
            .where(*base_filter)
            .group_by(BotUser.id)
            .order_by(latest_attempt_at.desc(), BotUser.id)
            .offset(max(offset, 0))
            .limit(page_size)
        )

        rows: list[UserStats] = []
        user_id_to_row: dict[int, UserStats] = {}
        for user_id, tg_id, tg_username, student_id, _latest in users_q.all():
            row = UserStats(
                user_id=user_id,
                telegram_id=tg_id,
                telegram_username=tg_username,
                student_id=student_id,
            )
            rows.append(row)
            user_id_to_row[user_id] = row

        if not rows:
            return StatsPage(
                period=period,
                since=since,
                offset=max(offset, 0),
                page_size=page_size,
                total_users=total_users,
                rows=[],
            )

        attempts_q = await self.session.execute(
            select(
                AttemptSession.bot_user_id,
                Subject.name,
                AttemptSession.correct_count,
                AttemptSession.question_ids,
                AttemptSession.attempt_number,
                AttemptSession.status,
                AttemptSession.ended_at,
            )
            .join(Subject, Subject.id == AttemptSession.subject_id)
            .where(
                *base_filter,
                AttemptSession.bot_user_id.in_(list(user_id_to_row.keys())),
            )
            .order_by(AttemptSession.ended_at.desc())
        )

        for (
            user_id,
            subject_name,
            correct_count,
            question_ids,
            attempt_number,
            status,
            ended_at,
        ) in attempts_q.all():
            row = user_id_to_row.get(int(user_id))
            if row is None:
                continue
            total = len(question_ids or [])
            row.attempts.append(
                AttemptStat(
                    subject_name=subject_name,
                    correct=int(correct_count or 0),
                    total=total,
                    attempt_number=int(attempt_number or 0),
                    status=AttemptSessionStatus(status),
                    finished_at=ended_at,
                )
            )

        return StatsPage(
            period=period,
            since=since,
            offset=max(offset, 0),
            page_size=page_size,
            total_users=total_users,
            rows=rows,
        )
