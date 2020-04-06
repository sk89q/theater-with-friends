import threading
import logging
import time

__all__ = ('PipeRedirector', 'LoggerPipe', 'CountdownWriter', 'put_file',
           'force_cast', 'build_factory')


class PipeRedirector(threading.Thread):
    def __init__(self, source, dest):
        super(PipeRedirector, self).__init__()
        self.source = source
        self.dest = dest

    def run(self):
        while True:
            try:
                data = self.source.read(1024)
            except IOError as e:
                break
            if not data:
                break
            self.dest.write(data)


class LoggerPipe(object):
    def __init__(self, name):
        self.log = logging.getLogger(name)

    def write(self, str):
        self.log.debug(str)


class CountdownWriter(threading.Thread):
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = path
        self.running = True

    def run(self):
        while self.running:
            put_file(self.path, str(time.time()))


def put_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def force_cast(obj, type):
    return obj if isinstance(obj, type) else type()

def build_factory(cls, *args):
    class ProxyFactory:
        def create(self, data):
            real_args = []
            for k in args:
                if k not in data:
                    break
                real_args.append(data[k])
            return cls(*real_args)
    ProxyFactory.__name__ = cls.__name__ + "Factory"
    return ProxyFactory