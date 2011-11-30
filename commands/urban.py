#!/usr/bin/env python

"""
urban dictionary command.

requires json and requests(dev version)
"""
import requests
import json
from chii import command

URL = "http://www.urbandictionary.com/iphone/search/define?term=%s"


@command
def urban(self, channel, nick, host, *args):
    r = requests.get(URL % '%20'.join(args))
    # response is 200?
    if not r.ok:
        return 'Error looking up %s' % args

    data = json.loads(r.content)

    if len(data['list']) > 3:
        data['list'] = data['list'][:3]  # only print 3 results

    for i in range(len(data['list'])):
        self.batch_msg(channel, "(%s/%s) %s.\n%s\n" % (
                            str(data['list'][i][u'thumbs_up']),
                            str(data['list'][i][u'thumbs_down']),
                            str(data['list'][i][u'definition']),
                            str(data['list'][i][u'example'])))
