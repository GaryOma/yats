import logging

from yats.twitter_request import TwitterRequest

URL_PROXYSCRAPE = "https://api.proxyscrape.com/"


class RequestsHolder:

    def __init__(self, proxy=True):
        self.requests = []
        self.proxy = proxy
        if self.proxy:
            self.proxies = self._get_proxy_list()

    def _get_proxy_list(self):
        addresses = self._get_proxyscrape_list()
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

    def __len__(self):
        return len(self.requests)

    def get(self):
        if len(self.requests) == 0:
            if self.proxy:
                proxy = self.proxies.pop()
                logging.debug(f"using proxy {proxy}")
                req = TwitterRequest(proxy=proxy)
            else:
                req = TwitterRequest()
        else:
            req = self.requests.pop()
        return req

    def push(self, request):
        logging.debug("pushing request")
        self.requests.append(request)
