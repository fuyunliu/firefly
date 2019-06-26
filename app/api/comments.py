# -*- coding: utf-8 -*-

from flask.views import MethodView
from ..models import Comment
from .. import db


class CommentAPI(MethodView):

    def delete(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
