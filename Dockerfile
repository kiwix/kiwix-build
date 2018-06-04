FROM ubuntu:artful

ENV LANG C.UTF-8

RUN \
  dpkg --add-architecture i386; \
  apt update -q; \
  apt full-upgrade --purge -q -y; \
  apt install -q -y --no-install-recommends \
# Base build tools
    build-essential \
#    gcc-5 \
#    g++-5 \
    automake \
    libtool \
    cmake \
    ccache \
    pkg-config \
    autopoint \
    patch \
    python \
    python3 \
    python3-pip \
    python3-setuptools \
    git \
    subversion \
    wget \
    unzip \
    sudo \
# Win32 cross-compilation
    g++-mingw-w64-i686 \
    gcc-mingw-w64-i686 \
    gcc-mingw-w64-base \
    mingw-w64-tools \
# Some dependencies already packaged
    libbz2-dev \
    libmagic-dev \
    zlib1g-dev \
    uuid-dev \
    ctpp2-utils \
    libctpp2-dev \
    libmicrohttpd-dev \
# Qt packages
    libqt5gui5 \
    qtbase5-dev \
    qtwebengine5-dev \
    qt5-default \
# Some helper tools
    vim \
    less \
    grep \
    openssh-client \
    ; \
  apt-get clean -y; \
  rm -rf \
    /usr/share/doc/* \
    /var/cache/debconf/*

RUN useradd --create-home travis -G sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER travis

WORKDIR /home/travis

RUN \
  mkdir -p /home/travis/.local/bin ;\
  wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip ;\
  unzip ninja-linux.zip ninja ;\
  mv ninja /home/travis/.local/bin ;\
  rm ninja-linux.zip
ENV PATH="/home/travis/.local/bin:${PATH}"

COPY . kiwix-build/
RUN sudo chown -R travis:travis /home/travis/kiwix-build
RUN pip3 install --user -e kiwix-build

ENV TRAVISCI_SSH_KEY /home/travis/kiwix-build/travis/travisci_builder_id_key
ENV TRAVIS_OS_NAME linux

CMD kiwix-build/travis/compile_all.py && kiwix-build/travis/deploy.sh
