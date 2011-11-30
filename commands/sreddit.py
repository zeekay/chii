#!/usr/bin/env python

"""
Reddit plugin

requires reddit (pip or https://github.com/mellort/reddit_api)
"""

from chii import command
import reddit


@command
def sreddit(self, channel, nick, host, *args):
    r = reddit.Reddit(user_agent="chii")
    stories = r.get_subreddit(args[0].lower()).get_hot(limit=5)
    for delay, story in enumerate(stories):
        msg = "<%s> %s [Score: %s - Comments: %s]" % (story.author,
                                                      story.title,
                                                      story.score,
                                                      story.num_comments)
        self.msg_later(channel, msg, delay)
