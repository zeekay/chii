import socket

from chii import command

def dict_lookup(word):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("www.dict.org", 2628))
    sock.send('define * "%s"\r\n\r\n' % word)
    sock.settimeout(0.1)
    
    results = ''
    while True:
        try:
            buf = sock.recv(1024)
        except:
            break
        if not buf:
            break
        results += buf
    
    definition, match = [], False
    for line in results.splitlines():
        if line.startswith('552'):
            return 'No matches'
        if line.startswith('151'):
            if not match:
                match = True
            else:
                break
        else:
            if match is True:
                if not line.strip().startswith('[') and line.strip() != '.':
                    definition.append(line)
    return '\n'.join(definition)

@command('dict', 'define')
def dict(self, channel, nick, host, *args):
    """looks up words. i mean seriously you couldn't guess?"""
    if args:
        self.batch_msg(channel, dict_lookup(args[0]))
    else:
        return 'lookup \002what\002 word?'
