#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os.path
import sqlite3
import feedparser

from folio import Folio
from datetime import datetime
from collections import namedtuple

__authors__ = ('Juan M')
__license__ = 'WTFPL'
__version__ = '2013-10-14'

#: Jobs Feed from StackOverflow Careers 2.0
FEED_URL = 'http://careers.stackoverflow.com/jobs/feed'

#: The sqlite3 database filename to store jobs.
DB_FILENAME = 'careers-europe.db'

#: This is the regular expresion to retrieve the location of the position. It
#: look for something like this:
#:  * City, ST
#:  * City, ST, Country
#:  * City, ST, Country; Another City, State, Country
LOCATION_RE = re.compile('\(' \
        '((?P<city>[\w\s-]+)(, (?P<state>[\w\s-]+))?, (?P<country>[\w\s]+))' \
        '(; [\w\s-]+, [\w\s]+)*\)')

#: List of (some) countries in Europe.
EUROPE = ('Austria', 'Belgium', 'Denmark', 'Deutschland', 'Finland', 'France',
          'Germany', 'Greece', 'Ireland', 'Italy', 'Nederlands', 'Norway',
          'Poland', 'Portugal', 'Spain', 'Sweden', 'Switzerland', 'Ukraine',
          'United Kingdom')


Job = namedtuple('Job', ['link', 'title', 'published'])


def parse_location(title):
    matches = LOCATION_RE.search(title)
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
            entry_datetime = datetime(*entry.published_parsed[:6])
            job = Job(entry.link, entry.title, entry_datetime)
            jobs.append(job)

    return jobs


def parse_db(db):
    rows = db.execute('SELECT * FROM jobs ORDER BY published DESC LIMIT 25')
    jobs = []

    for row in rows:
        row_datetime = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
        job = Job(row[0], row[1], row_datetime)
        jobs.append(job)

    return jobs


def init_db():
    exists = os.path.exists(DB_FILENAME)
    db = sqlite3.connect(DB_FILENAME)

    if not exists:
        db.execute('''CREATE TABLE jobs (link text not null,
                                         title text not null,
                                         published datetime not null,
                                         primary key (link))''')

    return db


def build_jobs():
    db = init_db()
    jobs = parse_db(db)
    feed_jobs = parse_feed()

    for feed_job in reversed(feed_jobs):
        found = filter(lambda job: job.link == feed_job.link, jobs)
        if len(found) == 0:
            try:
                db.execute('INSERT INTO jobs VALUES (?, ?, ?)', feed_job)
            except sqlite3.IntegrityError:
                pass # Already exists in the database.
            jobs.insert(0, feed_job)

    db.commit()
    db.close()

    return jobs[-25:]


def build_proj(jobs):
    #: Create the Folio's project. Will use diferent paths as the defaults and
    #: enable the *themes* extension.
    proj = Folio(__name__, source_path='templates', build_path='html',
                 extensions=['themes'])

    #: Project configuration.
    proj.config.update({
        'THEME': 'basic',
        'THEMES_PATHS': [os.path.join('templates', 'themes')],
        'TEMPLATE_BUILDER_PATTERN': ('*.html', '*.xml'),
    })

    #: Add a global context with the jobs previously parsed.
    proj.add_context('*', {'jobs': jobs, 'updated': datetime.now()})

    #: Finally, build!
    return proj.build()


def main():
    jobs = build_jobs()
    resp = build_proj(jobs)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
