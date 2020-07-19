#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from yats.connector import Connector


def main():
    parser = argparse.ArgumentParser(prog="yats", usage="%(prog)s [options]",
                                     description="A fast Twitter scraper")
    # parser.add_argument("--username", "-u", type=str,
    #                     default="realdonaldtrump")
    parser.add_argument("username", type=str, default="realdonaldtrump")
    parser.add_argument("--thread", "-t", type=int, default=10)
    parser.add_argument("--timeline", "-tl", action="store_true")
    parser.add_argument("--output", "-o", type=str, default="/tmp/tweets.json")
    con = Connector()
    args = parser.parse_args()
    if args.timeline:
        tweets = con.get_tweets_timeline(args.username)
    else:
        tweets = con.get_tweets_user(args.username, thread_nb=args.thread)
    tweets.export(args.output)
    # profile = con.profile(args.username)
    # profile.describe()


if __name__ == "__main__":
    main()
