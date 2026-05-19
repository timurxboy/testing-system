from sqladmin import ModelView
from sqlalchemy import Select
from starlette.requests import Request

from apps.auth.admin.mixins import AdminMixin
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject


class QuestionAdmin(AdminMixin, ModelView, model=Question):
    name = "Question"
    name_plural = "Questions"
    category = "Testing"
    icon = "fa-solid fa-circle-question"

    column_list = [
        Question.id,
        Question.subject,
        Question.text,
        Question.is_active,
        Question.created_at,
    ]
    column_searchable_list = [Question.text]
    column_sortable_list = [
        Question.id,
        "subject",
        Question.text,
        Question.is_active,
        Question.created_at,
    ]
    column_labels = {"subject": "Subject", "text": "Question"}

    form_create_rules = ["subject", "text", "is_active", "options"]
    form_edit_rules = ["subject", "text", "is_active", "options"]
    form_ajax_refs = {
        "subject": {
            "fields": ("name",),
            "order_by": "name",
        },
    }

    def sort_query(self, stmt: Select, request: Request) -> Select:
        sort_by = request.query_params.get("sortBy")
        is_desc = request.query_params.get("sort", "asc") == "desc"

        if sort_by == "subject":
            order = Subject.name.desc() if is_desc else Subject.name.asc()
            return (
                stmt.join(Subject, Subject.id == Question.subject_id)
                .order_by(order, Question.id.asc())
            )

        if not sort_by:
            return (
                stmt.join(Subject, Subject.id == Question.subject_id)
                .order_by(Subject.name.asc(), Question.id.asc())
            )

        return super().sort_query(stmt, request)
