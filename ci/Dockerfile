FROM ubuntu:16.04
MAINTAINER Nils Schmidt <miniworldproject@gmail.com>

RUN apt-get update

# python3
RUN apt-get -y install python3 python3-pip
# apt dependencies
RUN apt-get -y install git ebtables iproute2 qemu-kvm bridge-utils bison flex libdb-dev psmisc curl

# git-lfs: https://github.com/git-lfs/git-lfs/wiki/Installation
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt-get install -y git-lfs
RUN git lfs install

# miniworld
ARG BRANCH=nightly
RUN mkdir /app
RUN git clone -b $BRANCH https://github.com/miniworld-project/miniworld_core.git app
RUN (cd /app && pip3 install -r requirements.txt)
WORKDIR /app

# iproute2
# RUN apt-get -y install pkg-config

CMD ["bash", "/app/start_server.sh"]

EXPOSE 5000