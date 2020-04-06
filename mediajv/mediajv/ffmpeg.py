import logging
import os
import os.path
import random
import re
import sys
import tempfile
from glob import glob
from io import StringIO
from signal import SIGINT
from subprocess import Popen, PIPE

import sh as pbs
import yaml
from sh import youtube_dl, which, ffmpeg

from mediajv import Filter, Media, Pipeline
from .util import LoggerPipe, PipeRedirector, build_factory

youtube_dl = youtube_dl.bake(**{"4": True})


class FFmpegPipeline(Pipeline):
    def __init__(self, video_dim):
        super(FFmpegPipeline, self).__init__()
        self.video_dim = video_dim

    def out_pipe(self):
        return sys.out


class Subtitles(Filter):
    log = logging.getLogger("mediajv.Subtitles")

    def __init__(self):
        super(Subtitles, self).__init__()

    def apply(self, media):
        if hasattr(media, 'path'):
            self.log.info("Detecting subtitles...")

            base_path, ext = os.path.splitext(media.path)
            srt_path = "%s.srt" % base_path
            ass_path = "%s.ass" % base_path

            # attach subs
            if os.path.exists(srt_path):
                media.log.info("Using subtitles at %s" % srt_path)
                media.add_vf("subtitles", srt_path)

            # auto-convert .srt to .ass
            if not os.path.exists(ass_path) and os.path.exists(srt_path):
                self.log.info("Converting .srt to .ass: %s" % srt_path)
                try:
                    ffmpeg("-i", srt_path, ass_path)
                except:
                    self.log.warn("Error auto-converting .srt to .ass", exc_info=True)

            # attach subs
            if os.path.exists(ass_path):
                media.log.info("Using subtitles at %s" % ass_path)
                media.add_vf("subtitles", ass_path)
        else:
            self.log.warn("No subtitles to render because it is a local file!")

    def __str__(self):
        return "SubtitlesDetector()"


SubtitlesFactory = build_factory(Subtitles)


class SkipTime(Filter):
    def __init__(self, skip_time):
        super(SkipTime, self).__init__()
        self.skip_time = skip_time

    def apply(self, media):
        media.skip_time = self.skip_time

    def __str__(self):
        return "skip ahead %s" % (self.skip_time)


SkipTimeFactory = build_factory(SkipTime, 'time')


class CornerOverlay(Filter):
    def __init__(self, text1, text2):
        super(CornerOverlay, self).__init__()
        self.text1 = text1
        self.text2 = text2

    def apply(self, media):
        media.add_vf("drawtext",
                     fontfile="fonts/ROCK.TTF",
                     textfile=media.write_temp_file(self.text1.encode("utf-8")),
                     x="w*0.05",
                     y="h*0.03",
                     fontsize=25,
                     fontcolor="white",
                     fix_bounds="1",
                     box="1",
                     boxcolor="black"
                     )

        media.add_vf("drawtext",
                     fontfile="fonts/DINE1.TTF",
                     textfile=media.write_temp_file(self.text2.encode("utf-8")),
                     x="w*0.05",
                     y="h*0.07",
                     fontsize=46,
                     fontcolor="white",
                     fix_bounds=1,
                     box=1,
                     boxcolor="0x97232f"
                     )

    def __str__(self):
        return "CornerOverlay (%s, %s)" % (self.text1, self.text2)


CornerOverlayFactory = build_factory(CornerOverlay, 'text1', 'text2')


class VolumeBoost(Filter):
    def __init__(self, gain, volume):
        super(VolumeBoost, self).__init__()
        self.gain = gain
        self.volume = volume

    def apply(self, media):
        media.audio_filters.append(
            "compand=.3 .3:1 1:-90/-60 -60/-40 -40/-30 -20/-20:6:%d:%d:0.2" % (self.gain, self.volume))

    def __str__(self):
        return "VolumeBoost (%d, %d)" % (self.gain, self.volume)


VolumeBoostFactory = build_factory(VolumeBoost, 'gain', 'volume')


class RenderSubtitles(Filter):
    def __init__(self, path):
        super(RenderSubtitles, self).__init__()
        self.path = path

    def apply(self, media):
        media.add_vf("subtitles", self.path)

    def __str__(self):
        return "RenderSubtitles (%s)" % (os.path.basename(self.path))


WebVideoFactory = build_factory(RenderSubtitles, 'path')


class FFmpegMedia(Media):
    log = logging.getLogger("mediajv.FFmpegMedia")
    input = "__missing__"
    extra_inputs = []
    filter_chars = re.compile("([':\\\\,])")
    realtime = True

    def __init__(self):
        super(FFmpegMedia, self).__init__()
        self.video_filters = []
        self.audio_filters = []
        self.temp_files = []
        self.skip_time = None

        self.add_vf("fps",
                    fps=25
                    )

    def write_temp_file(self, content):
        file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_files.append(file)
        file.write(content)
        file.close()
        return file.name

    def escape_filter(self, val):
        return self.filter_chars.sub("\\\\\\1", str(val) \
                                     .replace("\\", "\\\\") \
                                     .replace("\n", "\\n") \
                                     .replace("\r", "\\r") \
                                     .replace("\t", "\\t") \
                                     .replace("\0", ""))

    def _add_filter(self, arr, type, args, val=None, _index=None):
        s = StringIO()
        s.write(type)
        s.write("=")

        if val:
            s.write(self.escape_filter(val))
        else:
            first = True
            for k, v in args.items():
                if not first:
                    s.write(": ")
                first = False

                s.write(k)
                s.write("=")
                s.write(self.escape_filter(v))

        if _index:
            arr.insert(_index, s.getvalue())
        else:
            arr.append(s.getvalue())
        s.close()

    def add_vf(self, filter_type, val=None, _index=None, **kwargs):
        self._add_filter(self.video_filters, filter_type, kwargs, val, _index)

    def add_af(self, filter_type, val=None, _index=None, **kwargs):
        self._add_filter(self.audio_filters, filter_type, kwargs, val, _index)

    def run(self, pipeline):
        # scale video
        self.add_vf("scale", "%dx%d" % pipeline.video_dim)

        self.setup()

        for filter in self.filters:
            filter.apply(self)

        # get the input
        if not hasattr(self.input, 'fileno'):
            input_pipe = PIPE
            input_arg = self.input
        else:  # assume that it's a pipe
            input_pipe = self.input
            input_arg = "-"

        input_args = []
        if self.skip_time:
            input_args.append("-ss")
            input_args.append(self.skip_time)
        for input in self.extra_inputs:
            input_args.append("-i")
            input_args.append(input)
        input_args += ['-i', input_arg]

        cmd = [
                  which("ffmpeg"),
              ] + (["-re"] if self.realtime else []) + input_args + [
                  "-vf", ", ".join(self.video_filters),
              ] + (["-af", ", ".join(self.audio_filters)] if len(self.audio_filters) else []) + [
                  "-shortest",
                  "-target", "film-dvd", "-q:v", "0", "-q:a", "0",
                  "-f", "mpeg",
                  "-loglevel", "error",
                  "-"
              ]

        self.log.debug(" ".join(cmd))

        self.proc = Popen(cmd, stdin=input_pipe, stdout=PIPE, stderr=PIPE)

        try:
            PipeRedirector(self.proc.stderr, LoggerPipe("mediajv.FFmpegSource.ffmpeg")).start()
            PipeRedirector(self.proc.stdout, sys.stdout.buffer).start()

            # wait until it dies
            self.proc.wait()
        finally:
            self.proc = None

            for file in self.temp_files:
                try:
                    os.remove(file.name)
                except:
                    pass

    def abort(self):
        proc = self.proc
        try:
            if proc:
                proc.send_signal(SIGINT)
                proc.kill()
        except Exception as e:
            self.log.warning("Failed to send SIGINT to ffmpeg", exc_info=True)


class GraphicsCard(FFmpegMedia):
    media_dir = "source/graphics"
    valid = re.compile("[^A-Za-z0-9_\\-]")

    def __init__(self, style, texts, audio_filename=None):
        super(GraphicsCard, self).__init__()
        self.texts = texts

        # read style
        self.style_name = os.path.basename(self.valid.sub("", style))
        style_file = os.path.join(self.media_dir, self.style_name + ".yml")
        if os.path.exists(style_file):
            with open(style_file, "r") as f:
                self.style = yaml.load(f.read())
            self.background_path = os.path.join(self.media_dir, self.style['video'])
        else:
            raise ValueError("Unknown style: %s" % style)

        # read alternate audio
        if audio_filename:
            self.audio_path = os.path.join(self.media_dir, os.path.basename(audio_filename))
            if not os.path.isfile(self.audio_path):
                raise ValueError("Unknown audio file: %s" % audio_filename)
        else:
            self.audio_path = None

    def setup(self):
        self.input = self.background_path
        if self.audio_path:
            self.extra_inputs = [self.audio_path]
        else:
            # audio from the style file
            if 'audio' in self.style:
                audio = self.style['audio']
                if audio['type'] == "random":
                    pattern = audio['pattern']
                    files = glob(os.path.join(self.media_dir, pattern))
                    if len(files) > 0:
                        file = random.choice(files)
                        self.log.info("Graphics card music: %s" % file)
                        self.extra_inputs = [file]

        # audio filters
        if 'audio-filters' in self.style:
            filters = self.style['audio-filters']
            for filter in filters:
                self.log.info("Added audio filter: %s" % filter['type'])
                self.add_af(filter['type'], **filter['properties'])

        # video filters
        if 'video-filters' in self.style:
            filters = self.style['video-filters']
            for filter in filters:
                self.log.info("Added video filter: %s" % filter['type'])
                self.add_vf(filter['type'], **filter['properties'])

        # draw text boxes
        for textbox in self.style['textboxes']:
            var = textbox['var']
            if var not in self.texts:
                continue
            text = self.texts[var]

            # line spacing
            if 'line-spacing' in textbox:
                line_spacing = textbox['line-spacing']
            else:
                line_spacing = 10

            for index, line in enumerate(text.split("\n")[:7]):
                prop = textbox['properties'].copy()

                # line %d value in y
                if 'y' in prop:
                    prop['y'] = str(prop['y']).replace("%d", str(index * line_spacing))

                self.add_vf("drawtext",
                            textfile=self.write_temp_file(line.encode("utf-8")),
                            **prop
                            )

    def __str__(self):
        return "Graphics Card (%s)" % self.style_name


GraphicsCardFactory = build_factory(GraphicsCard, 'style', 'texts', 'audio')


class WebVideo(FFmpegMedia):
    """Play a video from the web.
    
    """
    log = logging.getLogger("mediajv.WebVideo")
    url = re.compile("^https?://", re.I)
    youtube_url = re.compile("^https?://(?:[A-Za-z0-9\\-\\.]+\\.)?youtu(?:be(?:\\-embed)?\\.com|\\.be)(?:/.*)?$", re.I)
    youtube_formats = [37, 22, 45, 44, 35, 34, 18, 22, 6, 5]

    def __init__(self, url):
        super(WebVideo, self).__init__()

        self.url = url

        # try to resolve the URL to see if we can play it
        # this may throw an error!
        self.format = None  # self.resolve_format(self.url)
        self.get_local = self.check_exists(self.url)

    def check_exists(self, url):
        try:
            url = youtube_dl(url, g=True)
            if url.startswith("http"):
                return True
        except pbs.ErrorReturnCode_1:
            pass
        return False

    def resolve_format(self, url):
        self.log.info("Trying to resolve %s" % url)

        # if it's a YouTube video, we have to find the best quality video
        if self.youtube_url.match(url):
            for format in self.youtube_formats:
                self.log.debug("Trying %s with format %d" % (url, format))
                try:
                    url = youtube_dl(url, g=True, format=format)
                    if url.startswith("http"):
                        return format
                except pbs.ErrorReturnCode_1:
                    pass
            raise IOError("Failed to resolve format for %s" % url)

        # otherwise just check it if exists
        else:
            try:
                url = youtube_dl(url, g=True)
                if url.startswith("http"):
                    return None
            except pbs.ErrorReturnCode_1:
                pass
            raise IOError("Failed to resolve format for %s" % url)

    def setup(self):
        # pipe video from youtube-dl
        if self.get_local:
            self.log.info("Locally fetching %s..." % self.url)
            cmd = [which("youtube-dl"), "-4"]
        else:
            self.log.info("Remotely fetching %s..." % self.url)
            cmd = [which("ssh"), "-C", "theaterproxy@xxx", "youtube-dl"]
        if self.format:
            cmd += ["-f", str(self.format)]
        cmd += ["-o", "-", self.url]

        p1 = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        PipeRedirector(p1.stderr, LoggerPipe("mediajv.WebVideo.youtube-dl")).start()
        p1.stdin.close()

        self.input = p1.stdout

    def __str__(self):
        return self.url


WebVideoFactory = build_factory(WebVideo, 'url')


class DirectURL(FFmpegMedia):
    """Play a video from a URL.

    """
    log = logging.getLogger("mediajv.DirectURL")

    def __init__(self, url):
        super(DirectURL, self).__init__()

        self.url = url

    def setup(self):
        self.input = self.url

    def __str__(self):
        return self.url


class Harbor(DirectURL):
    """Play from a harbor.

    """
    log = logging.getLogger("mediajv.Harbor")

    def __init__(self, base_app_url, id):
        self.id = id
        super(Harbor, self).__init__(base_app_url + id)

    def __str__(self):
        return "Harbor(%s)" % self.id


class HarborFactory(object):
    realtime = False

    def __init__(self, base_app_url):
        self.base_app_url = base_app_url

    def create(self, data):
        return Harbor(self.base_app_url, data['id'])


class LocalVideo(FFmpegMedia):
    """
    Plays a local video file. Subtitles will automatically be attached if they are
    found. .srt subtitles will eb auto-converted to .ass.
    """
    log = logging.getLogger("mediajv.LocalVideo")

    def __init__(self, path, **kwargs):
        super(LocalVideo, self).__init__(**kwargs)

        self.path = os.path.realpath(path)

        # exist check
        if not os.path.exists(self.path):
            raise IOError("%s doesn't exist" % self.path)

    def setup(self):
        self.input = self.path

    def __str__(self):
        return os.path.basename(self.path)


class LocalVideoFactory(object):
    def __init__(self, supervisor):
        self.supervisor = supervisor

    def create(self, data):
        path = self.supervisor.resolve_media(data['path'])
        return LocalVideo(path)
