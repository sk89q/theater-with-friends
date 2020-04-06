#!/bin/sh
pipenv run mediajvd default_config.json > /stream &

ffmpeg -re -i /stream -r 30 -vcodec libx264 -b:v 700k -s 1280x720 -g 60 -x264opts "bitrate=800:vbv-maxrate=1000:vbv-bufsize=166" -acodec aac -ab 128k -ar 44100 -ac 2 -f flv "rtmp://nginx:1935/stream/theater live=1"



# ffmpeg -re -i stream -vcodec libx264 -b:v 700k -s 848x480 -x264opts "bitrate=700:vbv-maxrate=800:vbv-bufsize=166" -acodec libfaac -ab 128k -ar 44100 -ac 2 -f flv \
#   "rtmp://example.com:443/theater/live"

# ffmpeg -re -i stream -vcodec libx264 -b:v 1500k -s 1280x720 \
   # -x264opts "bitrate=1500:vbv-maxrate=1500:vbv-bufsize=166" \
   # -acodec libfaac -ab 128k -ar 44100 -ac 2 -f flv \
   # "rtmp://example.com:80/theater-internal/live"
# ffmpeg -re -i stream -vcodec libx264 -b:v 700k -s 1280x720 \
    # -x264opts "bitrate=700:vbv-maxrate=700:vbv-bufsize=166" \
    # -acodec libfaac -ab 128k -ar 44100 -ac 2 -f flv \
    # "rtmp://example.com:1935/hls/live"