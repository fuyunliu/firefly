# -*- coding: utf-8 -*-

from flask import current_app, g, jsonify, request, url_for
from flask.views import MethodView
from .. import db
from ..models import Permission, Post, Comment
from .errors import forbidden


class PostAPI(MethodView):

    def get(self, post_id):
        if post_id is not None:
            post = Post.query.get_or_404(post_id)
            return jsonify(post.dumps())

        size = current_app.config['PER_PAGE_SIZE']
        max_id = request.args.get('max_id', None, type=int)
        if max_id is None:
            items = Post.query.order_by(Post.id.desc()).limit(size)
        else:
            items = Post.query.filter(Post.id < max_id)\
                .order_by(Post.id.desc()).limit(size)
        return jsonify({
            'posts': [p.dumps() for p in items],
            'next': url_for('api.posts',
                            max_id=min(p.id for p in items),
                            _external=True) if items.count() else None
        })

    def post(self):
        post = Post.loads(request.json)
        post.author = g.current_user
        db.session.add(post)
        db.session.commit()
        return jsonify(post.dumps()), 201, \
            {'Location': url_for('api.posts', post_id=post.id)}

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
        return jsonify({'success': 'true'})


class PostCommentAPI(MethodView):

    def get(self, post_id):
        post = Post.query.get_or_404(post_id)
        page = request.args.get('page', 1, type=int)
        pagination = post.comments.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.post_comment', post_id=post_id,
                           page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.post_comment', post_id=post_id,
                           page=page + 1, _external=True)
        return jsonify({
            'comments': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })

    def post(self, post_id):
        post = Post.query.get_or_404(post_id)
        comment = Comment.loads(request.json)
        comment.post = post
        comment.author = g.current_user
        db.session.add(comment)
        db.session.commit()


class PostLikeAPI(MethodView):

    def post(self, post_id):
        post = Post.query.get_or_404(post_id)
        g.current_user.like_post(post)
        db.session.commit()
        return jsonify({
            'method': 'delete',
            'count': post.like_count
        })

    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        g.current_user.dislike_post(post)
        db.session.commit()
        return jsonify({
            'method': 'post',
            'count': post.like_count
        })


class PostCollectAPI(MethodView):

    def post(self, post_id):
        post = Post.query.get_or_404(post_id)
        g.current_user.collect_post(post)
        db.session.commit()
        return jsonify({
            'method': 'delete',
            'count': post.collect_count
        })

    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        g.current_user.discollect_post(post)
        db.session.commit()
        return jsonify({
            'method': 'post',
            'count': post.collect_count
        })
