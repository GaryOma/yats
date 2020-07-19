
from src.sorted_set import SortedSet
from src.tweet import Tweet


class TweetSet(SortedSet):

    def __init__(self, data=[]):
        if not data or isinstance(data, list):
            super().__init__(data)
        else:
            super().__init__([])
            tweets_raw = data["tweets"]
            users_raw = data["users"]
            for id, content in tweets_raw.items():
                tweet = Tweet(content, users_raw)
                self.add(tweet)
