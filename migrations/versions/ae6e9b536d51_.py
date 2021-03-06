"""empty message

Revision ID: ae6e9b536d51
Revises: e54d49e8083f
Create Date: 2019-05-18 18:56:44.516853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae6e9b536d51'
down_revision = 'e54d49e8083f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('author_name', sa.String(length=64), nullable=True))
    op.add_column('posts', sa.Column('title', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_posts_title'), 'posts', ['title'], unique=False)
    op.drop_index('ix_user_like_comment_create_time', table_name='user_like_comment')
    op.drop_index('ix_user_like_post_create_time', table_name='user_like_post')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_user_like_post_create_time', 'user_like_post', ['create_time'], unique=False)
    op.create_index('ix_user_like_comment_create_time', 'user_like_comment', ['create_time'], unique=False)
    op.drop_index(op.f('ix_posts_title'), table_name='posts')
    op.drop_column('posts', 'title')
    op.drop_column('posts', 'author_name')
    # ### end Alembic commands ###
