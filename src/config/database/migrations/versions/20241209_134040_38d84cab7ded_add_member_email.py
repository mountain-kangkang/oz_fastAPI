"""ADD Member.email

Revision ID: 38d84cab7ded
Revises: 41a4e9d72f0a
Create Date: 2024-12-09 13:40:40.313434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '38d84cab7ded'
down_revision: Union[str, None] = '41a4e9d72f0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('service_member', sa.Column('email', sa.String(length=256), nullable=True))
    op.alter_column('service_member', 'username',
               existing_type=mysql.VARCHAR(length=16),
               nullable=False)
    op.alter_column('service_member', 'password',
               existing_type=mysql.VARCHAR(length=60),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('service_member', 'password',
               existing_type=mysql.VARCHAR(length=60),
               nullable=True)
    op.alter_column('service_member', 'username',
               existing_type=mysql.VARCHAR(length=16),
               nullable=True)
    op.drop_column('service_member', 'email')
    # ### end Alembic commands ###
