#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import re
import urlparse, json
import os
import subprocess
import sys


class S(BaseHTTPRequestHandler):
    p = None
    patente = None
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        
        self._set_headers()
        try:
            if re.match("/twitter-stream", self.path):
                try:
                    self.p.terminate()
                except Exception:
                    print "err"
                self.p = subprocess.Popen(["python", "captura.py"])
                return
            elif re.match("/patente", self.path):
                try:
                    self.patente.terminate()
                except Exception:
                    print "err"
                self.patente = subprocess.Popen(["python", "patents.py"])
                return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
            self.wfile.write("<html><body><h1>hi!</h1></body></html>")

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")
        
def run(server_class=HTTPServer, handler_class=S, port=1010):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()