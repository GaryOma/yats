# YATS - Yet Another Twitter Scraper

YATS is an ultra-fast, login-less, dependency-free Twitter scraper.

# Installation

Run the following command, no dependency needed, only python 3.6+ & an internet connection.

``` 
pip install yats
```

# How to use it

YATS will fetch all the tweets from a query, day after day. To get this query, simply go to [Twitter's official search query generator](https://twitter.com/search-advanced), and create your desired query.

You can set the number of parallel threads using the `-t` argument.

# Usage example

## Get all Tweets from [Elon Musk](https://twitter.com/elonmusk) since the beginning, using 50 parallel threads

```
yats '(from:elonmusk)' -t 50 -v
```
