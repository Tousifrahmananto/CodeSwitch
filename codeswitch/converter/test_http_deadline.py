import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import TestCase

import requests
from converter.http_client import request_json


class HTTPDeadlineTests(TestCase):
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
                                time.sleep(.35)
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
                                     started + .15, timeout=(.1, .5))
                    self.assertLess(time.monotonic() - started, .3)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()
