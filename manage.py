# -*- coding: utf-8 -*-

from app import create_app, db, rdb
from app.models import Role, Follow, User, Permission, Post, Comment, \
    UserLikeComment, UserLikePost

app = create_app('default')


@app.shell_context_processor
def add_all_models():
    return dict(
        db=db, rdb=rdb, User=User, Role=Role, Follow=Follow,
        Permission=Permission, Post=Post, Comment=Comment,
        UserLikePost=UserLikePost, UserLikeComment=UserLikeComment)
