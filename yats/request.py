import urllib
import http.client
import json
import re
import ssl
import copyreg
# from multiprocessing.reduction import rebuild_socket, reduce_socket


class Request:

    def __init__(self):
        # copyreg.pickle(ssl.SSLSocket, reduce_socket, rebuild_socket)
        copyreg.pickle(ssl.SSLContext, self._save_sslcontext)
        pass

    def _save_sslcontext(obj):
        return obj.__class__, (obj.protocol,)

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
            self.https = http.client.HTTPSConnection(host)
        try:
            self.https.request(type, path, headers=headers)
        except http.client.CannotSendRequest:
            print("Cannot send request, refreshing connection")
            self.https = http.client.HTTPSConnection(host)
            self.https.request(type, path, headers=headers)
        # parse the response
        response = self.https.getresponse()
        # print("RESPONSE STATUS", response.status)
        content_type = self._parse_content_type(
            response.getheader("content-type")
        )
        self.response = response
        self.headers = response.getheaders()
        self.body = self._parse_body(response.read(), content_type)

    def get(self, url, params=None, headers={}):
        url_parsed = urllib.parse.urlparse(url)
        path = url_parsed.path
        if params is not None:
            payload = urllib.parse.urlencode(params)
            path += f"?{payload}"
        self._send("GET", url_parsed.netloc, path, headers)

    def header(self, name):
        return self.response.getheader(name)
