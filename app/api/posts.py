# -*- coding: utf-8 -*-

from flask import current_app, g, jsonify, request, url_for, redirect
from flask.views import MethodView
from .. import db
from ..models import Permission, Post
from .errors import forbidden


class PostAPI(MethodView):

    # login required permission write required
    decorators = []

    def get(self, post_id):
        if post_id is not None:
            post = Post.query.get_or_404(post_id)
            return jsonify(post.dumps())
        else:
            size = current_app.config['FIREFLY_PER_PAGE_SIZE']
            max_id = request.args.get('max_id', None, type=int)
            if max_id is None:
                items = Post.query.order_by(Post.id.desc()).limit(size)
            else:
                items = Post.query.filter(Post.id < max_id)\
                        .order_by(Post.id.desc()).limit(size)
            return jsonify({
                'posts': [p.dumps() for p in items],
                'next': url_for('api.post_api',
                                max_id=min(p.id for p in items),
                                _external=True) if items.count() else None
            })

    def post(self):
        post = Post.loads(request.json)
        post.author = g.current_user
        post.author_name = g.current_user.username
        db.session.add(post)
        db.session.commit()
        return jsonify(post.dumps()), 201, \
            {'Location': url_for('api.post_api', post_id=post.id)}

    def put(self, post_id):
        post = Post.query.get_or_404(post_id)
        if g.current_user != post.author and \
                not g.current_user.can(Permission.ADMIN):
            return forbidden('Insufficient permissions')
        post.title = request.json.get('title', post.title)
        post.body = request.json.get('body', post.body)
        db.session.add(post)
        db.session.commit()
        return jsonify(post.dumps())

    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('api.post_api'))


class PostCommentAPI(MethodView):

    decorators = []

    def get(self):
        # show post's comments
        pass


class UserLikePostAPI(MethodView):

    decorators = []

    def get(self):
        # show user like post
        pass
