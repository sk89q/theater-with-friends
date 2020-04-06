#!/usr/bin/env python

import json
from argparse import ArgumentParser

from mediajv import Supervisor
from mediajv.api import APIServer
from mediajv.ffmpeg import *


def main():
    parser = ArgumentParser()
    parser.add_argument("config", metavar="PATH", help="configuration file")
    options = parser.parse_args()

    with open(options.config, "rb") as f:
        config = json.loads(f.read())

    logging.basicConfig(level=logging.DEBUG, format=config['logging']['format'])
    logging.getLogger("sh").setLevel(logging.WARNING)

    host = config['api']['host']
    port = config['api']['port']

    logging.info("Starting MediaJ, listening at %s:%d..." % (host, port))

    pipeline = FFmpegPipeline((848, 480))

    supervisor = Supervisor(pipeline)
    supervisor.media_path = config['media']['dir']
    supervisor.media_exts = config['media']['extensions']

    supervisor.register_source('web', WebVideoFactory())
    supervisor.register_source('graphics', GraphicsCardFactory())
    supervisor.register_source('file', LocalVideoFactory(supervisor))
    supervisor.register_source('harbor', HarborFactory(config['harbor']['base-app-path']))
    supervisor.register_filter('corner-overlay', CornerOverlayFactory())
    supervisor.register_filter('volume-boost', VolumeBoostFactory())
    supervisor.register_filter('skip-time', SkipTimeFactory())
    supervisor.register_filter('subtitles', SubtitlesFactory())

    server = APIServer((host, port), supervisor, config['api']['accounts'])

    supervisor.start()
    server.serve_forever()


if __name__ == "__main__":
    main()
