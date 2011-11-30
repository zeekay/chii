#!/usr/bin/env python

"""
The magic 8-ball knows all.
"""

from chii import command
from random import choice
from color import toBold

@command
def eight_ball(self, channel, nick, host, *args):
    answers = ['Yes', 'No',
               'Outlook so so', 'Absolutely',
               'My sources say no', 'Yes definitely',
               'Very doubtful', 'Most likely',
               'Forget about it', 'Are you kidding?',
               'Go for it', 'Not now',
               'Looking good', 'Who knows',
               'A definite yes', 'You will have to wait'
               'Yes, in due time', 'I have my doubts']
    
    #question = ' '.join(args)
    self.msg(channel, toBold("*shakes the magic 8-ball*")) 
    self.msg_later(channel, "%s the 8-ball says %s" % (nick, toBold(choice(answers))), 4)
