import logging
import re
from multiprocessing import Queue

from yats.twitter_request import TwitterRequest

URL_PROXYSCRAPE = "https://api.proxyscrape.com/"
URL_FREE_PROXY_LIST = "https://free-proxy-list.net"
URL_GITHUB_PROXY_LIST = ("https://raw.githubusercontent.com/"
                         "clarketm/proxy-list/master/proxy-list-raw.txt")


class RequestsHolder:

    def __init__(self, proxy=True, proxy_list=None):
        self.requests = []
        self.proxy = proxy
        if self.proxy:
            self.proxies = Queue()
            if proxy_list is None:
                proxy_list = self._get_proxy_list()
            for add in proxy_list:
                self.proxies.put(add)
        elif proxy_list is not None:
            logging.warning(("a proxy_list was provided but "
                             "the current mode is proxy less"))

    def _get_proxy_list(self):
        addresses = []
        print("get proxy list")
        addresses.extend(self._get_proxyscrape_list())
        addresses.extend(self._get_free_proxy_list())
        addresses.extend(self._get_github_proxy_list())
        return addresses

    def _get_proxyscrape_list(self, max_timeout=1000):
        payload = {
            "request": "getproxies",
            "proxytype": "http",
            "timeout": max_timeout,
            "country": "all",
            "ssl": "yes",
            "anonymity": "all"
        }
        req = TwitterRequest(URL_PROXYSCRAPE)
        req.get(URL_PROXYSCRAPE, params=payload)
        addresses = []
        for add in req.body.split("\r\n"):
            if add:
                a = add.split(":")
                addresses.append((a[0], int(a[1])))
        logging.info(f"fetched {len(addresses)} proxies from proxyscrape")
        return addresses

    def _get_add_port_from_result(self, res):
        addresses = []
        for add in re.findall(
                r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]+",
                res):
            a = add.split(":")
            addresses.append((a[0], int(a[1])))
        return addresses

    def _get_free_proxy_list(self):
        req = TwitterRequest()
        req.get(URL_FREE_PROXY_LIST)
        addresses = self._get_add_port_from_result(req.body)
        logging.info(f"fetched {len(addresses)} proxies from free-proxy-list")
        return addresses

    def _get_github_proxy_list(self):
        req = TwitterRequest()
        req.get(URL_GITHUB_PROXY_LIST)
        addresses = self._get_add_port_from_result(req.body)
        logging.info(f"fetched {len(addresses)} proxies from github list")
        return addresses

    def __len__(self):
        return len(self.requests)

    def get(self):
        if len(self.requests) == 0:
            if self.proxy:
                req = TwitterRequest(proxy=self.proxies)
            else:
                req = TwitterRequest()
        else:
            req = self.requests.pop()
        return req

    def push(self, request):
        logging.debug("pushing request")
        self.requests.append(request)
