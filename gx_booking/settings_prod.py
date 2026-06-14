from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['parkrangx.pythonanywhere.com']
CSRF_TRUSTED_ORIGINS = ['https://parkrangx.pythonanywhere.com']
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
STATIC_ROOT = BASE_DIR / 'staticfiles'
