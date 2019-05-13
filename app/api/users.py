# -*- coding: utf-8 -*-

from flask import g, request, jsonify
from . import api
from .auth import auth
from .. import db


@api.route('/me', methods=['PUT'])
@auth.login_required
def me():
    data = request.get_json()
    name = data.get('name')
    if name is not None:
        g.current_user.name = name
    location = data.get('location')
    if location is not None:
        g.current_user.location = location
    about_me = data.get('about_me')
    if about_me is not None:
        g.current_user.about_me = about_me
    db.session.add(g.current_user)
    db.session.commit()
    return jsonify({'success': 'true'})
