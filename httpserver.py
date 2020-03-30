# coding=utf-8

import SimpleHTTPServer
import SocketServer
import sys


def main():
    """
    cli entry
    """

    port = int(sys.argv[1])

    handler = SimpleHTTPServer.SimpleHTTPRequestHandler

    httpd = SocketServer.TCPServer(("127.0.0.1", port), handler)

    print "start http server at port", port

    httpd.serve_forever()


if __name__ == "__main__":
    main()
