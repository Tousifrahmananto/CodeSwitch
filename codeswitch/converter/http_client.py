import json
import subprocess
import sys
import time
from urllib.parse import urlsplit
from opentelemetry import trace

import requests


def request_json(method, url, deadline, **kwargs):
    with trace.get_tracer(__name__).start_as_current_span(
        'http.request', kind=trace.SpanKind.CLIENT,
        attributes={'http.request.method': method.upper(), 'server.address': urlsplit(url).hostname or ''},
    ) as span:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise requests.Timeout()
        # A process can be stopped during DNS, slow headers, and decompression as well as body reads.
        try:
            result = subprocess.run(
                [sys.executable, __file__],
                input=json.dumps({'method': method, 'url': url, 'kwargs': kwargs}),
                capture_output=True, text=True, encoding='utf-8', timeout=remaining,
            )
        except subprocess.TimeoutExpired as exc:
            raise requests.Timeout() from exc
        if result.returncode:
            raise requests.RequestException('HTTP transport failed.')
        response = json.loads(result.stdout)
        if 'status' in response:
            span.set_attribute('http.response.status_code', response['status'])
        if response.get('error') == 'timeout':
            raise requests.Timeout()
        if response.get('error') == 'http':
            failed = requests.Response()
            failed.status_code = response['status']
            raise requests.HTTPError(response=failed)
        if response.get('error') == 'invalid':
            raise ValueError('Invalid JSON response.')
        if response.get('error'):
            raise requests.RequestException('HTTP transport failed.')
        return response['data']


def _request_in_child(request):
    kwargs = request['kwargs']
    if isinstance(kwargs.get('timeout'), list):
        kwargs['timeout'] = tuple(kwargs['timeout'])
    kwargs['headers'] = {**kwargs.get('headers', {}), 'Accept-Encoding': 'identity'}
    try:
        with requests.request(request['method'], request['url'], stream=True, **kwargs) as response:
            response.raise_for_status()
            return {'data': response.json(), 'status': response.status_code}
    except requests.Timeout:
        return {'error': 'timeout'}
    except requests.HTTPError as exc:
        return {'error': 'http', 'status': exc.response.status_code}
    except ValueError:
        return {'error': 'invalid'}
    except requests.RequestException:
        return {'error': 'unavailable'}


if __name__ == '__main__':
    json.dump(_request_in_child(json.load(sys.stdin)), sys.stdout)
