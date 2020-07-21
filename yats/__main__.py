#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from datetime import timezone

from yats.connector import Connector
from yats.custom_datetime import CustomDateTime as datetime


def main():
    parser = argparse.ArgumentParser(prog="yats",
                                     description="A fast Twitter scraper",
                                     epilog="yats @realdonaldtrump")
    parser.add_argument("query", type=str,
                        help=("the query to execute using the twitter "
                              "syntax inside '' or a @username"))
    parser.add_argument("-lc", "--limit-cooldown", type=int, default=5,
                        help=("minimum tweets to get per "
                              "requests during cooldown "
                              "default %(default)s"))
    parser.add_argument("-o", "--output", type=str, default="/tmp/tweets.json",
                        help="output file .json or .csv, default %(default)s")
    parser.add_argument("-s", "--since", default=None,
                        type=(lambda s: datetime.strptime(s, '%Y-%m-%d')),
                        help="since this date, YYYY-MM-DD")
    parser.add_argument("-t", "--thread", type=int, default=10,
                        help=("number of parallel thread to use, "
                              "default = %(default)s"))
    parser.add_argument("-tl", "--timeline", action="store_true",
                        help="only fetches the tweets from the user timeline")
    parser.add_argument("-u", "--until", default=None,
                        type=(lambda s: datetime.strptime(s, '%Y-%m-%d')),
                        help="until this date, YYYY-MM-DD")
    con = Connector()
    args = parser.parse_args()
    if args.timeline:
        tweets = con.get_tweets_timeline(args.query)
    else:
        if args.since is not None:
            args.since = args.since.replace(tzinfo=timezone.utc)
        if args.until is not None:
            args.until = args.until.replace(tzinfo=timezone.utc)
        query = args.query
        query_list = ["thread", "limit_cooldown", "since", "until"]
        query_args = {}
        for arg in query_list:
            query_args[arg] = vars(args)[arg]
        tweets = con.request(query, **query_args)
        # tweets = con.get_tweets_user(args.username, thread_nb=args.thread)
    print(f"writing {len(tweets)} tweets to {args.output}")
    tweets.export(args.output)
    # profile = con.profile(args.username)
    # profile.describe()


if __name__ == "__main__":
    main()
