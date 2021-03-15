"""Added Card table

Revision ID: 402880fe83d7
Revises: 88602d3e9a37
Create Date: 2021-03-15 00:52:44.640699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '402880fe83d7'
down_revision = '88602d3e9a37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('card')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('card',
    sa.Column('CardID', sa.INTEGER(), nullable=False),
    sa.Column('UserID', sa.INTEGER(), nullable=True),
    sa.Column('CardNo', sa.VARCHAR(length=25), nullable=True),
    sa.Column('Name', sa.VARCHAR(length=50), nullable=True),
    sa.Column('CVV', sa.VARCHAR(length=5), nullable=True),
    sa.Column('Expiry', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['UserID'], ['user.UserID'], ),
    sa.PrimaryKeyConstraint('CardID')
    )
    # ### end Alembic commands ###