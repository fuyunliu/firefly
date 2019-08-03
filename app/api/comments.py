from flask import jsonify, g
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


class CommentLikeAPI(MethodView):

    def post(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        g.current_user.like_comment(comment)
        db.session.commit()
        return jsonify({
            'method': 'delete',
            'count': comment.like_count
        })

    def delete(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        g.current_user.dislike_comment(comment)
        db.session.commit()
        return jsonify({
            'method': 'post',
            'count': comment.like_count
        })
