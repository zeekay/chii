try:
    import tweepy
    from chii import config, command
    from fnmatch import fnmatch
    
    CONSUMER_KEY = config['consumer_key'] or '7YQFmkKuayyGpGrqgQGcA'
    CONSUMER_SECRET = config['consumer_secret'] or '6KybR8lgUihTx5g305QZRXIid708JAhqBisYfkYEMy8'
    
    @command
    def tweet(self, channel, nick, host, *args):
        """tweet tweet"""
        def get_auth_url(auth):
            """returns url to authorize"""
            try:
                auth_url = auth.get_authorization_url()
            except tweepy.TweepError:
                return 'Error! Failed to get request token.'
            self.config['tweet'] = 'authorize me @ %s' % auth_url
            config.save()
            return 'authorize me and gimme your pin: %s' % auth_url
    
        def save_oauth_token(auth, pin):
            """attempts to use user provided pin to save twitter oauth token key and secret"""
            try:
                auth.get_access_token(pin)
            except tweepy.TweepError:
                return 'Error! Failed to get access token.'
            config['token'], config['secret'] = auth.access_token.key, auth.access_token.secret
            self.config.save()
            return "locked'n'loaded ready 2 tweet"
    
        def update_status(args, auth, config):
            """tweets arguments"""
            token, secret = config['token'], config['secret']
            auth.set_access_token(token, secret)
            api = tweepy.API(auth)
            try:
                s = api.update_status(' '.join(args))
                return 'tweeted! https://twitter.com/#!/%s/status/%d' % (str(s.author.screen_name), s.id)
            except Exception as e:
                return e
    
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        for user in self.config['tweet']:
            if fnmatch('!'.join((nick, host)), user):
                config = self.config['tweet'][user]
                break
        else:
            config = self.config['tweet']['bot']
        if args and config:
            if 'token' and 'secret' in config:
                return update_status(args, auth, config)
            else:
                return save_oauth_token(auth, args[0])
        elif config:
            return 'tweet?'
        else:
            return get_auth_url(auth)
except:
    pass
