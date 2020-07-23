import urllib
import logging
import http.client
import json
import socket
import re

DEFAULT_TIMEOUT = 15


class Request:

    def __init__(self, proxy=None):
        self.proxy = proxy

    def _parse_content_type(self, c_type):
        res = re.match(r"(?P<type>\w+?)\/(?P<app>\w+?);"
                       r"\s*charset=(?P<charset>.+)",
                       c_type)
        return res.groupdict()

    def _parse_body(self, raw, content_type):
        if content_type["app"] == "json":
            body = json.loads(raw)
        else:
            body = raw.decode(content_type["charset"])
        return body

    def _send(self, type, host, path, headers):
        logging.debug("will send" + host)
        if not hasattr(self, "https"):
            self.recreate_connection(host)
        if self.proxy is not None:
            # self.https.set_tunnel(host)
            self.recreate_connection(host)
            logging.debug("setting tunnel")
            self.https.set_tunnel(host, port=443, headers=headers)
            logging.debug("tunnel set")
            # self.https.set_tunnel(host, port=443)
        else:
            self.https.host = host
        self.body = None
        logging.debug("entering the loop")
        while self.body is None:
            logging.debug(f"trying to send request to {host}")
            try:
                if self.proxy is not None:
                    # self.https.request(type, path)
                    self.https.request(type, path, headers=headers)
                else:
                    self.https.request(type, path, headers=headers)
            except http.client.CannotSendRequest:
                logging.error("Cannot send request, refreshing connection")
                self.recreate_connection(host)
                continue
            except socket.timeout:
                logging.error("timeout while sending request, refreshing")
                # self.recreate_connection(host)
                continue
            except ConnectionResetError:
                logging.error("connection refused, recreating")
                continue
            except OSError:
                logging.error("OSError")
                continue
            # parse the response
            try:
                response = self.https.getresponse()
            except socket.timeout:
                logging.error("timeout while reading response, refreshing")
                # self.recreate_connection(host)
                continue
            logging.debug(f"response status {response.status}")
            content_type = self._parse_content_type(
                response.getheader("content-type")
            )
            self.response = response
            self.headers = response.getheaders()
            try:
                self.body = self._parse_body(response.read(), content_type)
            except socket.timeout:
                # self.recreate_connection(host)
                logging.error("timeout while reading body, refreshing")
                continue
        logging.debug("body sucessfully read")
        self.https.close()

    def recreate_connection(self, host):
        if hasattr(self, "https"):
            self.https.close()
        if self.proxy is not None:
            logging.debug(f"create new connection with proxy {self.proxy[0]}")
            self.https = http.client.HTTPSConnection(
                self.proxy[0],
                self.proxy[1],
                timeout=DEFAULT_TIMEOUT)
            # self.https.set_debuglevel(1000)
        else:
            url_parsed = urllib.parse.urlparse(host)
            logging.debug(f"create new connection with {url_parsed.netloc}")
            self.https = http.client.HTTPSConnection(
                url_parsed.path,
                timeout=DEFAULT_TIMEOUT)

    def get(self, url, params=None, headers={}):
        url_parsed = urllib.parse.urlparse(url)
        path = url_parsed.path
        if params is not None:
            payload = urllib.parse.urlencode(params)
            path += f"?{payload}"
        self._send("GET", url_parsed.netloc, path, headers)

    def header(self, name):
        return self.response.getheader(name)

    def to_file(self, file_name):
        with open(file_name, "w") as outfile:
            json.dump({
                "headers": self.headers,
                "body": self.body
            }, outfile, indent=4)
