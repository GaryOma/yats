import re
import math
import logging
from datetime import timedelta, timezone
from multiprocessing import Manager
from multiprocessing.pool import ThreadPool
from functools import partial

from yats.custom_datetime import CustomDateTime as datetime
from yats.twitter_request import TwitterRequest
from yats.profile import Profile
from yats.tweet_set import TweetSet
from yats.requests_holder import RequestsHolder
from yats.iterable_queue import IterableQueue

TWITTER_CREATION_DATE = datetime(2006, 3, 21, tzinfo=timezone.utc)
COUNT_QUERY = 20
# COUNT_QUERY = 1000


class Connector:

    def __init__(self):
        pass

    def __repr__(self):
        return "<yats.Connector>"

    def profile(self, name, request=None):
        request = TwitterRequest() if request is None else request
        request.get_profile_request(name)
        res = request.body
        profile_res = Profile(res, verbose=True)
        return profile_res

    def _create_query(self,
                      q: str = None,
                      words: list = None,
                      sentence: str = None,
                      words_or: list = None,
                      words_not: list = None,
                      hashtag: str = None,
                      from_account: str = None,
                      to_account: str = None,
                      mention: str = None,
                      min_replies: int = None,
                      min_likes: int = None,
                      min_retweets: int = None,
                      since: datetime = None,
                      until: datetime = None,
                      filter_links: bool = None,
                      filter_replies: bool = None):
        if q is not None:
            query = f'{q} '
        else:
            query = ""
            if words is not None:
                query = f'{" ".join(words)} '
            if sentence is not None:
                query += f'"{sentence}" '
            if words_or is not None:
                query += f'({" OR ".join(words_or)}) '
            if words_not is not None:
                query += f'{" ".join(["-"+x for x in words_not])} '
            if hashtag is not None:
                query += f'({"#"+hashtag if hashtag[0] != "#" else hashtag}) '
            if from_account is not None:
                query += f'(from:{from_account}) '
            if to_account is not None:
                query += f'(to:{to_account}) '
            if mention is not None:
                query += f'({mention}) '
            if min_replies is not None:
                query += f'min_replies:{min_replies} '
            if min_likes is not None:
                query += f'min_faves:{min_likes} '
            if min_retweets is not None:
                query += f'min_retweets:{min_retweets} '
            if filter_links is not None and filter_links:
                query += "-filter:links "
            if filter_replies is not None and filter_replies:
                query += "-filter:replies "
        if until is not None:
            query += f'until:{until.strftime("%Y-%m-%d")} '
        if since is not None:
            query += f'since:{since.strftime("%Y-%m-%d")} '
        # check if query finishes by a space
        if query[-1] == " ":
            query = query[:-1]
        return query

    def _create_payload(self, count, query=None, user_id=None):
        payload = {
            "include_profile_interstitial_type": "1",
            "include_blocking": "1",
            "include_blocked_by": "1",
            "include_followed_by": "1",
            "include_want_retweets": "1",
            "include_mute_edge": "1",
            "include_can_dm": "1",
            "include_can_media_tag": "1",
            "skip_status": "1",
            "cards_platform": "Web-12",
            "include_cards": "1",
            "include_ext_alt_text": "true",
            "include_quote_count": "true",
            "include_reply_count": "1",
            "tweet_mode": "extended",
            "include_entities": "true",
            "include_user_entities": "true",
            "include_ext_media_color": "true",
            "include_ext_media_availability": "true",
            "send_error_codes": "true",
            "simple_quoted_tweet": "true",
            "count": count,
            "query_source": "typed_query",
            "pc": "1",
            "spelling_corrections": "1",
            "ext": "mediaStats,highlightedLabel"
        }
        if query is not None:
            payload["q"] = query
        if user_id is not None:
            payload["userId"] = user_id
        return payload

    def _extract_since_until_from_q(self, q):
        until = None
        regex = r"until:(\d{4}-\d{2}-\d{2})"
        se = re.search(regex, q)
        if se:
            until = (datetime.strptime(se.group(1), "%Y-%m-%d")
                     .replace(tzinfo=timezone.utc))
            q = re.sub(regex, "", q)
        since = None
        regex = r"since:(\d{4}-\d{2}-\d{2})"
        se = re.search(regex, q)
        if se:
            since = (datetime.strptime(se.group(1), "%Y-%m-%d")
                     .replace(tzinfo=timezone.utc))
            q = re.sub(regex, "", q)
        return since, until, q

    def _tweet_worker(self, requests, lock, task_queue, limit_cooldown,
                      max_round, payload):
        with lock:
            request = requests.get()
        current_round = payload["round"] + 1
        del payload["round"]
        try:
            data, cursor = request.get_tweets_request(payload)
        except TypeError:
            request.to_file("error_request.json")
            exit(0)
        new_tweets = TweetSet(data)
        last_inserted = len(new_tweets)
        if last_inserted >= limit_cooldown and current_round < max_round:
            payload["cursor"] = cursor
            payload["round"] = current_round
            task_queue.put(payload)
        else:
            task_queue.put(None)
        with lock:
            requests.push(request)
        return new_tweets

    def _payload_generator(self,
                           verbosity,
                           count=COUNT_QUERY,
                           q=None,
                           since=None,
                           until=None,
                           **args):
        def_since = TWITTER_CREATION_DATE
        def_until = (datetime.now(timezone.utc)
                     + timedelta(days=1))
        if q is not None:
            q_since, q_until, q = self._extract_since_until_from_q(q)
            since = q_since if q_since is not None else def_since
            until = q_until if q_until is not None else def_until
        else:
            since = def_since if since is None else since
            until = def_until if until is None else until
        beg_date = since
        end_date = beg_date + timedelta(days=1)
        print_str = (f"from {since.strftime('%Y-%m-%d')}"
                     f" to {until.strftime('%Y-%m-%d')}")
        if 0 <= verbosity <= 1:
            print(print_str)
        elif verbosity > 1:
            logging.info(print_str)
        while beg_date < until:
            query = self._create_query(q=q,
                                       since=beg_date,
                                       until=end_date,
                                       **args)
            payload = self._create_payload(query=query, count=count)
            payload["round"] = 0
            yield payload
            beg_date = end_date
            end_date += timedelta(days=1)

    def get_tweets_request(self,
                           verbosity,
                           max_round,
                           thread=20,
                           limit_cooldown=5,
                           **args):
        # initiating the initial task lisk for
        # the ThreadPool
        task_list = [task for task in self._payload_generator(verbosity,
                                                              **args)
                     ]
        # copying each tasks in the IterableQueue
        # thus "allowing" the threads to add
        # additional tasks (bit of a dirty hack)
        task_queue = IterableQueue(maxsize=len(task_list))
        for task in task_list:
            task_queue.put(task)
        # object that holds the open connections
        # couldn't do it with Queues because of the SSLContext
        # not pickable :'-(
        requests = RequestsHolder()
        for _ in range(thread):
            requests.push(TwitterRequest())
        # creation of the lock for the RequestHolder
        manager = Manager()
        lock = manager.Lock()
        # TweetSet to keep the fetched tweets
        tweets = TweetSet()
        # formatting variables
        task_format = int(math.log(len(task_list), 10)) + 1
        task_it = 0
        round_format = int(math.log(max_round, 10)) + 1
        round_size = len(task_list)
        next_round_size = round_size
        round_it = 0
        disp_str = ""
        try:
            with ThreadPool(thread) as p:
                for new_tweets in p.imap_unordered(
                        partial(self._tweet_worker, requests,
                                lock, task_queue, limit_cooldown,
                                max_round),
                        task_queue):
                    tweets.add(new_tweets)
                    disp_str = (
                        f"TWEETS={len(tweets):<6} | "
                        f"NEW={len(new_tweets):<2} | "
                        f"TASK={task_it:{task_format}}/"
                        f"{round_size:<{task_format}} | "
                        f"ROUND={round_it:{round_format}}/"
                        f"{max_round} | "
                        f"NEXT ROUND<={next_round_size:{task_format}} TASKS")
                    if 0 <= verbosity <= 1:
                        end_char = "\r" if verbosity == 0 else "\n"
                        print(disp_str, end=end_char)
                    elif verbosity > 1:
                        logging.info(disp_str)
                    if len(new_tweets) < limit_cooldown:
                        next_round_size -= 1
                    task_it += 1
                    if task_it >= round_size:
                        task_it = 0
                        round_size = next_round_size
                        round_it += 1
            if 0 <= verbosity <= 1:
                print(disp_str)
        except KeyboardInterrupt:
            if 0 <= verbosity <= 1:
                print(disp_str)
                print("Stopped by the user")
        return tweets

    def get_tweets_timeline(self, username, user_id=None):
        if user_id is None:
            request = TwitterRequest()
            profile = self.profile(username, request)
            user_id = profile.restid
            logging.debug(f"Getting {profile.name}'s timeline tweets...")
        requests = RequestsHolder()
        requests.push(TwitterRequest())
        payload = self._create_payload(user_id=user_id)
        manager = Manager()
        lock = manager.Lock()
        tweets = self._tweet_worker(requests, lock, payload)
        return tweets

    def get_tweets_user(self, username, verbosity, since=None, **args):
        if since is not None:
            beg_date = since
        else:
            request = TwitterRequest()
            profile = self.profile(username, request)
            beg_date = profile.creation
        print_str = f"Getting {username}'s all tweets..."
        if 0 <= verbosity <= 1:
            print(print_str)
        elif verbosity > 1:
            logging.info(print_str)
        tweets = self.get_tweets_request(from_account=username,
                                         since=beg_date,
                                         filter_replies=True,
                                         verbosity=verbosity,
                                         **args)
        return tweets

    def request(self, query, **args):
        user_query = re.search(r"^@(\S+)$", query)
        if user_query:
            username = user_query.group(1)
            tweets = self.get_tweets_user(username=username, **args)
        else:
            tweets = self.get_tweets_request(q=query, **args)
        return tweets
