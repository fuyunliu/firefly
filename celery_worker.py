# -*- coding: utf-8 -*-

from app import create_app, create_celery

celery = create_celery(create_app('default'))
celery.autodiscover_tasks(['app.email'])
