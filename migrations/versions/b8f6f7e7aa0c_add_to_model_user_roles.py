"""add to model User roles

Revision ID: b8f6f7e7aa0c
Revises: 74f88cb228e2
Create Date: 2025-04-10 16:26:03.480210

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8f6f7e7aa0c"
down_revision: Union[str, None] = "74f88cb228e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    connection = op.get_bind()
    stmt = "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole')"
    result = connection.execute(sa.text(stmt)).scalar()
    if not result:
        op.execute("CREATE TYPE userrole AS ENUM ('USER', 'ADMIN')")
    op.add_column(
        "users",
        sa.Column("role", sa.Enum("USER", "ADMIN", name="userrole"), nullable=True),
    )
    op.execute("UPDATE users SET role = 'USER' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "role")
    op.execute("DROP TYPE userrole")
    # ### end Alembic commands ###
