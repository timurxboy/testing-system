"""fix refresh_tokens: bigint id, timezone on expires_at, cascade FK

Revision ID: a1b2c3d4e5f6
Revises: 13519c1d1dc9
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '13519c1d1dc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change id from Integer to BigInteger
    op.alter_column(
        'refresh_tokens',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
    )

    # Change expires_at from DateTime to DateTime(timezone=True)
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )

    # Drop old FK and recreate with ON DELETE CASCADE
    op.drop_constraint(
        'fk_refresh_tokens_user_id_adminusers',
        'refresh_tokens',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'fk_refresh_tokens_user_id_adminusers',
        'refresh_tokens',
        'adminusers',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    # Restore FK without CASCADE
    op.drop_constraint(
        'fk_refresh_tokens_user_id_adminusers',
        'refresh_tokens',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'fk_refresh_tokens_user_id_adminusers',
        'refresh_tokens',
        'adminusers',
        ['user_id'],
        ['id'],
    )

    # Revert expires_at to DateTime without timezone
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
    )

    # Revert id from BigInteger to Integer
    op.alter_column(
        'refresh_tokens',
        'id',
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
    )
