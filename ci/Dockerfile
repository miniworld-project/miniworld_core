FROM ubuntu:16.04
MAINTAINER Nils Schmidt <miniworldproject@gmail.com>

RUN apt-get update && \
# python3
apt-get -y install python3 python3-pip && \
# apt dependencies
apt-get -y install git ebtables iproute2 qemu-kvm bridge-utils bison flex libdb-dev psmisc curl wget kmod libdb5.3-dev

# miniworld
ARG BRANCH=nightly
RUN mkdir /app
RUN git clone -b $BRANCH https://github.com/miniworld-project/miniworld_core.git app
WORKDIR /app

# for development:
# COPY . /miniworld/
# RUN pip3 install /miniworld\[develop,server\]

RUN pip3 install --upgrade pip && \
    pip3 install /app/[server,develop]

RUN (cd examples && ./get_images.sh)
COPY install_iproute2.sh /app/

# iproute2
# RUN apt-get -y install pkg-config

CMD bash -c '(./install_iproute2.sh) ; modprobe ebtables ; mwserver'

VOLUME ['/app/scenarios', '/app/examples']
EXPOSE 5000
EXPOSE 5001