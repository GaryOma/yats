#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
from datetime import timezone

from yats.connector import Connector
from yats.custom_datetime import CustomDateTime as datetime


def main():
    parser = argparse.ArgumentParser(prog="yats",
                                     description="A fast Twitter scraper",
                                     epilog="yats @realdonaldtrump")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("query", type=str,
                        help=("the query to execute using the twitter "
                              "syntax inside '' or a @username"))
    parser.add_argument("-c", "--count", type=int, default=20,
                        help=("count parameter of the "
                              "query default %(default)s"))
    parser.add_argument("-lc", "--limit-cooldown", type=int, default=5,
                        help=("minimum tweets to get per "
                              "requests during cooldown "
                              "default %(default)s"))
    parser.add_argument("-o", "--output", type=str, default="/tmp/tweets.json",
                        help="output file .json or .csv, default %(default)s")
    parser.add_argument("-r", "--max-round", type=int, default=20,
                        help="max round limit default %(default)s")
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
    group.add_argument("-v", "--verbosity", action="count", default=0,
                       help=("verbosity level "
                             "increase with -v or -vv or -vvv"))
    group.add_argument("-q", "--quiet", action="store_true",
                       help="remove all the outputs")
    con = Connector()
    args = parser.parse_args()
    print(args)
    if args.verbosity > 3:
        print("Verbosity too high, accepted values are:")
        print(" -v, -vv, -vvv")
        exit(1)
    elif args.quiet:
        verbosity_level = -1
    else:
        verbosity_level = args.verbosity
    logging_mode = {
        3: logging.NOTSET,
        2: logging.INFO,
        1: logging.CRITICAL,
        0: logging.CRITICAL,
        -1: logging.CRITICAL
    }
    logger = logging.getLogger()
    log_formatter = logging.Formatter("%(asctime)s "
                                      "[%(threadName)-12.12s] "
                                      "[%(levelname)-5.5s]  "
                                      "%(message)s",
                                      datefmt='%H:%M:%S',)
    logging_level = logging_mode[verbosity_level]
    print(logging_level)
    console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging_level)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging_level)
    if args.timeline:
        tweets = con.get_tweets_timeline(args.query)
    else:
        if args.since is not None:
            args.since = args.since.replace(tzinfo=timezone.utc)
        if args.until is not None:
            args.until = args.until.replace(tzinfo=timezone.utc)
        query = args.query
        query_list = ["thread", "limit_cooldown", "since", "until",
                      "count", "max_round"]
        query_args = {}
        for arg in query_list:
            query_args[arg] = vars(args)[arg]
        tweets = con.request(query, verbosity=verbosity_level, **query_args)
    print(f"writing {len(tweets)} tweets to {args.output}")
    tweets.export(args.output)
    # profile = con.profile(args.username)
    # profile.describe()


if __name__ == "__main__":
    main()
