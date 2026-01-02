import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_conf.settings")

app = Celery("chatbot_conf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
