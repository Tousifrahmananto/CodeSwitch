import threading

from django.apps import AppConfig


class ConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'converter'

    def ready(self):
        # Pre-populate the Wandbox compiler list in a background thread so the
        # first real user request does not pay the 10-second HTTP cost.
        def _prefetch():
            try:
                from .views import _get_wandbox_compilers
                _get_wandbox_compilers()
            except Exception:
                pass  # Non-critical — the first request will retry

        t = threading.Thread(target=_prefetch, daemon=True)
        t.start()
