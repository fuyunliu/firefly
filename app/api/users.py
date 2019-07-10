# -*- coding: utf-8 -*-

from flask import g, request, jsonify, current_app, url_for
from flask.views import MethodView
from .. import db
from ..models import User, Permission
from ..backends import send_email, delete_account
from .errors import forbidden


class UserAPI(MethodView):

    def get(self, user_id):
        if user_id is not None:
            user = User.query.get_or_404(user_id)
            return jsonify(user.dumps())

        page = request.args.get('page', 1, type=int)
        pagination = User.query.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.users', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.users', page=page + 1, _external=True)
        return jsonify({
            'users': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })

    def post(self):
        user = User.loads(request.json)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        return jsonify(user.dumps()), 201, \
            {'Location': url_for('api.users', user_id=user.id)}

    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        if g.current_user != user and \
                not g.current_user.can(Permission.ADMIN):
            return forbidden('Insufficient permissions')
        user.name = request.json.get('name', user.name)
        user.location = request.json.get('location', user.location)
        user.about_me = request.json.get('about_me', user.about_me)
        db.session.add(user)
        db.session.commit()
        return jsonify(user.dumps())

    def delete(self, user_id):
        # 删除用户，设置 7 天期限，放 celery 删除，发送邮件
        delete_account.delay(user_id)


class UserPostAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        pagination = user.posts.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_post',
                           user_id=user_id,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_post',
                           user_id=user_id,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })


class UserTweetAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        pagination = user.tweets.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_tweet',
                           user_id=user_id,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_tweet',
                           user_id=user_id,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })


class UserCommentAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        pagination = user.comments.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_comment',
                           user_id=user_id,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_comment',
                           user_id=user_id,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })


class UserFavoriteAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        pagination = user.favorites.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_favorite',
                           user_id=user_id,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_favorite',
                           user_id=user_id,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })


class UserLikeAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        type = request.args.get('type', 'post', type=str)
        page = request.args.get('page', 1, type=int)
        bq = {
            'post': user.liked_posts,
            'tweet': user.liked_tweets,
            'comment': user.liked_comments
        }
        pagination = bq[type].paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_like',
                           user_id=user_id,
                           type=type,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_like',
                           user_id=user_id,
                           type=type,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })


class UserCollectAPI(MethodView):

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        pagination = user.collected_posts.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_collect',
                           user_id=user_id,
                           page=page - 1,
                           _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_collect',
                           user_id=user_id,
                           page=page + 1,
                           _external=True)
        return jsonify({
            'data': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })
