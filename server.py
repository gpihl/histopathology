#!/usr/bin/env python3
import json
import scripts.handle_request
import imp
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

class Payload(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)

class S(BaseHTTPRequestHandler):
    def _set_post_response(self, content_type):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header("Content-Encoding", "gzip")
        self.end_headers()
    
    def _set_get_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self._set_get_response()
        with open('pathology_test.html', mode='r', encoding='utf-8') as html_file:
            self.wfile.write(html_file.read().encode('utf-8'))

    def do_POST(self):
        try:
            print('received post to: ' + self.path)
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = Payload(post_data)

            if self.path.split('/')[-1] == 'getimages':
                imp.reload(scripts.handle_request)
                resp = scripts.handle_request.get_response(data)
                self._set_post_response("application/json")
                self.wfile.write(resp)

        except Exception:
            print(traceback.format_exc())

def run(server_class=HTTPServer, handler_class=S, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Closing server')

if __name__ == '__main__':
    from sys import argv
    print('Starting server')        

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
