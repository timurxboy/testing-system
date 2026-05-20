from sqladmin import ModelView
from sqlalchemy import Select
from starlette.requests import Request

from apps.auth.admin.mixins import AdminMixin
from apps.testing.models.answer_option import AnswerOption
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject


class AnswerOptionAdmin(AdminMixin, ModelView, model=AnswerOption):
    name = "Javob varianti"
    name_plural = "Javob variantlari"
    category = "Testlar"
    icon = "fa-solid fa-list-check"

    column_list = [
        AnswerOption.id,
        AnswerOption.question,
        AnswerOption.text,
        AnswerOption.is_correct,
    ]
    column_searchable_list = [AnswerOption.text]
    column_sortable_list = [
        AnswerOption.id,
        "question",
        AnswerOption.text,
        AnswerOption.is_correct,
    ]
    column_labels = {
        "id": "ID",
        "question": "Savol",
        "text": "Matn",
        "is_correct": "To'g'ri",
    }

    form_create_rules = ["question", "text", "is_correct"]
    form_edit_rules = ["question", "text", "is_correct"]
    form_ajax_refs = {
        "question": {
            "fields": ("text",),
            "order_by": "id",
        },
    }

    def sort_query(self, stmt: Select, request: Request) -> Select:
        sort_by = request.query_params.get("sortBy")
        is_desc = request.query_params.get("sort", "asc") == "desc"

        if sort_by == "question":
            subject_order = Subject.name.desc() if is_desc else Subject.name.asc()
            question_order = Question.text.desc() if is_desc else Question.text.asc()
            return (
                stmt.join(Question, Question.id == AnswerOption.question_id)
                .join(Subject, Subject.id == Question.subject_id)
                .order_by(subject_order, question_order, AnswerOption.id.asc())
            )

        if not sort_by:
            return (
                stmt.join(Question, Question.id == AnswerOption.question_id)
                .join(Subject, Subject.id == Question.subject_id)
                .order_by(Subject.name.asc(), Question.text.asc(), AnswerOption.id.asc())
            )

        return super().sort_query(stmt, request)
