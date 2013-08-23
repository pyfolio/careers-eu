#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import feedparser

__authors__ = ('Juan M')
__license__ = 'Public Domain'
__version__ = '2013-08-23'

FEED_URL = 'http://careers.stackoverflow.com/jobs/feed'
LOC_RE = re.compile('\(' \
        '((?P<city>[\w\s]+)(, (?P<state>[\w\s]+))?, (?P<country>[\w\s]+))' \
        '(; [\w\s]+, [\w\s]+)*\)')

EUROPE = ('Austria', 'Belgium', 'Denmark', 'Deutschland', 'Finland', 'France',
          'Germany', 'Greece', 'Ireland', 'Italy', 'Nederlands', 'Norway',
          'Poland', 'Portugal', 'Spain', 'Sweden', 'Switzerland', 'Ukraine',
          'United Kingdom')


class Job:
    def __init__(self, link, title, published):
        self.link = link
        self.title = title
        self.published = published


def parse_location(title):
    matches = LOC_RE.search(title)
    city = matches.group('city')
    state = matches.group('state')
    country = matches.group('country')
    if len(country) == 2:
        state = country
        country = 'USA'
    return (city, state, country)


def parse_feed():
    feed = feedparser.parse(FEED_URL)
    jobs = []

    for entry in feed.entries:
        location = parse_location(entry.title)
        if location[2] in EUROPE:
            job = Job(entry.link, entry.title, entry.published_parsed)
            jobs.append(job)

    return jobs


def main():
    jobs = parse_feed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    try:
        main()
    except KeyboardInterrupt:
        pass
