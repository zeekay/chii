from chii import command

import inspect

# utilities
@command(restrict='admins')
def args(self, channel, nick, host, *args):
    """prints arguments for a function/method"""
    argspec = inspect.getargspec(eval(args[0]))
    args = ['\002%s\002: %s' % (x, ' '.join(getattr(argspec, x)))
                for x in ('args', 'varargs', 'keywords', 'defaults')
                        if getattr(argspec, x) is not None]
    for arg in args:
        self.msg(channel, arg)

@command('exec', restrict='admins')
def evil_exec(self, channel, nick, host, *args):
    """u don't know me"""
    if args:
        from twisted.python import log
        from StringIO import StringIO

        # add twisted log observer
        output = StringIO()
        observer = log.FileLogObserver(output)
        observer.start()
        # grab initial "log started" message, we don't care about that
        output.getvalue()

        # exec args
        exec compile(' '.join(args), '', 'single')

        # stop observer and return output
        observer.stop()
        logged = output.getvalue().partition('] ')[2]
        output.close()
        return logged

@command('eval', restrict='admins')
def evil_eval(self, channel, nick, host, *args):
    """u don't know me"""
    if args:
        return str(eval(' '.join(args)))
