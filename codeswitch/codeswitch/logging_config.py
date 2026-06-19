import json
import logging
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Small JSON formatter that emits only explicitly safe context."""
    SAFE_FIELDS = ('request_id', 'trace_id', 'span_id', 'method', 'route', 'status', 'duration_ms', 'user_id', 'scope')

    def format(self, record):
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'service': os.getenv('SERVICE_NAME', 'codeswitch-backend'),
            'environment': os.getenv('DEPLOYMENT_ENVIRONMENT', 'development'),
            'logger': record.name,
            'message': record.getMessage(),
        }
        for field in self.SAFE_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(',', ':'))
