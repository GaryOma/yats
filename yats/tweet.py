import sys

from src.custom_datetime import CustomDateTime as datetime
from src.sorted_element import SortedElement
SORT_KEYS = ["creation"]


class Tweet(SortedElement):

    def __init__(self, data, users, sort_keys=SORT_KEYS):
        super().__init__(sort_keys)
        creation_str = data["created_at"]
        self.creation = datetime.strptime(creation_str,
                                          "%a %b %d %H:%M:%S %z %Y")
        self.id = data["id"]
        self.id_str = data["id_str"]
        self.text = data["full_text"]
        self.truncated = data["truncated"]
        self.hashtags = data["entities"]["hashtags"]
        self.symbols = data["entities"]["symbols"]
        self.mentions = data["entities"]["user_mentions"]
        self.urls = data["entities"]["urls"]
        self.source = data["source"]
        self.reply_to = data["in_reply_to_user_id_str"]
        self.user_id = data["user_id"]
        self.user_id_str = data["user_id_str"]
        self.username = users[self.user_id_str]["screen_name"]
        self.localisation = data["geo"]
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
