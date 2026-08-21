"""Django project configuration package.

The Celery app is loaded from ``CoreConfig.ready`` after split settings have
finished evaluating. The Celery CLI still discovers ``config.celery:app`` when
invoked with ``-A config``.
"""
