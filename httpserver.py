# coding=utf-8
from __future__ import print_function
import sys

if sys.version_info.major == 2:
    import SimpleHTTPServer as HTTPServer
    import SocketServer
else:
    import http.server as HTTPServer
    import socketserver as SocketServer


def main():
    """
    cli entry
    """

    port = int(sys.argv[1])

    handler = HTTPServer.SimpleHTTPRequestHandler

    httpd = SocketServer.TCPServer(("127.0.0.1", port), handler)

    print("start http server at port", port)

    httpd.serve_forever()


if __name__ == "__main__":
    main()
