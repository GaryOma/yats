import re
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

TWITTER_CREATION_DATE = datetime(2006, 3, 21)
# COUNT_QUERY = 1000
COUNT_QUERY = 20


class Connector:

    def __init__(self, fast_mode=True):
        logging.basicConfig(level=logging.DEBUG,
                            format=('%(message)s'))

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

    def _create_payload(self, query, count=COUNT_QUERY):
        return {
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
            "q": query,
            "count": count,
            "query_source": "typed_query",
            "pc": "1",
            "spelling_corrections": "1",
            "ext": "mediaStats,highlightedLabel"
        }

    def _extract_since_until_from_q(self, q):
        until = None
        regex = r"until:(\d{4}-\d{2}-\d{2})"
        se = re.search(regex, q)
        if se:
            until = (datetime.strptime(se.group(1), "%Y-%M-%d")
                     .replace(tzinfo=timezone.utc))
            q = re.sub(regex, "", q)
        since = None
        regex = r"since:(\d{4}-\d{2}-\d{2})"
        se = re.search(regex, q)
        if se:
            since = (datetime.strptime(se.group(1), "%Y-%M-%d")
                     .replace(tzinfo=timezone.utc))
            q = re.sub(regex, "", q)
        return since, until, q

    def _tweet_worker(self, requests, lock, payload):
        with lock:
            if len(requests) > 0:
                request = requests.pop()
            else:
                request = TwitterRequest()
        tweets = TweetSet()
        data, cursor = request.get_tweets_request(payload)
        new_tweets = TweetSet(data)
        tweets.add(new_tweets)
        payload["cursor"] = cursor
        last_inserted = len(new_tweets)
        while last_inserted > 0:
            data, cursor = request.get_tweets_request(payload)
            new_tweets = TweetSet(data)
            tweets.add(new_tweets)
            payload["cursor"] = cursor
            last_inserted = len(new_tweets)
        with lock:
            requests.push(request)
        return tweets

    def _payload_generator(self,
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
        while beg_date < until:
            query = self._create_query(q=q,
                                       since=beg_date,
                                       until=end_date,
                                       **args)
            payload = self._create_payload(query)
            yield payload
            beg_date = end_date
            end_date += timedelta(days=1)

    def get_all_tweets_request(self,
                               thread_nb=20,
                               **args):
        manager = Manager()
        requests = RequestsHolder()
        for _ in range(thread_nb):
            requests.push(TwitterRequest())
        lock = manager.Lock()
        tweets = TweetSet()
        with ThreadPool(thread_nb) as p:
            for new_tweets in p.imap_unordered(
                    partial(self._tweet_worker, requests, lock),
                    self._payload_generator(**args)):
                tweets.add(new_tweets)
                logging.debug(f"TOTAL {len(tweets)}, NEW {len(new_tweets)}")
        return tweets

    def get_tweets_user(self, username, since=None, **args):
        request = None
        if since is not None:
            beg_date = since
        else:
            request = TwitterRequest()
            profile = self.profile(username, request)
            beg_date = profile.creation
            logging.debug(f"Getting {profile.name}'s all tweets...")
        username = "@"+username if username[0] != "@" else ""
        tweets = self.get_all_tweets_request(from_account=username,
                                             since=beg_date,
                                             filter_replies=True,
                                             **args)
        return tweets
