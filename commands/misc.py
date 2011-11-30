import json, random, os, urllib, urllib2, requests

from chii import config, command

def get_random(items):
    index = int(random.random() * len(items))
    return items[index]

@command
def face(self, channel, nick, host, *args):
    """you need help with your face?"""
    if args:
        args = ' '.join(args).split('+')
        name = args[0].strip()
        if len(args) > 1:
            madeof = ' and '.join(x.strip() for x in args[1:])
            return "hahaha %s's face is made of %s" % (name, madeof)
        return "hahah %s's face" % name
    return 'hahah your face'

@command
def lambchops(self, channel, nick, host, *args):
    """THIS IS THE..."""
    SONG_THAT_NEVER_ENDS = [
        "THIS IS THE SONG THAT DOESN'T END",
        "YES IT GOES ON AND ON MY FRIEND",
        "SOME PEOPLE STARTED SINGING IT NOT KNOWING WHAT IT WAS",
        "AND THEY'LL CONTINUE SINGING IT FOREVER JUST BECAUSE"
    ]
    for line in SONG_THAT_NEVER_ENDS:
        self.msg(channel, line)

@command
def last(self, channel, nick, host, *args):
    """that last bit was quite funny!"""
    def get_line(f, size):
        while True:
            size -= 1
            f.seek(size)
            line = f.read()
            if line.startswith('\n'):
                return f, size, line

    if self.config['log_channels']:
        log_file = os.path.join(self.config['logs_dir'], channel[1:] + '.log')
        size = os.path.getsize(log_file) - 2 # skip last \n hopefully
        with open(log_file) as f:
            last = get_line(f, size) # find last line
            line = get_line(last[0], last[1])[2].split('\n')[1].split(']', 1)[1] # get line before and clean it up!
        self.topic(channel, line.strip())
    else:
        return 'not logging, I have no fucking clue what happened 2 seconds ago'

@command
def dong(self, channel, nick, host, *args):
    """that last bit was quite funny!"""
    def get_line(f, size):
        while True:
            size -= 1
            f.seek(size)
            line = f.read()
            if line.startswith('\n'):
                return f, size, line

    if self.config['log_channels']:
        log_file = os.path.join(self.config['logs_dir'], channel[1:] + '.log')
        size = os.path.getsize(log_file) - 2 # skip last \n hopefully
        with open(log_file) as f:
            last = get_line(f, size) # find last line
            line = get_line(last[0], last[1])[2].split('\n')[1].split(']', 1)[1] # get line before and clean it up!
        count, mangled = 0, []
        words = line.split()[1:]
        for word in words:
            if random.random()*10 < 3 and count < .5*len(words):
                mangled.append('8' + '='*int(random.random()*10) + 'D')
                count += 1
            else:
                mangled.append(word)
        if count == 0:
            mangled.append('8' + '='*int(random.random()*10) + 'D')
        return ' '.join(mangled)
    else:
        return 'not logging, I have no fucking clue what happened 2 seconds ago'

@command
def directions(self, channel, nick, host, *args):
    """try from -> to, now get lost"""
    url = 'http://www.mapquest.com/?le=t&q1=%s&q2=%s&maptype=map&vs=directions'
    if '->' not in args:
        return 'um try again'
    directions = (urllib.quote(x) for x in ' '.join(args).split('->'))
    return url % tuple(directions)

try:
    import lxml.html
    @command
    def imgur(self, channel, nick, host, *args):
        """IT'S DANGEROUS TO GO ALONE! TAKE THIS."""
        url = 'http://imgur.com/gallery/new'
        doc = lxml.html.fromstring(requests.get(url).read())
        img = random.choice([x.attrib['id'] for x in doc.xpath("//div[@class='post']")])
        url = 'http://imgur.com/%s' % img
        try:
            tree = lxml.html.parse(url)
            title = tree.xpath('//title/text()')[0].split('-')[0]
            return "%s - %s" % (url, title)
        except:
            return "%s" % url
except ImportError: pass

@command('wk', 'wiki')
def wiki(self, channel, nick, host, *args):
    build_url = lambda s: 'http://en.wikipedia.org/wiki/%s' % s.replace(' ', '_')
    search_url = 'http://en.wikipedia.org/w/api.php?action=opensearch&search=%s&format=json'
    resp = requests.get(search_url % urllib.quote(' '.join(args)))
    matches = json.load(resp)[1]
    if not matches:
        return 'nada'
    else:
        self.batch_msg(channel, '\n'.join(build_url(match.encode('ascii', 'ignore')) for match in matches))

@command
def typo(self, channel, nick, host, *args):
    """only you can stop forest fires"""
    if args:
        nick = args[0]
        if nick not in ['muse', 'jesus-c']:
            return self.sendLine('KICK %s %s typo for great justice' % (channel, args[0]))
        else:
            return 'how can a bot be wrong?'
    else:
        return self.sendLine('KICK %s %s typo for great justice' % (channel, nick))
