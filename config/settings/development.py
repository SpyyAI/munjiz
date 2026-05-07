from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use ManifestStorage only in prod — dev uses simple static
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
