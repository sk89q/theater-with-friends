import logging
import os
import os.path
from base64 import b64decode

from jsonrpcserver import method, serve

from .util import force_cast


class APIServer(object):
    def __init__(self, addr, supervisor, accounts=None):
        self.addr = addr

        if not accounts:
            accounts = {}

        self.supervisor = supervisor
        self.accounts = accounts

        @method
        def skip(id):
            return self.supervisor.skip(id)

        @method
        def enqueue(type, data, raw_filters, userdata):
            try:
                source = self.supervisor.build_source(type, force_cast(data, dict))

                # get filters
                filters = []
                for f in force_cast(raw_filters, list):
                    filter = self.supervisor.build_filter(f['type'], f['data'])
                    filters.append(filter)

                source.filters += filters
                source.userdata = userdata

                self.supervisor.enqueue(source)
            except Exception as e:
                logging.warning("Error queueing", exc_info=True)
                raise Exception(str(e))

        @method
        def dir(path):
            try:
                path = self.supervisor.resolve_media(path)
                parent_path = None

                entries = []
                for o in os.listdir(path):
                    o_path = os.path.join(path, o)
                    rel_path = os.path.relpath(o_path, self.supervisor.media_path)
                    is_dir = os.path.isdir(o_path)

                    # filter out non-video files
                    if not is_dir:
                        base_path, ext = os.path.splitext(o_path)
                        if ext.lower() not in self.supervisor.media_exts:
                            continue

                    entries.append({'path': rel_path, 'dir': is_dir})

                entries = sorted(entries, key=lambda d: (not d['dir'], d['path']))

                if not os.path.relpath(path, self.supervisor.media_path) == ".":
                    parent_path = os.path.relpath(os.path.join(path, ".."), self.supervisor.media_path)

                return {
                    "entries": entries,
                    "parent": parent_path,
                }
            except Exception as e:
                logging.warning("Error listing", exc_info=True)
                raise Exception(str(e))

        @method
        def queue():
            with self.supervisor.lock:
                queue = self.supervisor.list_queue()
                history = self.supervisor.list_history()
                current = self.supervisor.get_current()

            return {
                "queue": [self.process_item(item) for item in queue],
                "history": [self.process_item(item) for item in history],
                "current": self.process_item(current),
            }

    def process_item(self, item):
        if item:
            return {
                "type": item.__class__.__name__,
                "qid": item.qid,
                "name": str(item),
                "aborted": item.aborted,
                "error": str(item.error) if item.error else None,
                "queued": item.queue_time,
                "started": item.start_time,
                "filters": [str(filter) for filter in item.filters],
                "userdata": item.userdata,
            }

    def authenticate(self, headers):
        authorization = headers.get('Authorization')

        if not authorization:
            return False

        (type, _, encoded) = authorization.partition(' ')

        if type != "Basic":
            return False

        try:
            (username, _, password) = b64decode(encoded).partition(':')
        except TypeError as e:
            return False

        if username not in self.accounts:
            return False
        if self.accounts[username] != password:
            return False

        return True

    def serve_forever(self):
        serve(*self.addr)
