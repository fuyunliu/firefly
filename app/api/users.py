# -*- coding: utf-8 -*-

from flask import g, request, jsonify, current_app, url_for
from flask.views import MethodView
from . import api
from .auth import auth
from .. import db
from ..models import User
from ..email import send_email
from .errors import forbidden


class UserAPI(MethodView):

    decorators = []

    def get(self, user_id):
        if user_id is not None:
            user = User.query.get_or_404(user_id)
            return jsonify(user.dumps())
        else:
            page = request.args.get('page', 1, type=int)
            pagination = User.query.paginate(
                page,
                per_page=current_app.config['FIREFLY_PER_PAGE_SIZE'],
                error_out=False)
            prev = None
            if pagination.has_prev:
                prev = url_for('api.get_users', page=page-1)
            next = None
            if pagination.has_next:
                next = url_for('api.get_users', page=page+1)
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
            {'Location': url_for('api.get_user', id=user.id)}

    def put(self, user_id):
        # 修改当前用户，或者某一用户
        post = Post.query.get_or_404(post_id)
        if g.current_user != post.author and \
                not g.current_user.can(Permission.ADMIN):
            return forbidden('Insufficient permissions')
        post.title = request.json.get('title', post.title)
        post.body = request.json.get('body', post.body)
        db.session.add(post)
        db.session.commit()
        return jsonify(post.dumps())

    def delete(self, user_id):
        # 删除用户，设置 7 天期限，放 celery 删除，发送邮件
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return 'ok'


@api.route('/me', methods=['PUT'])
@auth.login_required
def me():
    name = request.json.get('name')
    if name is not None:
        g.current_user.name = name
    location = request.json.get('location')
    if location is not None:
        g.current_user.location = location
    about_me = request.json.get('about_me')
    if about_me is not None:
        g.current_user.about_me = about_me
    db.session.add(g.current_user)
    db.session.commit()
    return jsonify(g.current_user.dumps())
