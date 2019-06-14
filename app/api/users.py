# -*- coding: utf-8 -*-

from flask import g, request, jsonify, current_app, url_for
from flask.views import MethodView
from .. import db
from ..models import User, Permission
from ..email import send_email
from .errors import forbidden


class UserAPI(MethodView):

    def get(self, user_id):
        if user_id is not None:
            user = User.query.get_or_404(user_id)
            return jsonify(user.dumps())

        page = request.args.get('page', 1, type=int)
        pagination = User.query.paginate(
            page,
            per_page=current_app.config['FIREFLY_PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.user_api', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.user_api', page=page + 1, _external=True)
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
            {'Location': url_for('api.user_api', user_id=user.id)}

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
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()


class UserLikeAPI(MethodView):
    """
    https://127.0.0.1:5000/api/users/1/likes
    """
    def get(self, user_id):
        user = User.query.get_or_404(user_id)


class UserCollectAPI(MethodView):
    """
    https://127.0.0.1:5000/api/users/1/collects
    """
    def get(self, user_id):
        # show user collect posts
        pass
