from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir('static')

class MyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Type', 'text/html')
        super().end_headers()

server = HTTPServer(('localhost', 8001), MyHandler)
print("Test server running at http://localhost:8001")
server.serve_forever()
