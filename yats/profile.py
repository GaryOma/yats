import logging

from yats.custom_datetime import CustomDateTime as datetime


class Profile:

    def __init__(self, response, verbose=False):
        user = response["data"]["user"]
        self.user = user
        self.name = user["legacy"]["name"]
        self.username = user["legacy"]["screen_name"]
        self.id = user["id"]
        self.restid = user["rest_id"]
        creation_str = user["legacy"]["created_at"]
        self.creation = datetime.strptime(creation_str,
                                          "%a %b %d %H:%M:%S %z %Y")
        self.description = user["legacy"]["description"]
        self.tweet_nb = user["legacy"]["statuses_count"]
        self.followers_nb = user["legacy"]["followers_count"]
        self.following_nb = user["legacy"]["friends_count"]
        self.favourites_nb = user["legacy"]["favourites_count"]

    def __repr__(self):
        return f"<yaps.Profile:{self.username}>"

    def describe(self):
        print(f"{self.name}'s Profile:")
        print(f"{self.username} {self.id}")
        print(f"{self.description}")
        print("Twitter Account:")
        print(f"Creation date: {self.creation}")
        print(f"Number of Tweets: {self.tweet_nb}")
        print(f"Number of followers: {self.followers_nb}")
        print(f"Number of following: {self.following_nb}")
        print(f"Number of favourites: {self.favourites_nb}")
