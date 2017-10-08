FROM ubuntu:16.04
MAINTAINER Nils Schmidt <miniworldproject@gmail.com>

RUN apt-get update && \
    # python3
    apt-get -y install python3 python3-pip && \
    # apt dependencies
    apt-get -y install git ebtables iproute2 qemu-kvm bridge-utils bison flex libdb-dev psmisc curl wget kmod libdb5.3-dev socat && \
    # iproute2
    apt-get -y install libxtables11 iptables-dev pkg-config libmnl-dev && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# install iproute2
ADD scripts/install_iproute2.sh /tmp
RUN /tmp/install_iproute2.sh

# miniworld
ARG BRANCH=master
RUN mkdir /app
RUN git clone -b $BRANCH https://github.com/miniworld-project/miniworld_core.git app
WORKDIR /app

# for development:
#COPY . /miniworld/
#COPY scripts/install_iproute2.sh /scripts/app/
#RUN pip3 install /miniworld\[develop,server\]
#RUN (cd examples && ./get_images.sh)

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir /app\[server,develop\]

CMD bash -c 'modprobe ebtables ; mwserver'

VOLUME '/app/scenarios'
VOLUME '/app/examples'
EXPOSE 5000
EXPOSE 5001

# HEALTHCHECK --timeout=5s --retries=3 CMD "./mw.py ping"
