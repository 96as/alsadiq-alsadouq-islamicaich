"""Test settings: run the suite on in-memory SQLite (no Postgres needed).

Usage: python3 manage.py test --settings=config.settings_sqlite_test
"""
import os

os.environ.setdefault('DEBUG', '1')  # tests run in dev mode unless the caller says otherwise

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
