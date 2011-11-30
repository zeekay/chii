#!/usr/bin/env python
import argparse, datetime, new, os, sys, time, traceback, zlib
from fnmatch import fnmatch
from collections import defaultdict

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer, threads
from twisted.internet.task import LoopingCall
from twisted.python import log

import yaml

### config ###
CONFIG_FILE = 'bot.config'

class ChiiConfig(dict):
    """Handles all configuration for chii. Reads/writes from/to YAML.
       Acts like a normal dict, except returns default value or None
       for non-existant keys."""

    defaults = {
        'nickname': 'chii',
        'realname': 'chii',
        'ident_pass': None,
        'server': 'irc.foo.bar',
        'port': 6667,
        'channels': ['chiisadventure'],
        'cmd_prefix': '.',
        'modules': ['commands', 'events', 'tasks'],
        'user_roles': {'admins': ['you@yourhost']},
        'logs_dir': '',
        'log_channels': False,
        'log_privmsg': False,
        'log_chii': False,
        'log_stdout': True,
        'disabled_modules': [],
        'disabled_commands': [],
        'disabled_events': [],
        'disabled_tasks': [],
        'threaded': False,
    }

    def __init__(self, file):
        self.file = file
        if os.path.isfile(file):
            with open(file) as f:
                config = yaml.load(f.read())
                if config:
                    try:
                        for k in config:
                            self.__setitem__(k, config[k])
                    except:
                        pass

    def __getitem__(self, key):
        if self.__contains__(key):
            return super(ChiiConfig, self).__getitem__(key)
        elif key in self.defaults:
            return self.defaults[key]

    def save(self):
        f = open(self.file, 'w')
        f.write(yaml.dump(dict((key, self.__getitem__(key)) for key in sorted(self.keys())), default_flow_style=False))
        f.close()

    def save_defaults(self):
        f = open(self.file, 'w')
        f.write(yaml.dump(dict((key, self.defaults[key]) for key in sorted(self.defaults)), default_flow_style=False))
        f.close()

### decorators ###
def command(*args, **kwargs):
    """Decorator which adds callable to command registry"""
    if args and not hasattr(args[0], '__call__') or kwargs:
        # decorator used with args for aliases or keyward arg
        def decorator(func):
            def wrapper(*func_args, **func_kwargs):
                return func(*func_args, **func_kwargs)
            wrapper._registry = 'commands'
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            if args:
                wrapper._command_names = args
            else:
                # used with keyword arg but not alias names!
                wrapper._command_names = (func.__name__,)
            if 'restrict' in kwargs:
                wrapper._restrict = kwargs['restrict']
            else:
                wrapper._restrict = None
            return wrapper
        return decorator
    else:
        # used without any args
        func = args[0]
        def wrapper(*func_args, **func_kwargs):
            return func(*func_args, **func_kwargs)
        wrapper._registry = 'commands'
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._command_names = (func.__name__,)
        if 'restrict' in kwargs:
            wrapper._restrict = kwargs['restrict']
        else:
            wrapper._restrict = None
        return wrapper

def event(*event_types):
    """Decorator which adds callable to the event registry"""
    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            return func(*func_args, **func_kwargs)
        wrapper._registry = 'events'
        wrapper._event_types = event_types
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__hash__ = lambda *args: zlib.crc32(func.__name__)
        return wrapper
    return decorator

def task(repeat, scale=None):
    """Decorator which adds callable to task registry"""
    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            return func(*func_args, **func_kwargs)
        wrapper._registry = 'tasks'
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._task_repeat = repeat
        wrapper._task_scale = scale
        return wrapper
    return decorator


### utils ###

def user_split(user):
    try:
        nick, host = user.split('!')
    except ValueError:
        nick, host = '', user
    return nick, host

### application logic ###
class ChiiLogger:
    """Logs both irc events and chii events into different log files"""
    def __init__(self, config):
        self.logs_dir = config['logs_dir']
        self.channel_logs = {}
        self.chii_log = None
        self.log_privmsg = False

        if self.logs_dir:
            if not os.path.isdir(self.logs_dir):
                os.mkdir(self.logs_dir)
            if config['log_channels']:
                self.channel_logs = dict(((channel, open(os.path.join(self.logs_dir, channel +'.log'), 'a')) for channel in config['channels']))
            if config['log_chii']:
                self.chii_log = open(os.path.join(self.logs_dir, config['nickname'] + '.log'), 'a')
                self.observer = log.FileLogObserver(self.chii_log)
                self.observer.start()
            if config['log_privmsg']:
                self.log_privmsg = True
        else:
            self.log = self.close = lambda *args: None

    def log(self, message, channel=None):
        """Write a message to the file."""
        if channel:
            if channel.startswith('#'):
                channel = channel[1:]
            if channel in self.channel_logs:
                file = self.channel_logs[channel]
                timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
                file.write('%s %s\n' % (timestamp, message))
                file.flush()
            elif self.log_privmsg:
                file = open(os.path.join(self.logs_dir, channel + '.log'), 'a')
                timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
                file.write('%s %s\n' % (timestamp, message))
                file.close()

    def close(self):
        if self.chii_log:
            self.observer.stop()
            self.chii_log.close()
        for channel in self.channel_logs.values():
            channel.close()

class ChiiBot:
    """what makes chii, chii"""
    def _add_command(self, method):
        """add new instance method to self.commands"""
        if method.__name__ not in self.config['disabled_commands']:
            for name in method._command_names:
                if name in self.commands:
                    print 'Warning! commands registry already contains %s' % name
                self.commands[name] = new.instancemethod(method, self, ChiiBot)

    def _add_event(self, method):
        """add new instance method to self.events"""
        if method.__name__ not in self.config['disabled_events']:
            for event in method._event_types:
                self.events[event].add(new.instancemethod(method, self, ChiiBot))

    def _add_task(self, method):
        """add new instance method to self.tasks"""
        if method.__name__ not in self.config['disabled_tasks']:
            self.tasks[method.__name__] = (new.instancemethod(method, self, ChiiBot), method._task_repeat, method._task_scale)

    def _add_to_registry(self, mod):
        """Adds registred methods to registry"""
        dispatch = {'commands': self._add_command, 'events': self._add_event, 'tasks': self._add_task}

        registered = filter(lambda x: hasattr(x, '_registry'), (getattr(mod, x) for x in dir(mod) if not x.startswith('_')))
        for method in registered:
            dispatch.get(method._registry)(method)

    def _import_module(self, package, module):
        """imports, reloading if neccessary given package.module"""
        if package:
            path = '%s.%s' % (package, module)
        else:
            path = module
        # cleanup if we're reloading
        if path in sys.modules:
            print 'Reloading', path
            mod = sys.modules[path]
            for attr in filter(lambda x: x != '__name__', dir(mod)):
                delattr(mod, attr)
            reload(mod)
        else:
            print 'Importing', path

        # try to import module
        try:
            mod = __import__(path, globals(), locals(), [module], -1)
            return mod
        except Exception as e:
            print 'Error importing %s: %s' % (path, e)
            traceback.print_exc()

    def _update_registry(self):
        """Updates command, event task registries"""
        paths = self.config['modules']
        if paths:
            self.commands = {}
            self.events = defaultdict(set)
            self.tasks = {}
            self.running_tasks = {}
            for path in paths:
                if os.path.isdir(path):
                    package = os.path.basename(path)
                    modules = [f.replace('.py', '') for f in os.listdir(path) if f.endswith('.py') and f != '__init__.py']
                else:
                    package = None
                    modules = [path]
                for module in modules:
                    if module not in config['disabled_modules']:
                        mod = self._import_module(package, module)
                        if mod:
                            self._add_to_registry(mod)
            print '[commands]', ', '.join(sorted(x for x in self.commands))
            print '[events]', ' '.join(sorted(x + ': ' + ', '.join(sorted(y.__name__ for y in self.events[x])) for x in self.events))
            print '[tasks]', ', '.join(sorted(x for x in self.tasks))

    # command, event task methods that execute specify commands for given behavior
    def _command(self, command, channel, nick, host, msg):
        """excecutes a command"""
        if len(msg) > 1:
            args = msg[1:]
        else:
            args = ()
        try:
            response = command(channel, nick, host, *args)
        except Exception as e:
            response = 'Error! Error! Error! Abandon ship! %s' % e
            traceback.print_exc()
        if response:
            self.msg(channel, response)
            self.logger.log("<%s> %s" % (self.nickname, response), channel)

    def _event(self, event, args=(), respond_to=False):
        """executes an event"""
        try:
            response = event(*args)
        except Exception as e:
            response = 'Event failed! %s' % e
            traceback.print_exc()
        if response and respond_to:
            # only return something if this event is caught in a channel
            self.msg(respond_to, response)
            self.logger.log("<%s> %s" % (self.nickname, response), respond_to)

    def _task(self, name, func, repeat=60, scale=None):
        """executes looping task"""
        def loop_task(func, repeat):
            lc = LoopingCall(func)
            lc.start(repeat)
            self.running_tasks[func.__name__] = lc
            print 'starting task %s. repeating every %s' % (name, self._fmt_seconds(repeat))

        time_scale = {
            'min': 60,
            'hou': 3600,
            'day': 86400,
            'wee': 604800,
        }

        if type(repeat) is not int:
            repeat = 1
            scale = repeat

        if scale is None:
            loop_task(func, repeat)
        elif scale[:3] in time_scale:
            repeat = repeat * time_scale[scale[:3]]
            loop_task(func, repeat)

    # command, event, task handlers
    def _handle_command(self, channel, nick, host, msg):
        """handles command dispatch"""
        msg = msg.split()
        command = self.commands.get(msg[0][1:].lower(), None)
        if command:
            if self._check_permission(command._restrict, nick, host):
                if self.config['threaded']:
                    threads.deferToThread(self._command, command, channel, nick, host, msg)
                else:
                    defer.execute(self._command, command, channel, nick, host, msg)

    def _handle_event(self, event_type, args=(), respond_to=False):
        """handles event dispatch"""
        for event in self.events[event_type]:
            if self.config['threaded']:
                threads.deferToThread(self._event, event, args, respond_to)
            else:
                defer.execute(self._event, event, args, respond_to)

    def _start_tasks(self):
        """starts all tasks"""
        if self.tasks:
            for task in self.tasks:
                func, repeat, scale = self.tasks[task]
                if self.config['threaded']:
                    threads.deferToThread(self._task, task, func, repeat, scale)
                else:
                    defer.execute(self._task, task, func, repeat, scale)

    def _stop_tasks(self):
        """stops all tasks"""
        if self.tasks:
            for task in self.tasks:
                try:
                    self.running_tasks[task].stop()
                except:
                    pass

    # a couple of ways to do deferred messaging
    def batch_msg(self, channel, msg):
        """tries to prevent flooding by sending messages staggered 1 second per line"""
        for delay, line in enumerate(msg.split('\n')):
            self.msg_later(channel, line, delay)

    def msg_later(self, channel, msg, delay):
        """uses reactor.callLater to send a message after a given delay"""
        d = defer.Deferred()
        reactor.callLater(delay, d.callback, None)
        d.addCallback(lambda x: self.msg(channel, msg))

    def msg_deferred(self, channel, func, *args):
        """returns deferred result of func as message to given channel"""
        d = defer.Deferred()
        d.addCallback(lambda result: self.msg(channel, str(result)))
        d.callback(func(*args))

    def msg_defer_to_thread(self, channel, func, *args):
        """returns deferred result of func as message to given channel (using deferToThread)"""
        d = threads.deferToThread(func, *args)
        d.addCallback(lambda result: self.msg(channel, str(result)))

    # some extra deferred wrappers
    def _call_later(self, delay, func, *args):
        """uses reactor.callLater to call function at a later point, returns deferred object"""
        d = defer.Deferred()
        reactor.callLater(delay, d.callback, None)
        d.addCallback(lambda x: func(*args))
        return d

    def _deferred(self):
        """returns a deferred object"""
        d = defer.Deferred()
        return d

    def _deferred_func(self, cb, func, *args):
        """defers a func, sets callback, returns deferred object"""
        d = defer.Deferred()
        d.addCallback(cb)
        d.callback(func(*args))
        return d

    def _deferred_to_thread(self, cb, func, *args):
        """defers func to another thread, returns deferred object"""
        d = threads.deferToThread(func, *args)
        d.addCallback(lambda result: cb(result))
        return d

    # misc functions
    def _check_permission(self, role, nick, host):
        """checks whether nick, host, or nick!host has required role"""
        if role is None:
            return True
        user = '!'.join((nick, host))
        for rule in self.config['user_roles'][role]:
            if fnmatch(user, rule):
                return True
        return False

    def _fmt_seconds(self, s):
        """returns formatted time"""
        d, remainder = divmod(s, 86400)
        h, remainder = divmod(remainder, 3600)
        m, s = divmod(remainder, 60)
        time = {d: 'days', h: 'hours', m: 'minutes', s: 'seconds'}
        return ' '.join(' '.join((str(x), time[x])) for x in (d, h, m, s) if x is not 0)

    def _rehash(self):
        self._handle_event('unload')
        self._stop_tasks()
        self._update_registry()
        self._handle_event('load')
        self._start_tasks()

    def _quit(self, message=None):
        self._handle_event('quit')
        self._stop_tasks()
        self.factory.doStop()
        self.quit(message)
        reactor.callLater(1, self.logger.close, None)
        reactor.callLater(1, reactor.stop, None)
        reactor.stop()


### twisted protocol/factory ###
class ChiiProto(irc.IRCClient, ChiiBot):
    """a very peculiar bot"""
    _names_list = defaultdict(set)

    def connectionMade(self):
        self.logger.log("[connected at %s]" % time.asctime(time.localtime(time.time())))
        irc.IRCClient.connectionMade(self)

        # update list of commands, events, tasks, and start tasks
        self._update_registry()
        self._handle_event('load')
        self._start_tasks()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % time.asctime(time.localtime(time.time())))
        self.logger.close()

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.setNick(self.nickname)
        if self.config['ident_pass']:
            self.msg('nickserv', 'identify %s' % self.config['ident_pass'])
        for channel in self.config['channels']:
            self.join(channel)

    def kick(self, user, channel, msg):
        self.sendLine('KICK %s %s %s')

    def whois(self, user, channel=None):
        """Retrieve information about the specified user."""
        if not hasattr(self, '_saved_whois'):
            self._saved_whois = {}
        self._current_whois = (channel, user)
        self._saved_whois[user] = {
            'user': None,
            'server': None,
            'operator': False,
            'idle': 0,
            'channels': [],
            'added': datetime.datetime.now()
        }
        self.sendLine('WHOIS ' + user)

    def joined(self, channel):
        """This will get called when the bot joins a channel."""
        self.logger.log("[I have joined %s]" % channel, channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        nick, host = user_split(user)

        # handle message events
        if channel == self.nickname:
            channel = nick # there is no channel, so set channel to nick so response goes some place (if there is one)
            self._handle_event('privmsg', args=(channel, nick, host, msg), respond_to=channel)
        else:
            self._handle_event('pubmsg', args=(channel, nick, host, msg), respond_to=channel)
        self._handle_event('msg', args=(channel, nick, host, msg), respond_to=channel)

        # Check if we're getting a command
        if msg.startswith(self.config['cmd_prefix']):
            self._handle_command(channel, nick, host, msg)

        # logs
        self.logger.log("<%s> %s" % (nick, msg), channel)

    # event callbacks
    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        nick, host = user_split(user)
        if channel == self.nickname:
            channel = nick
        self.logger.log("* %s %s" % (nick, msg), channel)
        self._handle_event('action', args=(channel, nick, host, msg), respond_to=channel)

    def userJoined(self, user, channel):
        """Called when I see another user joining a channel."""
        self._handle_event('user_joined', args=(channel, user), respond_to=channel)

    def userLeft(self, user, channel):
        """Called when I see another user leaving a channel."""
        nick, host = user_split(user)
        self._handle_event('user_left', args=(channel, user), respond_to=channel)

    def userQuit(self, user, quitMessage):
        """Called when I see another user disconnect from the network."""
        self._handle_event('user_quit', args=(user, quitMessage))

    def userKicked(self, kickee, channel, kicker, message):
        """Called when I observe someone else being kicked from a channel."""
        self._handle_event('user_kicked', args=(channel, kickee, kicker, message))

    def _ping(self, user, message=None, channel=None):
        if channel:
            self._ping_called_from = channel
        self.ping(user, message)

    def pong(self, user, secs):
        if hasattr(self, '_ping_called_from'):
            channel = self._ping_called_from
            if channel:
                self.msg(channel, 'ping! reply from %s: %f seconds' % (user, secs))
            del self._ping_called_from

    # irc callbacks
    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))
        self._handle_event('user_nick_changed', args=(old_nick, new_nick))

    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '`'

    def irc_ERR_NICKNAMEINUSE(self, prefix, params):
        """
        Called when we try to register or change to a nickname that is already
        taken.
        """
        if self.config['identpass']:
            self.msg('nickserv', 'ghost %s %s' % (self.nickname, self.config['identpass']))
            self.setNick(self.nickname)
        else:
            self.setNick(self.alterCollidedNick(self._attemptedNick))

    def irc_RPL_WHOISUSER(self, prefix, params):
        channel, user = self._current_whois
        self._saved_whois[user]['user'] = (params[2], params[3], params[5])

    def irc_RPL_WHOISSERVER(self, prefix, params):
        channel, user = self._current_whois
        self._saved_whois[user]['server'] = (params[2], params[3])

    def irc_RPL_WHOISOPERATOR(self, prefix, params):
        channel, user = self._current_whois
        self._saved_whois[user]['operator'] = True

    def irc_RPL_WHOISIDLE(self, prefix, params):
        channel, user = self._current_whois
        self._saved_whois[user]['idle'] = int(params[2])

    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        channel, user = self._current_whois
        self._saved_whois[user]['channels'].extend(params[2].split())

    def irc_RPL_ENDOFWHOIS(self, prefix, params):
        channel, user = self._current_whois
        if channel:
            a, c, i, o, s, u = [self._saved_whois[user][x] for x in sorted(self._saved_whois[user])]
            self.msg(channel, '\002user\002: %s!%s@%s' % u)
            self.msg(channel, '\002server\002: %s - %s' % s)
            self.msg(channel, '\002operator\002: %s' % o)
            self.msg(channel, '\002idle\002: %s' % self._fmt_seconds(i))
            self.msg(channel, '\002channels\002: %s' % ' '.join(x for x in c))
        del self._current_whois

    def irc_ERR_NOSUCHNICK(self, prefix, params):
        if hasattr(self, '_current_whois'):
            channel, user = self._current_whois
            if channel:
                self.msg(channel, 'no such user \002%s' % user)
            del self._current_whois
        else:
            pass

    def _names(self, channel, action=None):
        self._names_cb = (channel, action)
        self.sendLine('NAMES %s' % channel)

    def irc_RPL_NAMREPLY(self, prefix, params):
        # get list of users minus prefix & minus you!
        def strip_prefix(user):
            for prefix in ('+', '@'):
                if user.startswith(prefix):
                    user = user[1:]
            return user

        channel, users = params[2], params[3]
        self._names_list[channel] = set()
        for user in users.split():
            user = strip_prefix(user)
            if user != self.nickname:
                self._names_list[channel].add(user)

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        def msg(*args):
            self.msg(args[0], 'users in %s: %s' % (channel, ' '.join(self._names_list[channel])))

        def mode(*args):
            prefix, mode = args[0]
            mode = mode * len(self._names_list[channel])
            self.sendLine('MODE %s %s%s %s' % (channel, prefix, mode, ' '.join(self._names_list[channel])))

        error = lambda *args: None

        if hasattr(self, '_names_cb'):
            channel, action = self._names_cb
            if params[1] == channel and action:
                {'msg': msg, 'mode': mode}.get(action[0], error)(action[1])
                del self._names_cb

    def sendLine(self, line):
        """Coerce unicode objects to str objects encoded as  utf-8"""
        if isinstance(line, unicode):
            return irc.IRCClient.sendLine(self, line.encode('utf-8', 'ignore'))
        return irc.IRCClient.sendLine(self, line)

class ChiiFactory(protocol.ClientFactory):
    """A factory for ChiiBots."""
    def __init__(self, chii):
        self.protocol = chii

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.callLater(10, connector.connect)
        #reactor.stop()

# we do this so we can easily import the config into our modules from here
config = ChiiConfig(CONFIG_FILE)

### main ###
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple python bot')
    parser.add_argument('-c', '--config', metavar='config file', help='specify a non-default configuration file to use')
    parser.add_argument('--save-defaults', metavar='config file', nargs='?', const=True, help='specify a non-default configuration file to use', )
    args = parser.parse_args()

    if args.config:
        config = ChiiConfig(args.config)

    if args.save_defaults:
        config.save_defaults()
        sys.exit(0)

    # no config? DIE
    if not config:
        print 'No config file found! Create %s manually, or use --save-defaults to generate a new config file.', CONFIG_FILE
        sys.exit(1)

    # initialize logging
    if config['log_stdout']:
        log.startLogging(sys.stdout)

    # setup our protocol & factory
    ChiiProto.config = config
    ChiiProto.nickname = config['nickname']
    ChiiProto.realname = config['realname']

    # setup logging
    ChiiProto.logger = ChiiLogger(config)

    # yaya make our chii
    factory = ChiiFactory(ChiiProto)

    # connect factory to this host and port
    if config['ssl']:
        from twisted.internet import ssl
        contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(config['server'], config['port'], factory, contextFactory)
    else:
        reactor.connectTCP(config['server'], config['port'], factory)

    # run bot
    if config['threaded']:
        thread_size = config['threads'] or 4
        reactor.suggestThreadPoolSize(thread_size)
    reactor.run()
