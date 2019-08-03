from app import create_app, db
from app.models import Role, User, Permission, Post, Comment, Follow

app = create_app('default')


@app.shell_context_processor
def add_all_models():
    return dict(
        db=db, User=User, Role=Role, Follow=Follow,
        Permission=Permission, Post=Post, Comment=Comment)
