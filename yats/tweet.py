import sys

from yats.custom_datetime import CustomDateTime as datetime
from yats.sorted_element import SortedElement
SORT_KEYS = ["creation"]


class Tweet(SortedElement):

    def __init__(self, data, users, sort_keys=SORT_KEYS):
        super().__init__(sort_keys)
        creation_str = data["created_at"]
        self.creation = datetime.strptime(creation_str,
                                          "%a %b %d %H:%M:%S %z %Y")
        # if it comes from the timeline request
        # fewer infos are available
        if "id" not in data.keys():
            self.id = data["id_str"]
            self.truncated = None
            self.hashtags = None
            self.symbols = None
            self.urls = None
            self.reply_to = None
            self.user_id = data["user_id_str"]
            self.localisation = None
            if "user_mentions" not in data["entities"].keys():
                self.mentions = None
            else:
                self.mentions = data["entities"]["user_mentions"]
        else:
            self.id = data["id"]
            self.truncated = data["truncated"]
            self.hashtags = data["entities"]["hashtags"]
            self.symbols = data["entities"]["symbols"]
            self.urls = data["entities"]["urls"]
            self.reply_to = data["in_reply_to_user_id_str"]
            self.user_id = data["user_id"]
            self.localisation = data["geo"]
            self.mentions = data["entities"]["user_mentions"]
        self.id_str = data["id_str"]
        self.text = data["full_text"]
        self.source = data["source"]
        self.user_id_str = data["user_id_str"]
        self.username = users[self.user_id_str]["screen_name"]
        self.retweet_nb = data["retweet_count"]
        self.favorite_nb = data["favorite_count"]
        self.reply_nb = data["reply_count"]
        self.lang = data["lang"]

    def __repr__(self):
        return (f"<pyter.Tweet"
                f":{self.creation.strftime('%y-%m-%d %H:%M:%S')}"
                f":{self.id}"
                f":{self.username}>")

    def to_dict(self):
        d = dict(self.__dict__)
        del d["SORT_KEYS"]
        return d
