FROM ubuntu:xenial

ENV LANG C.UTF-8

RUN apt update -q
RUN \
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
# Cross win32 compiler
    g++-mingw-w64-i686 gcc-mingw-w64-i686 gcc-mingw-w64-base mingw-w64-tools \
# Cross compile i586
    libc6-dev-i386 lib32stdc++6 gcc-multilib g++-multilib \
# Other tools (to remove)
    vim less grep && \
  apt-get clean -y && \
  rm -rf /usr/share/doc/* /var/cache/debconf/*

# Create user
RUN useradd --create-home builder
USER builder
WORKDIR /home/builder
ENV PATH="/home/builder/.local/bin:${PATH}"

# Install kiwix-build
COPY --chown=builder:builder . kiwix-build
RUN pip3 install --user -e ./kiwix-build

ENV TRAVIS_BUILD_DIR /home/builder/kiwix-build
ENV GRADLE_USER_HOME /home/builder
ENV TRAVIS_OS_NAME   linux_xenial

CMD kiwix-build/travis/compile_all.py
