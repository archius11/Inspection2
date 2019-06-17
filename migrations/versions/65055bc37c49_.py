"""empty message

Revision ID: 65055bc37c49
Revises: 35583092d4b8
Create Date: 2019-06-05 12:57:48.158352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65055bc37c49'
down_revision = '35583092d4b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('norms', 'defect')
    op.drop_column('norms', 'major')
    op.drop_column('norms', 'minor')
    op.drop_column('norms', 'default')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('norms', sa.Column('default', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('norms', sa.Column('minor', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('norms', sa.Column('major', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('norms', sa.Column('defect', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###