from flask import render_template
from flask_login import login_required
from . import main
from ..models import Post


@main.route('/')
@login_required
def index():
    return render_template('index.html')


@main.route('/write')
@login_required
def write():
    return render_template('write.html')


@main.route('/post/<int:post_id>/edit')
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('edit.html', post=post)
