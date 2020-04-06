import threading
import logging
import uuid
import time
import os, os.path

__all__ = ('Media', 'Supervisor')


class Pipeline(object):
    video_dim = (1280, 720)

    def __init__(self):
        pass


class Filter(object):
    def __init__(self):
        pass


class Media(object):
    def __init__(self):
        self.qid = str(uuid.uuid1())
        self.played = False
        self.aborted = False
        self.error = None
        self.filters = []
        self.userdata = {}
        self.queue_time = time.time()
        self.start_time = None

    def add_filter(self, filter):
        self.filters.append(filter)

    def run(self, pipeline):
        self.start_time = time.time()

    def _abort(self):
        self.aborted = True
        self.abort()


class Supervisor(threading.Thread):
    log = logging.getLogger("mediajv.Supervisor")
    history_max = 5
    media_path = "videos"
    media_exts = [".avi"]

    def __init__(self, pipeline):
        super(Supervisor, self).__init__()
        self.queue = []
        self.history = []
        self.current = None
        self.lock = threading.Condition()
        self.pipeline = pipeline
        self.sources = {}
        self.filters = {}

    def register_source(self, id, factory):
        self.sources[id] = factory

    def register_filter(self, id, factory):
        self.filters[id] = factory

    def build_source(self, type, data):
        if type in self.sources:
            return self.sources[type].create(data)
        raise KeyError("Unknown type: %s" % type)

    def build_filter(self, type, data):
        if type in self.filters:
            return self.filters[type].create(data)
        raise KeyError("Unknown type: %s" % type)

    def resolve_media(self, path):
        base_path = os.path.realpath(self.media_path) + os.sep
        path = os.path.realpath(os.path.join(base_path, path))

        # security check
        if not (path + os.sep).startswith(base_path):
            raise IOError("%s isn't an acceptable path" % path)

        return path

    def run(self):
        while True:
            with self.lock:
                while not len(self.queue):
                    self.lock.wait()
                item = self.queue.pop(0)
            try:
                self.log.info("Going live to %s" % item)
                item.played = True
                self.current = item
                item.run(self.pipeline)
            except Exception as e:
                item.error = e
                self.log.warning("Error occurred while streaming", exc_info=True)
            finally:
                with self.lock:
                    self.history.append(self.current)
                    while len(self.history) > self.history_max:
                        self.history.pop(0)
                self.current = None

    def enqueue(self, item):
        with self.lock:
            self.log.debug("Enqueued %s" % item)
            self.queue.append(item)
            self.lock.notify()

    def list_queue(self):
        with self.lock:
            return [item for item in self.queue]

    def list_history(self):
        with self.lock:
            return [item for item in self.history]

    def get_current(self):
        return self.current

    def skip(self, qid):
        with self.lock:
            if self.current and self.current.qid == qid:
                self.current._abort()
                return True

            new_queue = []
            found = False
            for item in self.queue:
                if item.qid == qid:
                    found = True
                else:
                    new_queue.append(item)
            if found:
                self.queue = new_queue
            return found