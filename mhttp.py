#!/usr/bin/env python

from threading import Thread
from os.path import exists, splitext
import time
import socket

def log(msg, level = "info"):
    levels = {"info" : "\033[92mINFO \033[0m :",
              "error": "\033[91mERROR\033[0m :",
              "debug": "\033[94mDEBUG\033[0m :",
              "warn" : "\033[93mWARN \033[0m :"}

    print(time.strftime("\033[90m[%Y-%m-%d %H:%M:%S]", time.localtime()), levels[level], msg)

class Server:
    def __init__(self, host = "localhost", port = 8080, pwd = '.'):
        self.host = host
        self.port = port
        self.pwd  = pwd
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        log(f"Created socket object <binding \033[97m{self.host}:{self.port}\033[0m>")
        self.status = {200: "OK", 403: "Forbidden", 404: "Not Found", 500: "Internal Server Error", 502: "Bad Gateway"}
        self.contents = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
                         ".png": "image/png", ".jpg": "image/jpg", ".jpeg": "image/jpeg", ".gif": "image/gif",
                         ".svg": "image/svg+xml", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2",
                         ".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject", ".pdf": "application/pdf",
                         ".zip": "application/zip", ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".txt": "text/plain"}

    def status_html(self, code):
        return  f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>{code} {self.status[code]} - MHTTP Server</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1 align = "center">{code} {self.status[code]}</h1><hr />
                <p  align = "center">
                    MHTTP Server —— by Logic.<br />—— 馨香盈怀袖，路远莫致之。——
                </p>
            </body>
        </html>
        """.encode("utf-8")
    def get_path(self, client, path, cli_addr):
        if path == '/':
            if exists(f"{self.pwd}/index.html"):
                with open(f"{self.pwd}/index.html", 'r') as f:
                    self.send(client, f.read().encode("utf-8"), "/index.html", 200, "text/html", cli_addr)
            elif exists(f"{self.pwd}/index.htm"):
                with open(f"{self.pwd}/index.htm", 'r') as f:
                    self.send(client, f.read().encode("utf-8"), "/index.htm", 200, "text/html", cli_addr)
            else:
                self.send(client, self.status_html(404), "builtin", 404, "text/html", cli_addr)
                log(f"Sent status \033[97m404 {self.status[404]}\033[0m to \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m.")
        else:
            if exists(self.pwd + path): 
                if splitext(path)[1] in self.contents and self.contents[splitext(path)[1]].startswith("text/") or splitext(path)[1] in {".js", ".txt"}:
                    with open(self.pwd + path, 'r') as f:
                        self.send(client, f.read().encode("utf-8"), path, 200,
                            self.contents[splitext(path)[1]] if splitext(path)[1] in self.contents else "application/octet-stream", cli_addr)
                else:
                    with open(self.pwd + path, "rb") as f:
                        self.send(client, f.read(), path, 200,
                            self.contents[splitext(path)[1]] if splitext(path)[1] in self.contents else "application/octet-stream", cli_addr)

            else:
                self.send(client, self.status_html(404), "builtin", 404, "text/html", cli_addr)
                log(f"Sent status \033[97m404 {self.status[404]}\033[0m to \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m.")

    def handle(self, client, cli_addr):
        try:
            data = client.recv(8192).decode("utf-8")
            log(f"Received data from \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m:")
            print("\033[90m  ", '  '.join('' + line for line in data.splitlines(True)), "\033[0m", sep = '')
            method, path, version = data.split('\n')[0].split()
            log(f"Request method: \033[97m{method}\033[0m; path: \033[97m{path}\033[0m; version: \033[97m{version}\033[0m.")
            self.get_path(client, path, cli_addr)
        except Exception as expt:
            log(f"Failed to handle request from \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m: {expt}", "error")
            self.send(client, self.status_html(500), "builtin", 500, "text/html", cli_addr)
            log(f"Sent status \033[97m500 {self.status[500]}\033[0m to \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m.")
            client.close()
            log(f"Connection of \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m closed.")

    def send(self, client, res, path, code, content_type, cli_addr):
        client.send((
        f"HTTP/1.1 {code} {self.status[code]}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(res)}\r\n"
        "Connection: close\r\n"
        "\r\n").encode("utf-8") + res)
        log(f"Sent response \033[97m{path} {content_type}\033[0m to \033[97m{cli_addr[0]}:{cli_addr[1]}\033[0m.")

    def run(self):
        self.socket.listen(5)
        log(f"Listening on \033[97m{self.host}:{self.port}\033[0m...")
        while True:
            try:
                client = self.socket.accept()
                Thread(target = self.handle, args = client).start()
                log(f"Received request from \033[97m{client[1][0]}:{client[1][1]}\033[0m.")
            except KeyboardInterrupt:
                print()
                log(f"Interrupted by user. Exit.")
                break
            except Exception as expt:
                log("Failed to receive data: {expt}", "error")

        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()
        log("Socket closed.")

if __name__ == "__main__":
    print("\033[97mMHTTP Server\033[0m\nVersion 0.1.0.0 (Pre-build)\n\nCopyright (c) 2026 Logic\nAll Rights Reserved.\n")
    server = Server(port = 8080)
    server.run()

