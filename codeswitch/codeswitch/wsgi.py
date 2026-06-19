"""
WSGI config for CodeSwitch project.
Exposes the WSGI callable as a module-level variable named ``application``.
"""
import os
from django.core.wsgi import get_wsgi_application
from .observability import configure_opentelemetry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeswitch.settings')

configure_opentelemetry()
try:
    from opentelemetry.instrumentation.django import DjangoInstrumentor
    DjangoInstrumentor().instrument()
except Exception:
    pass

application = get_wsgi_application()
