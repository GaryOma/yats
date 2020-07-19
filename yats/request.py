import urllib
import logging
import http.client
import json
import socket
import re

DEFAULT_TIMEOUT = 5


class Request:

    def __init__(self):
        pass

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
        try:
            self.https.host = host
        except AttributeError:
            self.https = http.client.HTTPSConnection(host,
                                                     timeout=DEFAULT_TIMEOUT)
        self.body = None
        while self.body is None:
            try:
                self.https.request(type, path, headers=headers)
            except http.client.CannotSendRequest:
                print("Cannot send request, refreshing connection")
                self.https = http.client.HTTPSConnection(
                    host,
                    timeout=DEFAULT_TIMEOUT)
                self.https.request(type, path, headers=headers)
            # parse the response
            try:
                response = self.https.getresponse()
            except socket.timeout:
                logging.error("TIMEOUT WHILE READING RESPONSE, REFRESHING")
                self.https = http.client.HTTPSConnection(
                    host,
                    timeout=DEFAULT_TIMEOUT)
                continue
            # print("RESPONSE STATUS", response.status)
            content_type = self._parse_content_type(
                response.getheader("content-type")
            )
            self.response = response
            self.headers = response.getheaders()
            try:
                self.body = self._parse_body(response.read(), content_type)
            except socket.timeout:
                logging.error("TIMEOUT WHILE READING BODY, REFRESHING")
                self.https = http.client.HTTPSConnection(
                    host,
                    timeout=DEFAULT_TIMEOUT)
                continue

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
