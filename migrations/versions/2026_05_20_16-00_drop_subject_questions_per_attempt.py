"""drop subject questions_per_attempt

Revision ID: c4f2d8a1b39e
Revises: b7e9f4a25c81
Create Date: 2026-05-20 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f2d8a1b39e'
down_revision: Union[str, Sequence[str], None] = 'b7e9f4a25c81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Constraint may or may not exist (was only declared in the Python model
    # but never created via a migration on some databases). Drop conditionally.
    op.execute(
        "ALTER TABLE subjects "
        "DROP CONSTRAINT IF EXISTS ck_subjects_questions_per_attempt_positive"
    )
    op.execute(
        "ALTER TABLE subjects "
        "DROP CONSTRAINT IF EXISTS questions_per_attempt_positive"
    )
    op.drop_column('subjects', 'questions_per_attempt')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'subjects',
        sa.Column(
            'questions_per_attempt',
            sa.Integer(),
            server_default='25',
            nullable=False,
        ),
    )
