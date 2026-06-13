from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['parkrangx.pythonanywhere.com']

# 보안 설정
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# 정적 파일
STATIC_ROOT = BASE_DIR / 'staticfiles'
