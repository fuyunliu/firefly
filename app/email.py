# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from celery import shared_task
from . import mail, celery_app


@shared_task
def add(x, y):
    return x + y


@shared_task(serializer='pickle')
def send_async_email(msg):
    mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    send_async_email.delay(msg)
