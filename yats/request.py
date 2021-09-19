import urllib
import logging
import http.client
import json
import socket
import re

DEFAULT_TIMEOUT = 15
MAX_RETRY = 1


class Request:

    def __init__(self, proxy=None, use_https=True):
        self.use_https = use_https
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
        if not hasattr(self, "connection"):
            self.recreate_connection(host, reset_proxy=True)
        if self.proxy is not None:
            # self.https.set_tunnel(host)
            # self.recreate_connection(host)
            logging.debug("setting tunnel")
            try:
                self.connection.set_tunnel(host, port=443, headers=headers)
            except RuntimeError:
                logging.debug("Runtime error, refreshing")
                self.recreate_connection(host)
                self.connection.set_tunnel(host, port=443, headers=headers)
                logging.debug("Runtime error, validated")
            logging.debug("tunnel set")
            # self.https.set_tunnel(host, port=443)
        else:
            self.connection.host = host
        self.body = None
        retry_number = 0
        logging.debug("entering the loop")
        while self.body is None:
            logging.debug(f"trying to send request to {host}")
            try:
                if self.proxy is not None:
                    # self.https.request(type, path)
                    self.connection.request(type, path, headers=headers)
                else:
                    self.connection.request(type, path, headers=headers)
            except http.client.BadStatusLine:
                logging.debug("Bad status Line, retrying")
                continue
            except http.client.CannotSendRequest:
                logging.debug("Cannot send request, refreshing connection")
                # self.recreate_connection(host)
                self.recreate_connection(host, reset_proxy=True)
                logging.debug("quitting the send")
                return False
            except socket.timeout:
                logging.debug("timeout while sending request")
                if retry_number < MAX_RETRY:
                    retry_number += 1
                    logging.debug(f"retrying ({retry_number}/{MAX_RETRY})")
                    self.connection.close()
                    self.recreate_connection(host, reset_proxy=False)
                    continue
                else:
                    logging.debug("aborting")
                    return False
            except ConnectionResetError:
                logging.debug("connection refused, recreating")
                return False
            except OSError:
                logging.debug("OSError")
                # self.https.close()
                self.recreate_connection(host, reset_proxy=True)
                # self.recreate_connection(host)
                return False
            # parse the response
            try:
                response = self.connection.getresponse()
            except socket.timeout:
                logging.debug("timeout while reading response, refreshing")
                # self.recreate_connection(host)
                continue
            except http.client.ResponseNotReady:
                logging.debug("Response not ready, continue")
                continue
            except http.client.RemoteDisconnected:
                logging.debug("Remote disconnected")
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
                logging.debug("timeout while reading body, refreshing")
                continue
            except http.client.IncompleteRead:
                logging.debug("incomplete read")
                continue
        logging.debug("body sucessfully read")
        self.connection.close()
        return True

    def recreate_connection(self, host, reset_proxy=False):
        if hasattr(self, "connection"):
            self.connection.close()
        if self.proxy is not None:
            if reset_proxy:
                logging.debug("resetting the proxy")
                if self.proxy.empty():
                    logging.critical("EMPTY PROXY QUEUE")
                proxy = self.proxy.get()
                logging.debug(f"new proxy from queue {proxy}")
                self.current_proxy = proxy
            else:
                proxy = self.current_proxy
            logging.debug(f"create new connection with proxy {proxy[0]}")
            if self.use_https:
                self.connection = http.client.HTTPSConnection(
                    proxy[0],
                    proxy[1],
                    timeout=DEFAULT_TIMEOUT)
            else:
                self.connection = http.client.HTTPConnection(
                    proxy[0],
                    proxy[1],
                    timeout=DEFAULT_TIMEOUT)
            logging.debug("connection resetted")
            # self.https.set_debuglevel(1000)
        else:
            url_parsed = urllib.parse.urlparse(host)
            logging.debug(f"create new connection with {url_parsed.path}")
            if self.use_https:
                self.connection = http.client.HTTPSConnection(
                    url_parsed.path,
                    timeout=DEFAULT_TIMEOUT)
            else:
                self.connection = http.client.HTTPConnection(
                    url_parsed.path,
                    timeout=DEFAULT_TIMEOUT)

    def get(self, url, params=None, headers={}):
        url_parsed = urllib.parse.urlparse(url)
        path = url_parsed.path
        if params is not None:
            payload = urllib.parse.urlencode(params)
            path += f"?{payload}"
        ret = self._send("GET", url_parsed.netloc, path, headers)
        logging.debug(f"return from the send {ret}")
        return ret

    def header(self, name):
        return self.response.getheader(name)

    def to_file(self, file_name):
        with open(file_name, "w") as outfile:
            json.dump({
                "headers": self.headers,
                "body": self.body
            }, outfile, indent=4)
