# -*- coding: utf-8 -*-

from flask import g, jsonify
from flask_httpauth import HTTPTokenAuth
from ..models import User
from . import api

auth = HTTPTokenAuth()


@auth.verify_token
def verify_token(token):
    g.current_user = User.verify_auth_token(token)
    g.token_used = True
    return g.current_user is not None
