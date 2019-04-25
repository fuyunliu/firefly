# -*- coding: utf-8 -*-

from app import celery_app, create_app

app = create_app('default')
app.app_context().push()
