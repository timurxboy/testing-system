"""botuser preferred_question_count

Revision ID: b7e9f4a25c81
Revises: ec4d1ee433fa
Create Date: 2026-05-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e9f4a25c81'
down_revision: Union[str, Sequence[str], None] = 'ec4d1ee433fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'botusers',
        sa.Column('preferred_question_count', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('botusers', 'preferred_question_count')
