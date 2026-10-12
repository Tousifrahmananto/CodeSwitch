import json
import gzip
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from converter.http_client import request_json


class HTTPDeadlineTests(TestCase):
    def test_exported_transport_span_excludes_url_credentials_and_query_strings(self):
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        provider = TracerProvider()
        self.addCleanup(provider.shutdown)
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        with patch('converter.http_client.trace.get_tracer', return_value=provider.get_tracer('audit')), \
             patch('converter.http_client.subprocess.run', return_value=Mock(returncode=0, stdout='{"data":{},"status":200}')):
            request_json('post', 'https://username:private-key@example.com?key=private-key',
                         time.monotonic() + 2, headers={'x-goog-api-key': 'private-key'})
        span, = exporter.get_finished_spans()
        self.assertEqual(span.attributes['server.address'], 'example.com')
        self.assertEqual(span.attributes['http.response.status_code'], 200)
        self.assertNotIn('private-key', str(span.attributes))

    def test_transport_preserves_json_compression_redirects_and_http_errors(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == '/redirect':
                    self.send_response(302)
                    self.send_header('Location', '/json')
                    self.end_headers()
                    return
                body = b'not-json' if self.path == '/invalid' else json.dumps({'text': '猫'}).encode()
                self.send_response(429 if self.path == '/quota' else 200)
                if self.path == '/gzip':
                    body = gzip.compress(body)
                    self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for path in ('/json', '/gzip', '/redirect', '/quota', '/invalid'):
                with self.subTest(path=path):
                    def request():
                        return request_json('get', f'http://127.0.0.1:{server.server_port}{path}',
                                            time.monotonic() + 3, timeout=(1, 1))
                    if path == '/quota':
                        with self.assertRaises(requests.HTTPError) as error:
                            request()
                        self.assertEqual(error.exception.response.status_code, 429)
                    elif path == '/invalid':
                        with self.assertRaises(ValueError):
                            request()
                    else:
                        self.assertEqual(request(), {'text': '猫'})
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_deadline_includes_slow_headers(self):
        received = threading.Event()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                received.set()
                try:
                    for byte in b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}':
                        self.connection.sendall(bytes([byte]))
                        time.sleep(.06)
                except OSError:
                    pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            started = time.monotonic()
            with self.assertRaises(requests.Timeout):
                request_json('post', f'http://127.0.0.1:{server.server_port}',
                             started + 1, timeout=(.2, .2))
            self.assertTrue(received.is_set())
            self.assertLess(time.monotonic() - started, 1.4)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_deadline_interrupts_dripping_and_stalled_bodies(self):
        for drip in (True, False):
            with self.subTest(drip=drip):
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *args):
                        pass

                    def do_POST(self):
                        body = json.dumps({'text': 'x' * 200}).encode()
                        self.send_response(200)
                        self.send_header('Content-Length', str(len(body)))
                        self.end_headers()
                        try:
                            if not drip:
                                time.sleep(1.5)
                            for byte in body:
                                self.wfile.write(bytes([byte]))
                                self.wfile.flush()
                                time.sleep(.01)
                        except OSError:
                            pass
                server = HTTPServer(('127.0.0.1', 0), Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    started = time.monotonic()
                    with self.assertRaises(requests.Timeout):
                        request_json('post', f'http://127.0.0.1:{server.server_port}',
                                     started + 1, timeout=(.1, 2))
                    self.assertLess(time.monotonic() - started, 1.4)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()
