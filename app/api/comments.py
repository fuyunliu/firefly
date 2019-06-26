# -*- coding: utf-8 -*-

from flask import jsonify
from flask.views import MethodView
from ..models import Comment
from .. import db


class CommentAPI(MethodView):

    def get(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        return jsonify(comment.dumps())

    def delete(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
