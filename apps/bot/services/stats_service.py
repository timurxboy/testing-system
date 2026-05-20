from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.bot_user import BotUser
from apps.bot.models.test_attempt import TestAttempt
from apps.testing.models.question import Question
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
class SubjectStat:
    subject_name: str
    correct: int  # уникальные правильно решённые вопросы юзером
    total: int  # всего активных вопросов в предмете


@dataclass(slots=True)
class UserStats:
    user_id: int
    telegram_id: int
    telegram_username: str | None
    student_id: str | None
    correct: int  # сумма correct по предметам, к которым касался
    total: int  # сумма active questions в этих предметах
    by_subject: list[SubjectStat] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.student_id or self.telegram_username or f"tg:{self.telegram_id}"

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total * 100) if self.total else 0.0


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

    @property
    def has_prev(self) -> bool:
        return self.offset > 0

    @property
    def has_next(self) -> bool:
        return self.offset + len(self.rows) < self.total_users


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

        # "Уникальные правильные" — для (user, question) считаем 1, если был хоть один is_correct ответ.
        correct_unique = func.count(
            distinct(TestAttempt.question_id)
        ).filter(TestAttempt.is_correct.is_(True))

        total_users_q = await self.session.execute(
            select(func.count(distinct(TestAttempt.bot_user_id))).where(
                TestAttempt.created_at >= since
            )
        )
        total_users = int(total_users_q.scalar_one() or 0)

        rows_result = await self.session.execute(
            select(
                BotUser.id,
                BotUser.telegram_id,
                BotUser.telegram_username,
                BotUser.student_id,
                correct_unique.label("correct"),
            )
            .join(TestAttempt, TestAttempt.bot_user_id == BotUser.id)
            .where(TestAttempt.created_at >= since)
            .group_by(BotUser.id)
            .order_by(correct_unique.desc(), BotUser.id)
            .offset(max(offset, 0))
            .limit(page_size)
        )

        rows: list[UserStats] = []
        user_id_to_row: dict[int, UserStats] = {}
        for user_id, tg_id, tg_username, student_id, _correct in rows_result.all():
            row = UserStats(
                user_id=user_id,
                telegram_id=tg_id,
                telegram_username=tg_username,
                student_id=student_id,
                correct=0,
                total=0,
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

        # Per (user, subject) — уникальные правильные
        breakdown = await self.session.execute(
            select(
                TestAttempt.bot_user_id,
                Subject.id,
                Subject.name,
                correct_unique.label("correct"),
            )
            .join(Subject, Subject.id == TestAttempt.subject_id)
            .where(
                TestAttempt.created_at >= since,
                TestAttempt.bot_user_id.in_(list(user_id_to_row.keys())),
            )
            .group_by(TestAttempt.bot_user_id, Subject.id, Subject.name)
        )

        per_user_subjects: dict[int, list[tuple[int, str, int]]] = {}
        subject_ids: set[int] = set()
        for user_id, sub_id, sub_name, correct in breakdown.all():
            per_user_subjects.setdefault(user_id, []).append(
                (int(sub_id), sub_name, int(correct))
            )
            subject_ids.add(int(sub_id))

        # Всего активных вопросов в каждом из встреченных предметов
        totals_per_subject: dict[int, int] = {}
        if subject_ids:
            totals_q = await self.session.execute(
                select(Question.subject_id, func.count(Question.id))
                .where(
                    Question.subject_id.in_(list(subject_ids)),
                    Question.is_active.is_(True),
                )
                .group_by(Question.subject_id)
            )
            totals_per_subject = {int(sid): int(cnt) for sid, cnt in totals_q.all()}

        # Сборка breakdown + агрегатов по юзерам
        for user_id, row in user_id_to_row.items():
            entries = per_user_subjects.get(user_id, [])
            entries.sort(key=lambda e: e[2], reverse=True)
            for sub_id, sub_name, correct in entries:
                total = totals_per_subject.get(sub_id, 0)
                row.by_subject.append(
                    SubjectStat(subject_name=sub_name, correct=correct, total=total)
                )
                row.correct += correct
                row.total += total

        return StatsPage(
            period=period,
            since=since,
            offset=max(offset, 0),
            page_size=page_size,
            total_users=total_users,
            rows=rows,
        )
