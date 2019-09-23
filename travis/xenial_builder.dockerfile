FROM ubuntu:xenial

ENV LANG C.UTF-8

RUN apt update -q && \
  dpkg --add-architecture i386 && \
  apt install -q -y --no-install-recommends \
# Base build tools
    build-essential automake libtool cmake ccache pkg-config autopoint patch \
    python3-pip python3-setuptools python3-wheel git subversion wget unzip \
    ninja-build \
# Python (2) is needed to install android-ndk
    python \
# Packaged dependencies
    libbz2-dev libmagic-dev uuid-dev zlib1g-dev default-jdk \
    libmicrohttpd-dev \
# Cross compile i586
    libc6-dev-i386 lib32stdc++6 gcc-multilib g++-multilib \
# To create the appimage of kiwix-desktop
    libfuse2 fuse patchelf \
# Other tools (to remove)
#    vim less grep \
  && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* /usr/share/doc/* /var/cache/debconf/*

# Create user
RUN useradd --create-home ci_builder
USER ci_builder
WORKDIR /home/ci_builder
ENV PATH="/home/ci_builder/.local/bin:${PATH}"

ENV TRAVIS_BUILD_DIR /home/ci_builder/kiwix-build
ENV GRADLE_USER_HOME /home/ci_builder
ENV TRAVIS_OS_NAME linux_xenial

CMD pip3 install --user ./kiwix-build && kiwix-build/travis/compile_all.py
