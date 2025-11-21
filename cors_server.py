from http.server import SimpleHTTPRequestHandler, HTTPServer

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    server = HTTPServer(('', port), CORSHTTPRequestHandler)
    print(f"Serving at port {port}")
    server.serve_forever()
