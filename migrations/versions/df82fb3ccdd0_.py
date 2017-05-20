"""empty message

Revision ID: df82fb3ccdd0
Revises: c5cc90f23aa7
Create Date: 2017-05-16 12:53:15.146820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df82fb3ccdd0'
down_revision = 'c5cc90f23aa7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_name', sa.String(length=90), nullable=True),
    sa.Column('date_registered', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('bucketlists', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'bucketlists', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'bucketlists', type_='foreignkey')
    op.drop_column('bucketlists', 'user_id')
    op.drop_table('users')
    # ### end Alembic commands ###
