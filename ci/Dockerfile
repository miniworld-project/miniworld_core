FROM ubuntu:16.04
MAINTAINER Nils Schmidt <miniworldproject@gmail.com>

RUN apt-get update && \
    # python3
    apt-get -y install python3 python3-pip && \
    # apt dependencies
    apt-get -y --no-install-recommends install qemu-kvm qemu-utils git ebtables iproute2 bridge-utils bison flex libdb-dev psmisc curl wget socat && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*



# miniworld
ARG BRANCH=nightly
RUN mkdir /app
RUN git clone -b $BRANCH https://github.com/miniworld-project/miniworld_core.git app
WORKDIR /app
RUN (echo $PWD)
RUN pip3 install -r requirements.txt
RUN (cd examples && ./get_images.sh)

# iproute2
# RUN apt-get -y install pkg-config

CMD ["bash", "/app/start_server.sh"]

EXPOSE 5000

# TODO: decrease timeout and retries when there is an async rpc service :)
# TODO: use docker stack for deployment ?
# HEALTHCHECK --timeout=5 --retries=1 CMD "./mw.py ping"