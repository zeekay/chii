from chii import command, config, event

from ast import literal_eval

PERSIST = config['lambda_persist']
SAVED_LAMBDAS = config['lambdas']
HELPER_FUNCS = config['lambda_helpers']

# block dangerous stuff:
DANGEROUS = {x: None for x in 'eval execfile file open __import__ __file__ __builtins__ __package__ __name__ input raw_input'.split()}
SAFE = {
    'abs': abs,
    'all': all,
    'any': any,
    'basestring': basestring,
    'bin': bin,
    'bool': bool,
    'bytearray': bytearray,
    'callable': callable,
    'chr': chr,
    'classmethod': classmethod,
    'cmp': cmp,
    'complex': complex,
    'dict': dict,
    'divmod': divmod,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'format': format,
    'frozenset': frozenset,
    'hash': hash,
    'hex': hex,
    'id': id,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'iter': iter,
    'len': len,
    'list': list,
    'long': long,
    'map': map,
    'max': max,
    'min': min,
    'next': next,
    'object': object,
    'oct': oct,
    'ord': ord,
    'pow': pow,
    'range': range,
    'reduce': reduce,
    'repr': repr,
    'reveresed': reversed,
    'round': round,
    'set': set,
    'slice': slice,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'type': type,
    'unichr': unichr,
    'unicode': unicode,
    'xrange': xrange,
    'zip': zip,
    'True': True,
    'False': False,
}

LAMBDA_GLOBALS = SAFE
LAMBDA_GLOBALS.update(DANGEROUS)

if HELPER_FUNCS:
    import random
    # funcs available to lambda
    def rand(choices=None):
        """wrapper for random, to make it a bit easier to use common functions from lambdas"""
        if choices is None:
            return random.random()
        elif type(choices) is int:
            return int(random.random()*choices)
        elif hasattr(choices, '__iter__'):
            return random.choice(choices)
        else:
            return 'wtf mang'

    try:
        import httplib2
        h = httplib2.Http('.cache')

        def get(url):
            return h.request(url, 'GET')[1]

        def head(url):
            return h.request(url, 'GET')[0]
    except:
        import urllib2
        def get(url):
            request = urllib2.Request(url, None, {'Referer': 'http://quoth.notune.com'})
            return urllib2.urlopen(request)
    
    def json_get(url):
        return json.load(get(url))
    
    try:
        import yaml
        def yaml_get(url):
            return yaml.load(get(url))
    except:
        pass

    try:
        from BeautifulSoup import BeautifulSoup as bs
    except:
        pass

# actually handle adding/loading/removing/etc lambdas
def build_lambda(args):
    """Returns name and lambda function as strings"""
    name, body = ' '.join(args).split(':', 1)
    if name.endswith(')'):
        name, args = name[:-1].split('(', 1)
    else:
        args = '*args'
    func_s = 'lambda channel, nick, host, %s:%s' % (args, body)
    return func_s, name

def wrap_lambda(func, func_s, name, nick):
    """returns our wrapped lambda"""
    def wrapped_lambda(channel, nick, host, *args):
        try:
            args = tuple(literal_eval(''.join(args)))
        except:
            pass
        return str(func(channel, nick, host, *args))
    help_def = func_s.replace('channel, nick, host, ', '')
    wrapped_lambda.__doc__ = "lambda function added by \002%s\002\n%s = %s" % (nick, name, help_def)
    wrapped_lambda._restrict = None
    return wrapped_lambda

@command('lambda')
def lambda_command(self, channel, nick, host, *args):
    """add new functions to the bot using python lambda functions"""
    def list_lambda(nick, args):
        lambdas = self.config['lambdas']
        if lambdas:
            return 'lambdas: %s' % ' '.join(x for x in self.config['lambdas'])
        else:
            return 'no lambdas found'

    def del_lambda(nick, args):
        name = args[1]
        del self.config['lambdas'][name]
        self.config.save()
        return 'deleted %s' % name

    def add_lambda(nick, args):
        # build lambda, command name from args
        func_s, name = build_lambda(args)
        # return if command by that name exists
        if name in self.commands:
            if hasattr(self.commands[name], '_registry'):
                return "lambda commands can't override normal commands"
        # try to eval our lambda function
        try:
            func = eval(func_s, LAMBDA_GLOBALS, {})
        except Exception as e:
            return 'not a valid lambda function: %s' % e
        # save to config if persist_lambda is on
        if PERSIST:
            if not SAVED_LAMBDAS:
                self.config['lambdas'] = {}
            self.config['lambdas'][name] = [func_s, nick]
            self.config.save()
        self.commands[name] = wrap_lambda(func, func_s, name, nick)
        return 'added new lambda function to commands as %s' % name

    dispatch = {
        (lambda x: not x)(args): list_lambda,
        (lambda x: x and x[0].endswith(':'))(args): add_lambda,
        (lambda x: x and x[0] == 'del')(args): del_lambda,
    }

    return dispatch[True](nick, args)

if PERSIST and SAVED_LAMBDAS:
    @event('load')
    def load_lambdas(self, *args):
        for name in SAVED_LAMBDAS.keys():
            # build lambda, command name from args
            func_s, nick = self.config['lambdas'][name]
            # return if command by that name exists
            if name in self.commands:
                if hasattr(self.commands[name], '_registry'):
                    print "lambda commands can't override normal commands"
                    break
            # try to eval our lambda function
            try:
                func = eval(func_s)
            except Exception as e:
                print 'not a valid lambda function: %s' % e
                break
            self.commands[name] = wrap_lambda(func, func_s, name, nick)
            print 'added new lambda function to commands as %s' % name
