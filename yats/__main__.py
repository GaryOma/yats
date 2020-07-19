#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from yats.connector import Connector

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username",
                        "-u",
                        type=str,
                        default="realdonaldtrump")
    parser.add_argument("--thread",
                        "-t",
                        type=int,
                        default=10)
    args = parser.parse_args()
    con = Connector(args.username)
    profile = con.profile(args.username)
    profile.describe()
    con.get_tweets_user(args.username, thread_nb=args.thread)
