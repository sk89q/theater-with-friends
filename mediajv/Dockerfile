FROM python:3.8.2-slim-buster

WORKDIR /app

RUN apt-get update

RUN apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    ffmpeg

RUN apt-get update --fix-missing

RUN pip3 install --upgrade pip pipenv

RUN curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl
RUN chmod a+rx /usr/local/bin/youtube-dl

COPY Pipfile .
COPY deps deps
COPY bootstrap.sh .

RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --skip-lock

COPY . .
RUN chmod +x bootstrap.sh

RUN mkfifo /stream

CMD ["sh", "bootstrap.sh"]
