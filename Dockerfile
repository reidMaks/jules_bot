# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
ENV TOKEN=$TOKEN
WORKDIR /app

RUN apt-get -y update && apt-get install -y wget nano git build-essential yasm pkg-config libvorbis-dev libopus-dev

# Compile and install ffmpeg from source
RUN git clone https://github.com/FFmpeg/FFmpeg /root/ffmpeg && \
    cd /root/ffmpeg && \
    ./configure --enable-libvorbis --enable-libopus --extra-cflags=-I/usr/local/include && \
    make -j8 && make install -j8

# If you want to add some content to this image because the above takes a LONGGG time to build
ARG CACHEBREAK=1

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "./main.py"]