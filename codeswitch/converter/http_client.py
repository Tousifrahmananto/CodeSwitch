import json
import gzip
import zlib
import time

import requests
from urllib3.exceptions import ReadTimeoutError, HTTPError as TransportError


def request_json(method, url, deadline, **kwargs):
    kwargs['headers'] = {**kwargs.get('headers', {}), 'Accept-Encoding': 'identity'}
    response = getattr(requests, method)(url, stream=True, **kwargs)
    try:
        response.raise_for_status()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise requests.Timeout()
        # ponytail: urllib3 exposes no public transport timeout setter; update with transport changes.
        transport = response.raw._fp.fp.raw._sock
        read_timeout = kwargs['timeout'][1]
        transport.settimeout(min(read_timeout, remaining))
        body = bytearray()
        try:
            for chunk in response.raw.stream(amt=1, decode_content=False):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise requests.Timeout()
                body.extend(chunk)
                transport.settimeout(min(read_timeout, remaining))
        except ReadTimeoutError as exc:
            raise requests.Timeout() from exc
        except TransportError as exc:
            raise requests.RequestException() from exc
        except requests.ConnectionError as exc:
            if exc.args and isinstance(exc.args[0], ReadTimeoutError):
                raise requests.Timeout() from exc
            raise
        encoding = response.headers.get('Content-Encoding', '').lower()
        if encoding == 'gzip':
            body = gzip.decompress(body)
        elif encoding == 'deflate':
            body = zlib.decompress(body)
        elif encoding not in ('', 'identity'):
            raise ValueError('Unsupported response encoding.')
        if time.monotonic() >= deadline:
            raise requests.Timeout()
        return json.loads(body)
    finally:
        response.close()
