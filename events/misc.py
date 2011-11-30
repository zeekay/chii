from chii import event
import random

@event('action')
def trout(self, channel, nick, host, action):
    if 'trout' in action:
        self.me(channel, 'slaps %s around with a large carp' % nick)

@event('msg')
def the_best(self, channel, nick, host, msg):
    if (msg.startswith('who is') or msg.startswith('who the')) and (msg.endswith('best?') or msg.endswith('best')):
        if self.config['owner'] in '!'.join((nick, host)):
            if msg.startswith('who the'):
                response = "%s's the best!" % nick
            else:
                response = '%s is the %s best!' % (nick, ' '.join(msg.split()[2:-1]))
        else:
            response = 'not you'
        if self.nickname == channel:
            self.msg(nick, response)
        else:
            self.msg(channel, response)

@event('msg')
def ya(self, channel, nick, host, msg):
    if msg.strip() == 'ya':
        self.msg(channel, 'ya')

#@event('msg')
def xaimus(self, channel, nick, host, msg):
    if 'xaimus' in msg:
        self.msg(channel, 'huang')

#@event('msg')
def muse(self, channel, nick, host, msg):
    if 'muse' in msg:
        self.msg(channel, 'U RANG %s' % nick)

@event('msg')
def cool(self, channel, nick, host, msg):
    if msg.strip() == 'cool':
        self.msg(channel, 'cool')

@event('msg')
def anders(self, channel, nick, host, msg):
    ANDERS_IS_GAY = (
        'haha what a fag',
        'haha anders',
        'what a gay',
        '...eventually culminating in buttfuckery',
        'oh no look anders got penis stuck in his face'
    )
    if 'anders' in msg.lower():
        self.msg(channel, random.choice(ANDERS_IS_GAY))
