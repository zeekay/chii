try:
    import megahal
except:
    megahal = None

if megahal:
    from megahal import *
    import os, random, re
    from chii import config, event

    # get config or set defaults
    if config['megahal_brain']:
        BRAIN = config['megahal_brain']
    else:
        BRAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'megahal.brain')
    if config['megahal_chattiness']:
        CHATTINESS = config['megahal_chattiness']
    else:
        CHATTINESS = 0
    
    megahal = MegaHAL(brainfile=BRAIN, order=DEFAULT_ORDER, timeout=DEFAULT_TIMEOUT)
    
    @event('msg')
    def megachat(self, channel, nick, host, msg):
        if self.nickname.lower() in msg.lower():
            msg = re.compile(self.nickname + "[:,]* ?", re.I).sub('', msg)
            prefix = "%s: " % nick
        else:
            prefix = ''
    
        if prefix or random.random() <= CHATTINESS:
            return prefix + megahal.get_reply(msg)
        elif nick == 'ali':
            return prefix + megahal.get_reply(msg)            
    
    @event('unload', 'quit')
    def megaclose(self, *args):
        megahal.sync()
        megahal.close()
