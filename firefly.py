# -*- coding: utf-8 -*-

from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Follow, Role, Post, Comment, Permission

app = create_app('default')
migrate = Migrate(app, db)


@app.cli.command
def deploy():
    upgrade()
    Role.insert_roles()
    User.add_self_follows()
