"""Loopback-only deterministic HTTP fixture; never a model performance result."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


@contextmanager
def http_fixture(responder):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(dict(path=self.path, payload=payload,
                                 authorization=self.headers.get('Authorization')))
            status, body, extra_headers = responder(payload, len(requests))
            data = json.dumps(body).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            for key, value in extra_headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            return

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port) + '/v1', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def response(text, usage=None):
    return dict(id='local-fixture', choices=[dict(message=dict(role='assistant', content=text),
                                                 finish_reason='stop')], usage=usage)


def stimulus(payload, number):
    feedback = json.loads(payload['messages'][-1]['content'])
    target = feedback['assigned_target']['id']
    wire = json.dumps(dict(target=target, cycles=256, reset=True,
                           words=[[0x100080, 0x13], [0x100084, 0x6f]]))
    if number % 2 == 0:
        # The runner must forward this invalid reply untouched, not strip fences.
        wire = '```json\n' + wire + '\n```'
    usage = dict(prompt_tokens=23, completion_tokens=11, total_tokens=34) if number % 2 else None
    return 200, response(wire, usage), {}
