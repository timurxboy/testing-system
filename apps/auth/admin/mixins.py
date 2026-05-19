class AdminMixin:
    form_excluded_columns = (
        "id",
        "created_at",
        "updated_at",
    )