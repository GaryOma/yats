import re
import sys
import logging

from yats.request import Request
from yats.custom_datetime import CustomDateTime as datetime

TWITTER_URL = "https://mobile.twitter.com/"
GRAPHQL_URL = "https://api.twitter.com/graphql/"
USER_INFO_QL_PATH = "UserByScreenName"
USER_INFO_QL_ID = "-xfUfZsnR_zqjFd-IfrN5A"
USER_AGENT = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/83.0.4103.97 Safari/537.36"),
}
TOKEN_BEARER = ("AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
                "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")


class TwitterRequest(Request):

    def __init__(self, fast_mode=True):
        if fast_mode:
            self.graphql_ext = USER_INFO_QL_ID
            self.token_bearer = TOKEN_BEARER
        self.token_guest = None
        self.url_timeline = "https://api.twitter.com/2/timeline/profile/"
        self.url_search = "https://api.twitter.com/2/search/adaptive.json"
        super().__init__()

    def _is_unset(self, attributes):
        if isinstance(attributes, list):
            for attribute in attributes:
                if not hasattr(self, attribute) or attribute is None:
                    return True
            return False
        else:
            return not hasattr(self, attribute) or attribute is None

    def _get_initial_request(self):
        logging.debug(f"get initial request {TWITTER_URL}")
        self.get(TWITTER_URL, headers=USER_AGENT)
        if re.search(r'\"x-rate-limit-remaining\":\"0\"', self.body):
            timestamp = re.search(r'\"x-rate-limit-reset\":\"(\d+)\"',
                                  self.body).group(1)
            dt = datetime.fromtimestamp(int(timestamp))
            logging.critical(f"cooldown until {dt.isoformat()}")
            logging.warning("recreating ?")
            self.recreate_connection(TWITTER_URL)
            self.get(TWITTER_URL, headers=USER_AGENT)
        self.token_guest = re.search(r"gt=(\w+)",
                                     self.body).group(1)
        self.main_js = re.search(r"https://abs.twimg.com/responsive-web/"
                                 r"web(?:_legacy)?/"
                                 r"(main.(?:.*?)\.js)",
                                 self.body).group(0)

    def _get_main_js_page(self):
        logging.debug("get the token_bearer and graphql_ext")
        self.get(self.main_js)
        self.token_bearer = re.search(r's=\"([a-zA-Z0-9+%]{10,}?)\"',
                                      self.body).group(1)
        regex = r"queryId:\"(.*?)\",operationName:\"(.*?)\""
        queries = re.findall(regex, self.body)
        pair = next(x for x in queries if x[1] == USER_INFO_QL_PATH)
        self.graphql_ext = pair[0]

    def _get_connection_infos(self):
        if self._is_unset(["token_guest", "main_js"]):
            self._get_initial_request()
        if self._is_unset(["graphql_ext", "token_bearer"]):
            self._get_main_js_page()

    def _get_cursor(self, timeline):
        instructions = timeline["instructions"]
        for instruction in instructions:
            if "addEntries" in instruction.keys():
                for entry in instruction["addEntries"]["entries"]:
                    if "cursor-bottom" in entry["entryId"]:
                        content = entry["content"]
                        cursor = content["operation"]["cursor"]["value"]
                        return cursor
        for instruction in instructions:
            if "replaceEntry" in instruction.keys():
                replace = instruction["replaceEntry"]
                if replace["entryIdToReplace"] == "sq-cursor-bottom":
                    content = replace["entry"]["content"]
                    cursor = content["operation"]["cursor"]["value"]
                    return cursor
        else:
            cursor = None
            logging.error("No new cursor")
            sys.exit(0)
        return cursor

    def get_profile_request(self, username):
        self._get_connection_infos()
        user_url = GRAPHQL_URL + self.graphql_ext + "/" + USER_INFO_QL_PATH
        logging.debug(f"Getting {username} infos...")
        payload = {
            "variables": (f'{{"screen_name":"{username}",'
                          f'"withHighlightedLabel":true}}')
        }
        headers = {
            "authorization": f"Bearer {self.token_bearer}"
        }
        self.get(user_url, headers=headers, params=payload)

    def get_tweets_request(self, payload):
        self._get_connection_infos()
        headers = {
            "authorization": f"Bearer {self.token_bearer}",
            "x-csrf-token": "dbfeef183c6a3f1f4f1609aa22f3b379",
            "x-guest-token": self.token_guest
        }
        if "userId" in payload.keys():
            url = f"{self.url_timeline}{payload['userId']}.json"
        elif "q" in payload.keys():
            url = self.url_search
        self.get(url,
                 params=payload,
                 headers=headers)
        data = self.body["globalObjects"]
        cursor = self._get_cursor(self.body["timeline"])
        rate_limit_header = self.header("x-rate-limit-remaining")
        if rate_limit_header is None:
            return
        rate_limit = int(rate_limit_header)
        if rate_limit == 0:
            print("ur' fucked")
        elif rate_limit < 10:
            logging.warning(f"WARNING, rate-limit = {rate_limit}")
            logging.debug("Refreshing now")
            self._get_initial_request()
        return data, cursor
