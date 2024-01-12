# import socket
# import select
# from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
#
#
# class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
#     def do_CONNECT(self):
#         server_address = self.path.split(":")
#         target_server = (server_address[0], int(server_address[1]) if len(server_address) > 1 else 443)
#         target_socket = None
#
#         try:
#             # Establish a connection to the destination server
#             target_socket = socket.create_connection(target_server)
#             self.send_response(200, 'Connection Established')
#             self.end_headers()
#
#             # Set up a bidirectional transfer of data
#             connections = [self.connection, target_socket]
#             while True:
#                 readable, _, exceptional = select.select(connections, [], connections, 10)
#                 if exceptional:
#                     break
#
#                 for sock in readable:
#                     other = target_socket if sock is self.connection else self.connection
#                     data = sock.recv(4096)
#                     if not data:  # No more data
#                         break
#                     other.sendall(data)
#
#         except Exception as e:
#             self.send_error(500, str(e))
#
#         finally:
#             if target_socket:
#                 target_socket.close()
#
#     # To handle HTTP requests, you need to implement do_GET, do_POST, etc.
#     # This is a basic example for do_GET.
#     def do_GET(self):
#         self.send_error(501, "Not Implemented")
#
#     def do_POST(self):
#         self.send_error(501, "Not Implemented")
#
#     # def log_message(self, format, *args):
#     #     return  # Override to disable automatic logging of incoming requests
#
#
# if __name__ == '__main__':
#     port = 8000
#     server_address = ('', port)
#     httpd = ThreadingHTTPServer(server_address, ProxyHTTPRequestHandler)
#     print(f'Serving HTTP and HTTPS on port {port}...')
#     httpd.serve_forever()


import socket
import select
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        server_address = self.path.split(":")
        target_server = (server_address[0], int(server_address[1]) if len(server_address) > 1 else 443)
        target_socket = None

        try:
            # Establish a connection to the destination server
            target_socket = socket.create_connection(target_server)
            self.send_response(200, 'Connection Established')
            self.end_headers()

            # Set up a bidirectional transfer of data
            connections = [self.connection, target_socket]
            while True:
                readable, _, exceptional = select.select(connections, [], connections, 10)
                if exceptional:
                    break

                for sock in readable:
                    other = target_socket if sock is self.connection else self.connection
                    data = sock.recv(4096)
                    if not data:  # No more data
                        break
                    other.sendall(data)

        except Exception as e:
            self.send_error(500, str(e))

        finally:
            if target_socket:
                target_socket.close()

    def forward_request(self, method):
        url = urlparse(self.path)
        target_server = (url.hostname, url.port if url.port else 80)
        target_socket = None

        try:
            # Establish a connection to the destination server
            target_socket = socket.create_connection(target_server)

            # Define custom headers
            custom_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/580.3029.110 Safari/537.36',
            }

            # Forward the request line
            request_line = f"{method} {url.path} HTTP/1.1\r\n"
            target_socket.sendall(request_line.encode())

            # Forward the original headers along with custom headers
            for header, value in self.headers.items():
                target_socket.sendall(f"{header}: {value}\r\n".encode())
            for header, value in custom_headers.items():
                target_socket.sendall(f"{header}: {value}\r\n".encode())
            target_socket.sendall(b"\r\n")

            # Forward the request body if present (for POST requests)
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                target_socket.sendall(body)

            # Receive the response from the target server and forward it to the client
            while True:
                data = target_socket.recv(4096)
                if not data:
                    break
                self.wfile.write(data)

        except Exception as e:
            self.send_error(500, str(e))

        finally:
            if target_socket:
                target_socket.close()

    def do_GET(self):
        self.forward_request("GET")

    def do_POST(self):
        self.forward_request("POST")

    # ... rest of the existing code ...


if __name__ == '__main__':
    port = 8000
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ProxyHTTPRequestHandler)
    print(f'Serving HTTP and HTTPS on port {port}...')
    httpd.serve_forever()
