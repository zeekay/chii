from chii import command, config, event

THRESHOLD = config['haha_threshold']

if THRESHOLD:
    import random

    LAUGHTER = (
            'hahah',
            'lollolol',
            'rofl',
            'ahahahahahah',
            'hg h gh ghg hgh',
            'h a h a h a h a h a h',
            'aaaaaaaaaaaaaaaaa',
            'aaaahahah',
            'ahahah',
            'bahhhhhh',
            'waaaaaaaaaaah',
            'hshshshshahaah',
            'MOTHERFUCKING H & A',
            'hahahahahaahhahahaahahahahhhahhhhahahahahahahahahahahahahahahahaahahahaha',
    )

    @event('msg')
    def haha(self, channel, nick, host, msg):
        if random.random() < self.config['haha_threshold']:
            if 'haha' in msg.lower():
                haha = ''
                for i in range(int(random.random()*10)):
                    haha += LAUGHTER[int(random.random()*len(LAUGHTER))]
                return haha

    @command
    def hat(self, channel, nick, host, threshold=None):
        """set's threshold for random laughter. must be a float between 0.01 and 0.99"""
        if threshold:
            try:
                threshold = float(threshold)
            except ValueError:
                return 'hey man use a fucking float!'
            if 0 <= threshold <= 1:
                self.config['haha_threshold'] = threshold
                return 'laughter threshold set to %s' % threshold
            else:
                return 'yeah fuck you'
        else:
           return 'laughter threshold set to %s' % self.config['haha_threshold']
