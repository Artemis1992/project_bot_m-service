"""
WSGI config for requests_service.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_requests.settings")

application = get_wsgi_application()

