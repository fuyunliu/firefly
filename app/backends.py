from flask import current_app, render_template
from flask_mail import Message
from . import mail, celery_app, db
from .models import User


@celery_app.task(serializer='pickle')
def send_async_email(msg):
    mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    send_async_email.delay(msg)


@celery_app.task
def delete_account(user_id):
    user = User.query.get(int(user_id))
    db.session.delete(user)
    db.session.commit()
